"""
MCP Server for AI Generation Platforms
Provides standardized interface to multiple AI video/image generation services
Based on InstaVibe's MCP server pattern
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
import asyncio
import os
import sys
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from utils.resilience import retry_with_backoff, CircuitBreaker, circuit_breaker
    from utils.logging_utils import setup_logging, set_correlation_id, get_correlation_id
except ImportError:
    # Fallback if utils not available
    def retry_with_backoff(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    circuit_breaker = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CineVibe AI Platforms MCP Server", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys (from environment variables)
RUNWAY_API_KEY = os.environ.get("RUNWAY_API_KEY", "")
PIKA_API_KEY = os.environ.get("PIKA_API_KEY", "")
MIDJOURNEY_API_KEY = os.environ.get("MIDJOURNEY_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # For Sora
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "")  # For Stable Diffusion
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")  # For Veo2 / Gemini

# Track active generation jobs
active_jobs: Dict[str, Dict] = {}

# Track costs per session
cost_tracker: Dict[str, float] = {}

# Platform API endpoints
API_ENDPOINTS = {
    "runway": "https://api.runwayml.com/v1",
    "pika": "https://api.pika.art/v1",
    "midjourney": "https://api.midjourney.com/v1",
    "sora": "https://api.openai.com/v1",
    "stable_diffusion": "https://api.stability.ai/v1",
    "veo2": "https://generativelanguage.googleapis.com/v1beta",
    "nano_banana": "https://generativelanguage.googleapis.com/v1beta"
}

# Cost per generation (in USD)
PLATFORM_COSTS = {
    "runway": {"per_second": 0.15, "min_charge": 0.75},
    "pika": {"per_second": 0.10, "min_charge": 0.50},
    "sora": {"per_second": 0.20, "min_charge": 1.00},
    "veo2": {"per_second": 0.18, "min_charge": 0.90},
    "midjourney": {"per_image": 0.05},
    "stable_diffusion": {"per_image": 0.02},
    "nano_banana": {"per_image": 0.039},
}


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GenerationJob:
    """Track generation job details"""
    job_id: str
    platform: str
    prompt: str
    content_type: str  # "video" or "image"
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error: Optional[str] = None
    cost: float = 0.0
    duration: Optional[int] = None
    parameters: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "platform": self.platform,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_url": self.result_url,
            "error": self.error,
            "cost": self.cost,
            "duration": self.duration,
        }


def calculate_cost(platform: str, duration: Optional[int] = None, count: int = 1) -> float:
    """Calculate generation cost for a platform"""
    costs = PLATFORM_COSTS.get(platform, {})

    if "per_second" in costs and duration:
        return max(costs.get("min_charge", 0), costs["per_second"] * duration)
    elif "per_image" in costs:
        return costs["per_image"] * count

    return 0.0


def track_cost(session_id: str, amount: float):
    """Track cost for a session"""
    if session_id not in cost_tracker:
        cost_tracker[session_id] = 0.0
    cost_tracker[session_id] += amount

async def generate_with_runway(
    prompt: str,
    duration: int = 5,
    parameters: Optional[Dict] = None
) -> Dict:
    """Generate video using Runway Gen-3 Alpha"""
    if not RUNWAY_API_KEY:
        return {"error": "Runway API key not configured"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_ENDPOINTS['runway']}/generate",
                headers={
                    "Authorization": f"Bearer {RUNWAY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "duration_seconds": duration,
                    "model": "gen3_alpha",
                    "parameters": parameters or {}
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("id", hashlib.md5(prompt.encode()).hexdigest())
                active_jobs[job_id] = {
                    "platform": "runway",
                    "status": "processing",
                    "created_at": datetime.utcnow().isoformat()
                }
                return result
            else:
                return {"error": f"Runway API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Runway generation error: {e}")
            return {"error": str(e)}

async def generate_with_pika(
    prompt: str,
    parameters: Optional[Dict] = None
) -> Dict:
    """Generate video using Pika 2.1"""
    if not PIKA_API_KEY:
        return {"error": "Pika API key not configured"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_ENDPOINTS['pika']}/generate",
                headers={
                    "Authorization": f"Bearer {PIKA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "aspect_ratio": parameters.get("aspect_ratio", "16:9") if parameters else "16:9",
                    "hd": True
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("job_id", hashlib.md5(prompt.encode()).hexdigest())
                active_jobs[job_id] = {
                    "platform": "pika",
                    "status": "processing",
                    "created_at": datetime.utcnow().isoformat()
                }
                return result
            else:
                return {"error": f"Pika API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Pika generation error: {e}")
            return {"error": str(e)}

async def generate_with_midjourney(
    prompt: str,
    parameters: Optional[Dict] = None
) -> Dict:
    """Generate image using Midjourney"""
    if not MIDJOURNEY_API_KEY:
        # Fallback to mock response for development
        return {
            "job_id": hashlib.md5(prompt.encode()).hexdigest(),
            "status": "queued",
            "message": "Midjourney API key not configured - mock response",
            "estimated_time": 60
        }
    
    # Midjourney API implementation would go here
    # This is a placeholder as Midjourney doesn't have official API yet
    return {
        "job_id": hashlib.md5(prompt.encode()).hexdigest(),
        "status": "processing",
        "platform": "midjourney"
    }

async def generate_with_stable_diffusion(
    prompt: str,
    negative_prompt: str = "",
    parameters: Optional[Dict] = None
) -> Dict:
    """Generate image using Stable Diffusion"""
    if not STABILITY_API_KEY:
        return {"error": "Stability API key not configured"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_ENDPOINTS['stable_diffusion']}/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {STABILITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [
                        {"text": prompt, "weight": 1},
                        {"text": negative_prompt, "weight": -1} if negative_prompt else None
                    ],
                    "cfg_scale": parameters.get("cfg_scale", 7) if parameters else 7,
                    "steps": parameters.get("steps", 30) if parameters else 30,
                    "samples": 1
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Stable Diffusion API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Stable Diffusion generation error: {e}")
            return {"error": str(e)}

async def generate_with_nano_banana(
    prompt: str,
    parameters: Optional[Dict] = None
) -> Dict:
    """Generate image using Google's Nano Banana (Gemini 2.5 Flash Image)"""
    if not GOOGLE_API_KEY:
        return {"error": "Google API key not configured"}

    async with httpx.AsyncClient() as client:
        try:
            # Gemini 2.5 Flash image generation endpoint
            response = await client.post(
                f"{API_ENDPOINTS['nano_banana']}/models/gemini-2.5-flash:generateContent",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": f"Generate a high quality cinematic image: {prompt}"}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseModalities": ["IMAGE"],
                        "imageSamplingParameters": {
                            "aspectRatio": parameters.get("aspect_ratio", "16:9") if parameters else "16:9"
                        }
                    }
                },
                timeout=60.0
            )

            if response.status_code == 200:
                result = response.json()
                job_id = hashlib.md5(prompt.encode()).hexdigest()

                # Calculate cost
                cost = calculate_cost("nano_banana")

                active_jobs[job_id] = GenerationJob(
                    job_id=job_id,
                    platform="nano_banana",
                    prompt=prompt,
                    content_type="image",
                    status=JobStatus.COMPLETED,
                    cost=cost,
                    result_url=result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("fileUri")
                ).to_dict()

                return {
                    "job_id": job_id,
                    "status": "completed",
                    "platform": "nano_banana",
                    "result": result,
                    "cost": cost
                }
            else:
                return {"error": f"Nano Banana API error: {response.status_code}", "details": response.text}

        except Exception as e:
            logger.error(f"Nano Banana generation error: {e}")
            return {"error": str(e)}


