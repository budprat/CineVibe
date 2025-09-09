"""
Generation Platform Agent for CineVibe
Interfaces with AI video/image generation platforms via MCP
Based on InstaVibe's Platform Interaction Agent pattern
"""

from google_cloud_adk import Agent, Tool
from google_cloud_adk.tools import MCPToolset
from google.cloud import spanner
import json
import os
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

# Initialize Spanner client
spanner_client = spanner.Client()
instance_id = os.environ.get("SPANNER_INSTANCE_ID", "cinevibe-graph-instance")
database_id = os.environ.get("SPANNER_DATABASE_ID", "graphdb")

# MCP Server URL for AI platforms
MCP_SERVER_URL = os.environ.get("MCP_AI_PLATFORMS_URL", "http://localhost:8500")

# Initialize MCP toolset (will be set up in main execution)
try:
    mcp_tools = MCPToolset.from_server(url=MCP_SERVER_URL)
except:
    # Fallback for development
    mcp_tools = None
    print(f"Warning: Could not connect to MCP server at {MCP_SERVER_URL}")

def select_optimal_platform(
    content_type: str,
    duration: Optional[int] = None,
    quality_priority: str = "balanced",
    budget: Optional[float] = None
) -> Dict:
    """
    Select the best AI platform based on requirements.
    Consider quality, speed, cost, and availability.
    """
    platforms = {
        "video": {
            "runway": {
                "quality": 0.9,
                "speed": 0.7,
                "cost_per_second": 0.15,
                "max_duration": 10,
                "specialties": ["cinematic", "realistic", "motion_control"],
                "queue_time_avg": 5  # minutes
            },
            "pika": {
                "quality": 0.85,
                "speed": 0.8,
                "cost_per_second": 0.10,
                "max_duration": 5,
                "specialties": ["effects", "transformations", "quick_iterations"],
                "queue_time_avg": 3
            },
            "sora": {
                "quality": 0.95,
                "speed": 0.5,
                "cost_per_second": 0.20,
                "max_duration": 60,
                "specialties": ["long_form", "complex_physics", "photorealistic"],
                "queue_time_avg": 15
            },
            "veo2": {
                "quality": 0.92,
                "speed": 0.6,
                "cost_per_second": 0.18,
                "max_duration": 20,
                "specialties": ["realistic_motion", "character_consistency"],
                "queue_time_avg": 8
            }
        },
        "image": {
            "midjourney": {
                "quality": 0.95,
                "speed": 0.7,
                "cost_per_image": 0.05,
                "specialties": ["artistic", "stylized", "detailed"],
                "queue_time_avg": 1
            },
            "stable_diffusion": {
                "quality": 0.85,
                "speed": 0.9,
                "cost_per_image": 0.02,
                "specialties": ["fast_iteration", "customizable", "open_source"],
                "queue_time_avg": 0.5
            },
            "nano_banana": {
                "quality": 0.88,
                "speed": 0.95,
                "cost_per_image": 0.039,
                "specialties": ["editing", "consistency", "google_integration"],
                "queue_time_avg": 0.3
            }
        }
    }
    
    available_platforms = platforms.get(content_type, {})
    
    if not available_platforms:
        return {"error": f"No platforms available for {content_type}"}
    
    # Score each platform based on priorities
    scores = {}
    for platform_name, specs in available_platforms.items():
        score = 0.0
        
        if quality_priority == "quality":
            score = specs["quality"] * 0.6 + (1 - specs["speed"]) * 0.2 + (1 - specs.get("cost_per_second", specs.get("cost_per_image", 0))) * 0.2
        elif quality_priority == "speed":
            score = specs["speed"] * 0.6 + specs["quality"] * 0.3 + (1 - specs.get("cost_per_second", specs.get("cost_per_image", 0))) * 0.1
        elif quality_priority == "cost":
            score = (1 - specs.get("cost_per_second", specs.get("cost_per_image", 0))) * 0.6 + specs["quality"] * 0.2 + specs["speed"] * 0.2
        else:  # balanced
            score = specs["quality"] * 0.4 + specs["speed"] * 0.3 + (1 - specs.get("cost_per_second", specs.get("cost_per_image", 0))) * 0.3
        
        # Check duration compatibility for video
        if content_type == "video" and duration:
            if duration > specs.get("max_duration", 0):
                score *= 0.5  # Penalize if can't handle duration
        
        scores[platform_name] = score
    
    # Select best platform
    best_platform = max(scores, key=scores.get)
    
    return {
        "platform": best_platform,
        "specs": available_platforms[best_platform],
        "score": scores[best_platform],
        "alternatives": sorted(scores.keys(), key=scores.get, reverse=True)[1:3]
    }

