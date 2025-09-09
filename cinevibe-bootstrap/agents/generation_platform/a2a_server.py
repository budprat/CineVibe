"""
A2A Server for Generation Platform Agent
Interfaces with AI generation platforms for video/image creation
Based on InstaVibe's Platform Interaction Agent A2A pattern
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

from a2a import A2AServer, AgentCard
from google_cloud_adk import Runner
from google_cloud_adk.services import (
    InMemoryArtifactService,
    InMemorySessionService,
    InMemoryVectorDB
)

from agent import generation_platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Agent Card
agent_card = AgentCard(
    name="Generation Platform",
    description="Interfaces with AI video/image generation platforms via MCP",
    version="1.0.0",
    capabilities=[
        "platform_selection",
        "prompt_formatting",
        "generation_management",
        "quality_validation",
        "cost_tracking"
    ],
    model_info={
        "model": "gemini-2.0-flash",
        "provider": "Google"
    },
    metadata={
        "author": "CineVibe Team",
        "category": "content_generation",
        "supported_platforms": ["runway", "pika", "sora", "midjourney", "stable_diffusion", "nano_banana"],
        "mcp_enabled": True
    }
)

# Create A2A server
server = A2AServer(agent_card=agent_card)

# Create ADK services
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()
vector_db = InMemoryVectorDB()

class GenerationPlatformExecutor:
    """Executor for generation platform tasks"""
    
    def __init__(self):
        self.runner = Runner(
            agent=generation_platform,
            artifact_service=artifact_service,
            session_service=session_service,
            vector_db=vector_db
        )
        self.active_jobs = {}  # Track generation jobs
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generation task"""
        try:
            task_type = task.get("type", "unknown")
            
            if task_type == "generate_video":
                return await self.generate_video(task)
            elif task_type == "generate_image":
                return await self.generate_image(task)
            elif task_type == "check_status":
                return await self.check_status(task)
            elif task_type == "select_platform":
                return await self.select_platform(task)
            else:
                # General task handling
                session_id = task.get("session_id", "default_session")
                session = await session_service.get_or_create(session_id)
                
                user_input = task.get("input", {}).get("request", "")
                result = await self.runner.run(
                    user_input=user_input,
                    session=session
                )
                
                if result and result.messages:
                    return {
                        "status": "success",
                        "result": result.messages[-1].content,
                        "session_id": session_id
                    }
                
                return {"status": "failed", "error": "No result generated"}
                
        except Exception as e:
            logger.error(f"Error executing generation task: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_video(self, task: Dict) -> Dict:
        """Generate video content"""
        request = task.get("input", {})
        
        session = await session_service.get_or_create(f"video_gen_{request.get('scene_id', 'unknown')}")
        
        prompt = f"""Generate video for:
        Scene: {request.get('scene')}
        Character DNA: {json.dumps(request.get('character_dna', {}))}
        Duration: {request.get('duration', 5)} seconds
        Platform: {request.get('platform', 'auto')}
        
        Select optimal platform, format prompt, and generate video."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            generation_result = json.loads(result.messages[-1].content)
            
            # Track job
            job_id = generation_result.get("job_id")
            if job_id:
                self.active_jobs[job_id] = generation_result
            
            return {
                "status": "success",
                "generation": generation_result,
                "job_id": job_id
            }
        
        return {"status": "failed", "error": "Video generation failed"}
    
    async def generate_image(self, task: Dict) -> Dict:
        """Generate image content"""
        request = task.get("input", {})
        
        session = await session_service.get_or_create(f"image_gen_{request.get('scene_id', 'unknown')}")
        
        prompt = f"""Generate image for:
        Scene: {request.get('scene')}
        Character DNA: {json.dumps(request.get('character_dna', {}))}
        Shot Type: {request.get('shot_type', 'medium')}
        Platform: {request.get('platform', 'auto')}
        
        Select optimal platform, format prompt, and generate image."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            generation_result = json.loads(result.messages[-1].content)
            
            # Track job
            job_id = generation_result.get("job_id")
            if job_id:
                self.active_jobs[job_id] = generation_result
            
            return {
                "status": "success",
                "generation": generation_result,
                "job_id": job_id
            }
        
        return {"status": "failed", "error": "Image generation failed"}
    
    async def check_status(self, task: Dict) -> Dict:
        """Check generation job status"""
        job_id = task.get("input", {}).get("job_id")
        
        if job_id in self.active_jobs:
            job_info = self.active_jobs[job_id]
            
            # In production, would check actual platform status
            return {
                "status": "success",
                "job_status": job_info.get("status", "processing"),
                "job_info": job_info
            }
        
        return {"status": "error", "error": "Job not found"}
    
    async def select_platform(self, task: Dict) -> Dict:
        """Select optimal generation platform"""
        request = task.get("input", {})
        
        session = await session_service.get_or_create("platform_selection")
        
        prompt = f"""Select optimal platform for:
        Content Type: {request.get('content_type', 'video')}
        Duration: {request.get('duration')} seconds
        Quality Priority: {request.get('quality_priority', 'balanced')}
        Budget: ${request.get('budget', 'unlimited')}
        
        Analyze requirements and recommend best platform."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            platform_selection = json.loads(result.messages[-1].content)
            
            return {
                "status": "success",
                "platform": platform_selection
            }
        
        return {"status": "failed", "error": "Platform selection failed"}

# Create executor instance
executor = GenerationPlatformExecutor()

@server.on_task
async def handle_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming A2A task requests"""
    logger.info(f"Received task: {task.get('type', 'unknown')}")
    return await executor.execute(task)

def main():
    """Main entry point"""
    port = int(os.environ.get("PORT", 8002))
    host = "0.0.0.0"
    
    logger.info(f"Starting Generation Platform A2A Server on {host}:{port}")
    logger.info(f"Agent Card: {json.dumps(agent_card.dict(), indent=2)}")
    logger.info(f"MCP Server URL: {os.environ.get('MCP_AI_PLATFORMS_URL', 'not set')}")
    
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()