async def generate_with_sora(
    prompt: str,
    duration: int = 10,
    parameters: Optional[Dict] = None
) -> Dict:
    """
    Generate video using OpenAI Sora.

    Sora is OpenAI's video generation model capable of creating
    high-quality videos up to 60 seconds long.
    """
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}

    job_id = hashlib.md5(f"{prompt}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]

    async with httpx.AsyncClient() as client:
        try:
            # OpenAI Sora API endpoint (hypothetical - adjust when API is available)
            response = await client.post(
                f"{API_ENDPOINTS['sora']}/videos/generations",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sora-1.0",
                    "prompt": prompt,
                    "duration": min(duration, 60),  # Max 60 seconds
                    "quality": parameters.get("quality", "hd") if parameters else "hd",
                    "style": parameters.get("style", "cinematic") if parameters else "cinematic",
                    "size": parameters.get("size", "1920x1080") if parameters else "1920x1080",
                },
                timeout=120.0  # Sora may take longer
            )

            cost = calculate_cost("sora", duration)

            if response.status_code == 200:
                result = response.json()
                video_id = result.get("id", job_id)

                active_jobs[video_id] = GenerationJob(
                    job_id=video_id,
                    platform="sora",
                    prompt=prompt,
                    content_type="video",
                    status=JobStatus.PROCESSING,
                    duration=duration,
                    cost=cost,
                    parameters=parameters or {}
                ).to_dict()

                return {
                    "job_id": video_id,
                    "status": "processing",
                    "platform": "sora",
                    "estimated_time": duration * 3,  # Rough estimate: 3x real-time
                    "cost_estimate": cost
                }
            elif response.status_code == 429:
                return {"error": "Sora rate limit exceeded", "retry_after": response.headers.get("Retry-After", 60)}
            else:
                return {"error": f"Sora API error: {response.status_code}", "details": response.text}

        except httpx.TimeoutException:
            # For long videos, return a processing job that can be polled
            active_jobs[job_id] = GenerationJob(
                job_id=job_id,
                platform="sora",
                prompt=prompt,
                content_type="video",
                status=JobStatus.PROCESSING,
                duration=duration,
                cost=calculate_cost("sora", duration)
            ).to_dict()

            return {
                "job_id": job_id,
                "status": "processing",
                "platform": "sora",
                "message": "Generation started - poll for status"
            }

        except Exception as e:
            logger.error(f"Sora generation error: {e}")
            return {"error": str(e)}


