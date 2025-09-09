"""
A2A Server for Script Analyzer Agent
Enables agent-to-agent communication via A2A protocol
Based on InstaVibe's A2A server pattern
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

from agent import script_analyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Agent Card (like InstaVibe's agent cards)
agent_card = AgentCard(
    name="Script Analyzer",
    description="Parses screenplays and extracts narrative elements for film production",
    version="1.0.0",
    capabilities=[
        "script_parsing",
        "character_extraction", 
        "scene_breakdown",
        "dialogue_analysis",
        "emotional_arc_mapping"
    ],
    model_info={
        "model": "gemini-2.0-flash",
        "provider": "Google"
    },
    metadata={
        "author": "CineVibe Team",
        "category": "pre-production",
        "input_formats": ["screenplay", "fountain", "pdf"],
        "output_format": "structured_json"
    }
)

# Create A2A server
server = A2AServer(agent_card=agent_card)

# Create ADK services (in-memory for development)
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()
vector_db = InMemoryVectorDB()

class ScriptAnalyzerExecutor:
    """Executor class to handle A2A requests"""
    
    def __init__(self):
        self.runner = Runner(
            agent=script_analyzer,
            artifact_service=artifact_service,
            session_service=session_service,
            vector_db=vector_db
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute script analysis task from A2A request
        """
        try:
            # Extract the script content from the task
            script_content = task.get("input", {}).get("script", "")
            
            if not script_content:
                return {
                    "error": "No script content provided",
                    "status": "failed"
                }
            
            # Create or get session
            session_id = task.get("session_id", "default_session")
            session = await session_service.get_or_create(session_id)
            
            # Run the agent
            result = await self.runner.run(
                user_input=f"Analyze this screenplay:\n\n{script_content}",
                session=session
            )
            
            # Extract the last message from the result
            if result and result.messages:
                last_message = result.messages[-1]
                return {
                    "status": "success",
                    "analysis": json.loads(last_message.content),
                    "session_id": session_id
                }
            
            return {
                "status": "failed",
                "error": "No analysis generated"
            }
            
        except Exception as e:
            logger.error(f"Error executing script analysis: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

# Create executor instance
executor = ScriptAnalyzerExecutor()

@server.on_task
async def handle_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming A2A task requests
    """
    logger.info(f"Received task: {task.get('type', 'unknown')}")
    return await executor.execute(task)

def main():
    """Main entry point"""
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting Script Analyzer A2A Server on {host}:{port}")
    logger.info(f"Agent Card: {json.dumps(agent_card.dict(), indent=2)}")
    
    # Run the server
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()