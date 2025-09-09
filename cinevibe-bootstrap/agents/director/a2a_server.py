"""
A2A Server for Director Orchestrator Agent
Central coordinator for the entire film production pipeline
Based on InstaVibe's Orchestrator A2A pattern
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

from a2a import A2AServer, AgentCard
from google_cloud_adk import Runner
from google_cloud_adk.services import (
    InMemoryArtifactService,
    InMemorySessionService,
    InMemoryVectorDB
)

from agent import director, register_remote_agents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Agent Card
agent_card = AgentCard(
    name="Director Orchestrator",
    description="Central coordinator managing the entire film production pipeline",
    version="1.0.0",
    capabilities=[
        "script_analysis_coordination",
        "character_design_management",
        "storyboard_orchestration",
        "video_generation_pipeline",
        "quality_assurance",
        "multi_agent_coordination"
    ],
    model_info={
        "model": "gemini-2.0-flash",
        "provider": "Google"
    },
    metadata={
        "author": "CineVibe Team",
        "category": "orchestration",
        "role": "central_coordinator",
        "managed_agents": ["script_analyzer", "visual_consistency", "generation_platform"]
    }
)

# Create A2A server
server = A2AServer(agent_card=agent_card)

# Create ADK services
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()
vector_db = InMemoryVectorDB()

class DirectorExecutor:
    """Executor for director orchestration tasks"""
    
    def __init__(self):
        self.runner = Runner(
            agent=director,
            artifact_service=artifact_service,
            session_service=session_service,
            vector_db=vector_db
        )
        self.production_sessions = {}  # Track active productions
        self.registered_agents = False
    
    async def ensure_agents_registered(self):
        """Ensure remote agents are registered"""
        if not self.registered_agents:
            result = await register_remote_agents()
            logger.info(f"Agent registration: {result}")
            self.registered_agents = True
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestration task"""
        try:
            # Ensure agents are registered
            await self.ensure_agents_registered()
            
            task_type = task.get("type", "unknown")
            
            if task_type == "start_production":
                return await self.start_production(task)
            elif task_type == "analyze_script":
                return await self.analyze_script(task)
            elif task_type == "create_characters":
                return await self.create_characters(task)
            elif task_type == "generate_storyboard":
                return await self.generate_storyboard(task)
            elif task_type == "generate_videos":
                return await self.generate_videos(task)
            elif task_type == "get_status":
                return await self.get_production_status(task)
            else:
                # General orchestration
                session_id = task.get("session_id", "default_production")
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
            logger.error(f"Error executing director task: {e}")
            return {"status": "error", "error": str(e)}
    
    async def start_production(self, task: Dict) -> Dict:
        """Start a new film production"""
        production_info = task.get("input", {})
        
        production_id = f"prod_{production_info.get('title', 'untitled').replace(' ', '_').lower()}"
        session = await session_service.get_or_create(production_id)
        
        # Store production session
        self.production_sessions[production_id] = {
            "title": production_info.get("title"),
            "script": production_info.get("script"),
            "status": "initialized",
            "phases": []
        }
        
        prompt = f"""Start new film production:
        Title: {production_info.get('title')}
        Script Length: {len(production_info.get('script', ''))} characters
        Requirements: {production_info.get('requirements', 'standard')}
        
        Create production plan and begin Phase 1: Script Analysis."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            production_plan = json.loads(result.messages[-1].content)
            
            self.production_sessions[production_id]["plan"] = production_plan
            self.production_sessions[production_id]["status"] = "script_analysis"
            
            return {
                "status": "success",
                "production_id": production_id,
                "plan": production_plan
            }
        
        return {"status": "failed", "error": "Could not start production"}
    
    async def analyze_script(self, task: Dict) -> Dict:
        """Coordinate script analysis"""
        script_data = task.get("input", {})
        production_id = script_data.get("production_id", "default")
        
        session = await session_service.get_or_create(f"{production_id}_analysis")
        
        prompt = f"""Analyze screenplay:
        Title: {script_data.get('title')}
        Script: {script_data.get('script')}
        
        Delegate to Script Analyzer agent and get:
        - Character list with descriptions
        - Scene breakdown
        - Location list
        - Emotional arc
        Store results in database."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            analysis = json.loads(result.messages[-1].content)
            
            if production_id in self.production_sessions:
                self.production_sessions[production_id]["analysis"] = analysis
                self.production_sessions[production_id]["status"] = "character_design"
            
            return {
                "status": "success",
                "analysis": analysis,
                "next_phase": "character_design"
            }
        
        return {"status": "failed", "error": "Script analysis failed"}
    
    async def create_characters(self, task: Dict) -> Dict:
        """Coordinate character DNA creation"""
        characters = task.get("input", {}).get("characters", [])
        production_id = task.get("input", {}).get("production_id", "default")
        
        session = await session_service.get_or_create(f"{production_id}_characters")
        
        prompt = f"""Create Character DNA for all characters:
        Characters: {json.dumps(characters)}
        
        For each character:
        1. Send to Visual Consistency agent
        2. Create detailed DNA profile
        3. Generate reference images
        4. Store in database
        
        Ensure consistency tokens are defined."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            character_dnas = json.loads(result.messages[-1].content)
            
            if production_id in self.production_sessions:
                self.production_sessions[production_id]["character_dnas"] = character_dnas
                self.production_sessions[production_id]["status"] = "storyboarding"
            
            return {
                "status": "success",
                "character_dnas": character_dnas,
                "next_phase": "storyboarding"
            }
        
        return {"status": "failed", "error": "Character creation failed"}
    
    async def generate_storyboard(self, task: Dict) -> Dict:
        """Coordinate storyboard generation"""
        scenes = task.get("input", {}).get("scenes", [])
        production_id = task.get("input", {}).get("production_id", "default")
        
        session = await session_service.get_or_create(f"{production_id}_storyboard")
        
        prompt = f"""Generate storyboards for all scenes:
        Scenes: {json.dumps(scenes)}
        
        For each scene:
        1. Get character DNA from Visual Consistency
        2. Create scene style guide
        3. Generate establishing, medium, close-up shots
        4. Validate consistency
        5. Store in database"""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            storyboards = json.loads(result.messages[-1].content)
            
            if production_id in self.production_sessions:
                self.production_sessions[production_id]["storyboards"] = storyboards
                self.production_sessions[production_id]["status"] = "video_generation"
            
            return {
                "status": "success",
                "storyboards": storyboards,
                "next_phase": "video_generation"
            }
        
        return {"status": "failed", "error": "Storyboard generation failed"}
    
    async def generate_videos(self, task: Dict) -> Dict:
        """Coordinate video generation"""
        scenes = task.get("input", {}).get("scenes", [])
        production_id = task.get("input", {}).get("production_id", "default")
        
        session = await session_service.get_or_create(f"{production_id}_videos")
        
        prompt = f"""Generate videos for key scenes:
        Scenes: {json.dumps(scenes)}
        
        For each scene:
        1. Get optimized prompts from Visual Consistency
        2. Select best platform via Generation Platform agent
        3. Generate video content
        4. Validate quality and consistency
        5. Store successful assets
        
        Track costs and generation times."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            videos = json.loads(result.messages[-1].content)
            
            if production_id in self.production_sessions:
                self.production_sessions[production_id]["videos"] = videos
                self.production_sessions[production_id]["status"] = "completed"
            
            return {
                "status": "success",
                "videos": videos,
                "production_status": "completed"
            }
        
        return {"status": "failed", "error": "Video generation failed"}
    
    async def get_production_status(self, task: Dict) -> Dict:
        """Get production pipeline status"""
        production_id = task.get("input", {}).get("production_id")
        
        if production_id in self.production_sessions:
            return {
                "status": "success",
                "production": self.production_sessions[production_id]
            }
        
        return {"status": "error", "error": "Production not found"}

# Create executor instance
executor = DirectorExecutor()

@server.on_task
async def handle_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming A2A task requests"""
    logger.info(f"Director received task: {task.get('type', 'unknown')}")
    return await executor.execute(task)

def main():
    """Main entry point"""
    port = int(os.environ.get("PORT", 8003))
    host = "0.0.0.0"
    
    logger.info(f"Starting Director Orchestrator A2A Server on {host}:{port}")
    logger.info(f"Agent Card: {json.dumps(agent_card.dict(), indent=2)}")
    
    # Log remote agent addresses
    remote_agents = os.environ.get("REMOTE_AGENT_ADDRESSES", "").split(",")
    logger.info(f"Remote agents to coordinate: {remote_agents}")
    
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()