async def generate_with_veo2(
    prompt: str,
    duration: int = 8,
    parameters: Optional[Dict] = None
) -> Dict:
    """
    Generate video using Google Veo2.

    Veo2 is Google's advanced video generation model integrated with Gemini,
    capable of generating high-quality, photorealistic videos.
    """
    if not GOOGLE_API_KEY:
        return {"error": "Google API key not configured"}

    job_id = hashlib.md5(f"{prompt}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]

    async with httpx.AsyncClient() as client:
        try:
            # Google Veo2 via Vertex AI / Generative AI API
            response = await client.post(
                f"{API_ENDPOINTS['veo2']}/models/veo-2.0-generate-001:generateVideo",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": {
                        "text": prompt
                    },
                    "videoConfig": {
                        "aspectRatio": parameters.get("aspect_ratio", "16:9") if parameters else "16:9",
                        "durationSec": min(duration, 20),  # Veo2 max duration
                        "personGeneration": parameters.get("person_generation", "ALLOW_ADULT") if parameters else "ALLOW_ADULT",
                        "numberOfVideos": 1
                    },
                    "outputConfig": {
                        "compressionQuality": parameters.get("quality", "HIGH") if parameters else "HIGH"
                    }
                },
                timeout=90.0
            )

            cost = calculate_cost("veo2", duration)

            if response.status_code == 200:
                result = response.json()

                # Veo2 returns an operation that needs to be polled
                operation_name = result.get("name", job_id)

                active_jobs[job_id] = GenerationJob(
                    job_id=job_id,
                    platform="veo2",
                    prompt=prompt,
                    content_type="video",
                    status=JobStatus.PROCESSING,
                    duration=duration,
                    cost=cost,
                    parameters={
                        "operation_name": operation_name,
                        **(parameters or {})
                    }
                ).to_dict()

                return {
                    "job_id": job_id,
                    "operation_name": operation_name,
                    "status": "processing",
                    "platform": "veo2",
                    "estimated_time": duration * 2,  # Rough estimate
                    "cost_estimate": cost
                }

            elif response.status_code == 400:
                return {"error": "Invalid request to Veo2", "details": response.text}
            elif response.status_code == 403:
                return {"error": "Veo2 access denied - check API key and quotas"}
            else:
                return {"error": f"Veo2 API error: {response.status_code}", "details": response.text}

        except httpx.TimeoutException:
            # Start async generation
            active_jobs[job_id] = GenerationJob(
                job_id=job_id,
                platform="veo2",
                prompt=prompt,
                content_type="video",
                status=JobStatus.PROCESSING,
                duration=duration,
                cost=calculate_cost("veo2", duration)
            ).to_dict()

            return {
                "job_id": job_id,
                "status": "processing",
                "platform": "veo2",
                "message": "Generation started - poll for status"
            }

        except Exception as e:
            logger.error(f"Veo2 generation error: {e}")
            return {"error": str(e)}


async def poll_veo2_status(operation_name: str) -> Dict:
    """Poll Veo2 operation status"""
    if not GOOGLE_API_KEY:
        return {"error": "Google API key not configured"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_ENDPOINTS['veo2']}/{operation_name}",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()

                if result.get("done"):
                    # Operation completed
                    video_result = result.get("response", {})
                    return {
                        "status": "completed",
                        "videos": video_result.get("generatedVideos", []),
                        "operation_name": operation_name
                    }
                else:
                    # Still processing
                    return {
                        "status": "processing",
                        "progress": result.get("metadata", {}).get("progress", 0),
                        "operation_name": operation_name
                    }
            else:
                return {"error": f"Status check failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Veo2 status check error: {e}")
            return {"error": str(e)}


async def poll_sora_status(job_id: str) -> Dict:
    """Poll Sora job status"""
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_ENDPOINTS['sora']}/videos/generations/{job_id}",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")

                if status == "succeeded":
                    return {
                        "status": "completed",
                        "url": result.get("url"),
                        "job_id": job_id
                    }
                elif status == "failed":
                    return {
                        "status": "failed",
                        "error": result.get("error", "Unknown error"),
                        "job_id": job_id
                    }
                else:
                    return {
                        "status": "processing",
                        "progress": result.get("progress", 0),
                        "job_id": job_id
                    }
            else:
                return {"error": f"Status check failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Sora status check error: {e}")
            return {"error": str(e)}

