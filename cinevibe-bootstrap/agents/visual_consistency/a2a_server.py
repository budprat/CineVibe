"""
A2A Server for Visual Consistency Agent
Maintains character and style consistency across all generated content
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

from agent import visual_consistency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Agent Card
agent_card = AgentCard(
    name="Visual Consistency",
    description="Maintains character DNA and visual style consistency for film production",
    version="1.0.0",
    capabilities=[
        "character_dna_creation",
        "consistency_validation",
        "style_guide_generation",
        "prompt_optimization",
        "visual_reference_search"
    ],
    model_info={
        "model": "gemini-2.0-flash",
        "provider": "Google"
    },
    metadata={
        "author": "CineVibe Team",
        "category": "visual_production",
        "consistency_threshold": 0.8,
        "supported_formats": ["image", "video", "prompt"]
    }
)

# Create A2A server
server = A2AServer(agent_card=agent_card)

# Create ADK services
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()
vector_db = InMemoryVectorDB()

class VisualConsistencyExecutor:
    """Executor for visual consistency tasks"""
    
    def __init__(self):
        self.runner = Runner(
            agent=visual_consistency,
            artifact_service=artifact_service,
            session_service=session_service,
            vector_db=vector_db
        )
        self.character_registry = {}  # Cache character DNA
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute visual consistency task"""
        try:
            task_type = task.get("type", "unknown")
            
            if task_type == "create_character":
                return await self.create_character(task)
            elif task_type == "validate_consistency":
                return await self.validate_consistency(task)
            elif task_type == "generate_prompt":
                return await self.generate_prompt(task)
            elif task_type == "create_style_guide":
                return await self.create_style_guide(task)
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
            logger.error(f"Error executing visual consistency task: {e}")
            return {"status": "error", "error": str(e)}
    
    async def create_character(self, task: Dict) -> Dict:
        """Create character DNA profile"""
        character_info = task.get("input", {})
        
        session = await session_service.get_or_create(f"char_{character_info.get('name', 'unknown')}")
        
        prompt = f"""Create Character DNA for:
        Name: {character_info.get('name')}
        Description: {character_info.get('description')}
        Age: {character_info.get('age', 'unknown')}
        
        Generate complete character DNA profile and store it."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            character_dna = json.loads(result.messages[-1].content)
            self.character_registry[character_dna["character_id"]] = character_dna
            
            return {
                "status": "success",
                "character_dna": character_dna,
                "character_id": character_dna["character_id"]
            }
        
        return {"status": "failed", "error": "Could not create character DNA"}
    
    async def validate_consistency(self, task: Dict) -> Dict:
        """Validate content consistency"""
        validation_request = task.get("input", {})
        character_id = validation_request.get("character_id")
        content = validation_request.get("content")
        
        if character_id not in self.character_registry:
            return {"status": "error", "error": "Character not found"}
        
        character_dna = self.character_registry[character_id]
        
        session = await session_service.get_or_create(f"validate_{character_id}")
        
        prompt = f"""Validate this content for character consistency:
        Character DNA: {json.dumps(character_dna)}
        Content to validate: {content}
        
        Check consistency and provide score."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            validation = json.loads(result.messages[-1].content)
            return {
                "status": "success",
                "validation": validation,
                "passed": validation.get("consistency_score", 0) >= 0.8
            }
        
        return {"status": "failed", "error": "Validation failed"}
    
    async def generate_prompt(self, task: Dict) -> Dict:
        """Generate consistent prompt for content generation"""
        request = task.get("input", {})
        
        session = await session_service.get_or_create(f"prompt_gen")
        
        prompt = f"""Generate a consistent prompt for:
        Character: {request.get('character_id')}
        Scene: {request.get('scene')}
        Action: {request.get('action')}
        Shot Type: {request.get('shot_type', 'medium')}
        
        Create optimized prompt for AI generation."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            prompt_data = json.loads(result.messages[-1].content)
            return {
                "status": "success",
                "prompt": prompt_data
            }
        
        return {"status": "failed", "error": "Could not generate prompt"}
    
    async def create_style_guide(self, task: Dict) -> Dict:
        """Create scene style guide"""
        scene_info = task.get("input", {})
        
        session = await session_service.get_or_create(f"style_{scene_info.get('scene_id', 'unknown')}")
        
        prompt = f"""Create visual style guide for:
        Scene: {scene_info.get('location')}
        Time: {scene_info.get('time_of_day')}
        Mood: {scene_info.get('mood', 'neutral')}
        
        Define complete visual style for consistency."""
        
        result = await self.runner.run(user_input=prompt, session=session)
        
        if result and result.messages:
            style_guide = json.loads(result.messages[-1].content)
            return {
                "status": "success",
                "style_guide": style_guide
            }
        
        return {"status": "failed", "error": "Could not create style guide"}

# Create executor instance
executor = VisualConsistencyExecutor()

@server.on_task
async def handle_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming A2A task requests"""
    logger.info(f"Received task: {task.get('type', 'unknown')}")
    return await executor.execute(task)

def main():
    """Main entry point"""
    port = int(os.environ.get("PORT", 8001))
    host = "0.0.0.0"
    
    logger.info(f"Starting Visual Consistency A2A Server on {host}:{port}")
    logger.info(f"Agent Card: {json.dumps(agent_card.dict(), indent=2)}")
    
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()