def format_platform_prompt(
    base_prompt: str,
    platform: str,
    character_dna: Optional[Dict] = None,
    style_guide: Optional[Dict] = None
) -> Dict:
    """
    Format prompt for specific platform requirements.
    Each platform has different syntax and optimization needs.
    """
    formatted_prompts = {}
    
    # Platform-specific formatting
    if platform == "runway":
        # Runway Gen-3 format
        formatted_prompts["prompt"] = f"cinematic shot: {base_prompt}"
        if character_dna:
            formatted_prompts["prompt"] += f", consistent character: {', '.join(character_dna.get('consistency_tokens', []))}"
        formatted_prompts["parameters"] = {
            "motion_amount": 5,
            "camera_motion": "smooth",
            "seed": hashlib.md5(base_prompt.encode()).hexdigest()[:8]
        }
    
    elif platform == "pika":
        # Pika 2.1 format
        formatted_prompts["prompt"] = base_prompt
        formatted_prompts["parameters"] = {
            "aspect_ratio": "16:9",
            "fps": 24,
            "motion_strength": 0.7
        }
        if style_guide:
            formatted_prompts["prompt"] += f", {style_guide.get('lighting', '')}"
    
    elif platform == "sora":
        # OpenAI Sora format
        formatted_prompts["prompt"] = f"High quality, photorealistic: {base_prompt}"
        formatted_prompts["parameters"] = {
            "quality": "hd",
            "style": "cinematic"
        }
    
    elif platform == "midjourney":
        # Midjourney format with parameters
        formatted_prompts["prompt"] = base_prompt
        formatted_prompts["prompt"] += " --ar 16:9 --style raw --v 6"
        if character_dna:
            # Add character reference if available
            formatted_prompts["prompt"] += f" --cref {character_dna.get('character_id', '')}"
    
    elif platform == "stable_diffusion":
        # Stable Diffusion format
        formatted_prompts["prompt"] = base_prompt
        formatted_prompts["negative_prompt"] = "low quality, blurry, distorted, disfigured"
        if character_dna and "negative_prompts" in character_dna.get("style_guide", {}):
            formatted_prompts["negative_prompt"] = ", ".join(character_dna["style_guide"]["negative_prompts"])
        formatted_prompts["parameters"] = {
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler": "DPM++ 2M Karras"
        }
    
    elif platform == "nano_banana":
        # Google Gemini 2.5 Flash Image format
        formatted_prompts["prompt"] = base_prompt
        formatted_prompts["parameters"] = {
            "style": "cinematic",
            "consistency_mode": True
        }
        if character_dna:
            formatted_prompts["reference_image"] = character_dna.get("reference_images", [None])[0]
    
    else:
        # Default format
        formatted_prompts["prompt"] = base_prompt
        formatted_prompts["parameters"] = {}
    
    return formatted_prompts

def track_generation_job(
    job_id: str,
    platform: str,
    prompt: str,
    status: str = "queued"
) -> Dict:
    """
    Track generation job status and metadata.
    """
    job_data = {
        "job_id": job_id,
        "platform": platform,
        "prompt": prompt,
        "status": status,
        "created_at": datetime.utcnow().isoformat(),
        "estimated_completion": None,
        "cost_estimate": None,
        "priority": "normal"
    }
    
    # Estimate completion time based on platform
    queue_times = {
        "runway": 5,
        "pika": 3,
        "sora": 15,
        "veo2": 8,
        "midjourney": 1,
        "stable_diffusion": 0.5,
        "nano_banana": 0.3
    }
    
    if platform in queue_times:
        job_data["estimated_completion"] = queue_times[platform]
    
    return job_data