@app.post("/list-tools")
async def list_tools():
    """List available AI generation tools - MCP endpoint"""
    tools = [
        {
            "name": "generate_video",
            "description": "Generate video using AI platforms (Runway, Pika, Sora, Veo2)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt describing the video"
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["runway", "pika", "sora", "veo2"],
                        "description": "AI platform to use"
                    },
                    "duration": {
                        "type": "number",
                        "description": "Video duration in seconds"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Platform-specific parameters"
                    }
                },
                "required": ["prompt", "platform"]
            }
        },
        {
            "name": "generate_image",
            "description": "Generate image using AI platforms (Midjourney, Stable Diffusion, Nano Banana)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt describing the image"
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["midjourney", "stable_diffusion", "nano_banana"],
                        "description": "AI platform to use"
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "What to avoid in the image"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Platform-specific parameters"
                    }
                },
                "required": ["prompt", "platform"]
            }
        },
        {
            "name": "check_generation_status",
            "description": "Check the status of a generation job",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID to check"
                    },
                    "platform": {
                        "type": "string",
                        "description": "Platform that created the job"
                    }
                },
                "required": ["job_id", "platform"]
            }
        },
        {
            "name": "cancel_generation",
            "description": "Cancel an ongoing generation job",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID to cancel"
                    },
                    "platform": {
                        "type": "string",
                        "description": "Platform running the job"
                    }
                },
                "required": ["job_id", "platform"]
            }
        }
    ]
    
    return {"tools": tools}

@app.post("/call-tool")
async def call_tool(request: Request):
    """Execute tool with streaming response - MCP endpoint"""
    try:
        data = await request.json()
        tool_name = data.get("name")
        args = data.get("arguments", {})
        
        logger.info(f"Executing tool: {tool_name} with args: {args}")
        
        async def generate() -> AsyncGenerator[str, None]:
            """Stream generation updates via SSE"""
            # Send initial status
            yield f"data: {json.dumps({'status': 'starting', 'tool': tool_name})}\n\n"
            
            result = {}
            
            if tool_name == "generate_video":
                platform = args.get("platform")
                prompt = args.get("prompt")
                duration = args.get("duration", 5)
                parameters = args.get("parameters", {})
                
                yield f"data: {json.dumps({'status': 'processing', 'message': f'Generating video with {platform}'})}\n\n"
                
                if platform == "runway":
                    result = await generate_with_runway(prompt, duration, parameters)
                elif platform == "pika":
                    result = await generate_with_pika(prompt, parameters)
                elif platform == "sora":
                    result = await generate_with_sora(prompt, duration, parameters)
                elif platform == "veo2":
                    result = await generate_with_veo2(prompt, duration, parameters)
                else:
                    result = {"error": f"Unknown platform: {platform}"}
            
            elif tool_name == "generate_image":
                platform = args.get("platform")
                prompt = args.get("prompt")
                negative_prompt = args.get("negative_prompt", "")
                parameters = args.get("parameters", {})
                
                yield f"data: {json.dumps({'status': 'processing', 'message': f'Generating image with {platform}'})}\n\n"
                
                if platform == "midjourney":
                    result = await generate_with_midjourney(prompt, parameters)
                elif platform == "stable_diffusion":
                    result = await generate_with_stable_diffusion(prompt, negative_prompt, parameters)
                elif platform == "nano_banana":
                    result = await generate_with_nano_banana(prompt, parameters)
                else:
                    result = {"error": f"Unknown platform: {platform}"}
            
            elif tool_name == "check_generation_status":
                job_id = args.get("job_id")
                platform = args.get("platform")
                
                # Check in active jobs
                if job_id in active_jobs:
                    result = active_jobs[job_id]
                else:
                    result = {"status": "unknown", "message": "Job not found"}
            
            elif tool_name == "cancel_generation":
                job_id = args.get("job_id")
                platform = args.get("platform")
                
                if job_id in active_jobs:
                    active_jobs[job_id]["status"] = "cancelled"
                    result = {"status": "cancelled", "job_id": job_id}
                else:
                    result = {"error": "Job not found"}
            
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            # Send final result
            yield f"data: {json.dumps({'status': 'complete', 'result': result})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CineVibe AI Platforms MCP Server",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": len(active_jobs)
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "CineVibe AI Platforms MCP Server",
        "version": "1.0.0",
        "description": "MCP server providing access to AI video/image generation platforms",
        "endpoints": [
            "/list-tools - List available MCP tools",
            "/call-tool - Execute MCP tool",
            "/health - Health check"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8500))
    uvicorn.run(app, host="0.0.0.0", port=port)