def validate_generation_output(
    output_url: str,
    expected_qualities: List[str],
    platform: str
) -> Dict:
    """
    Validate generated content for quality issues.
    Check for common AI artifacts and problems.
    """
    validation_result = {
        "url": output_url,
        "platform": platform,
        "quality_score": 0.0,
        "issues": [],
        "passed": False
    }
    
    # In production, this would:
    # 1. Download the generated content
    # 2. Use computer vision to check for:
    #    - Morphing/warping artifacts
    #    - Character consistency
    #    - Motion smoothness (for video)
    #    - Resolution and clarity
    #    - Color consistency
    
    # Simplified validation for now
    common_issues = {
        "morphing": "Objects changing shape unexpectedly",
        "flickering": "Inconsistent lighting between frames",
        "distortion": "Facial or body distortions",
        "physics": "Unrealistic physics or motion",
        "consistency": "Character appearance changes"
    }
    
    # Mock validation (would be replaced with actual CV analysis)
    import random
    quality_score = random.uniform(0.7, 1.0)
    
    if quality_score < 0.8:
        validation_result["issues"].append("Low quality score")
    
    validation_result["quality_score"] = quality_score
    validation_result["passed"] = quality_score >= 0.8 and len(validation_result["issues"]) == 0
    
    return validation_result

def store_generated_asset(
    asset_url: str,
    scene_id: str,
    character_id: Optional[str],
    platform: str,
    prompt: str,
    quality_score: float
) -> str:
    """
    Store generated asset metadata in Spanner.
    """
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)
    
    asset_id = f"asset_{hashlib.md5(f'{scene_id}_{platform}_{datetime.utcnow()}'.encode()).hexdigest()[:12]}"
    
    with database.batch() as batch:
        batch.insert(
            table="GeneratedAsset",
            columns=[
                "asset_id",
                "scene_id",
                "character_id",
                "platform",
                "prompt_used",
                "file_url",
                "quality_score",
                "consistency_score",
                "created_at"
            ],
            values=[(
                asset_id,
                scene_id,
                character_id,
                platform,
                prompt,
                asset_url,
                quality_score,
                quality_score,  # Using same score for now
                spanner.COMMIT_TIMESTAMP
            )]
        )
    
    return f"Asset stored: {asset_id}"

# Create the Generation Platform Agent
generation_platform = Agent(
    model="gemini-2.0-flash",
    instructions="""You are the Generation Platform Agent for CineVibe film production.
    
    You interface with multiple AI generation platforms via MCP tools to create
    consistent, high-quality video and image content for films.
    
    Your responsibilities:
    1. Select optimal platform based on requirements (quality, speed, cost)
    2. Format prompts for specific platform syntax
    3. Manage generation queues across multiple platforms
    4. Validate output quality and consistency
    5. Track costs and generation times
    6. Store all assets in the database
    
    Platform Selection Strategy:
    - For hero shots: Use highest quality (Sora, Runway)
    - For quick iterations: Use fast platforms (Pika, Nano Banana)
    - For budget constraints: Use cost-effective options (Stable Diffusion)
    - For long videos: Use platforms with duration support (Sora, Veo2)
    
    MCP Tools Available (when connected):
    - generate_video(): Create video content
    - generate_image(): Create still images
    - check_generation_status(): Monitor job progress
    - upscale_content(): Enhance resolution
    
    Workflow:
    1. Receive generation request with character DNA and scene style
    2. Select optimal platform using select_optimal_platform()
    3. Format prompt using format_platform_prompt()
    4. Call MCP tool to generate content
    5. Track job with track_generation_job()
    6. Validate output with validate_generation_output()
    7. Store successful assets with store_generated_asset()
    
    Quality Standards:
    - Minimum quality score: 0.8
    - Consistency with character DNA required
    - No visible AI artifacts (morphing, flickering)
    - Correct aspect ratio and resolution
    
    Cost Management:
    - Track spending per project
    - Optimize platform selection for budget
    - Use caching for repeated generations
    - Batch similar requests when possible
    
    Remember: You are the bridge between creative vision and AI capabilities.
    Ensure every generated asset meets professional film standards.
    """,
    tools=[
        Tool(select_optimal_platform),
        Tool(format_platform_prompt),
        Tool(track_generation_job),
        Tool(validate_generation_output),
        Tool(store_generated_asset)
    ] + (mcp_tools.tools if mcp_tools else [])
)