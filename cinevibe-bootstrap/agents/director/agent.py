"""
Director Orchestrator Agent for CineVibe
Central coordinator that manages the entire film production pipeline
Based on InstaVibe's Orchestrator Agent pattern
"""

from google_cloud_adk import Agent, Tool
from a2a import A2AClient
import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get remote agent URLs from environment
REMOTE_AGENT_ADDRESSES = os.environ.get("REMOTE_AGENT_ADDRESSES", "").split(",")

# Initialize A2A client for communicating with remote agents
a2a_client = A2AClient()

# Registry of available agents and their capabilities
agent_registry = {}

async def register_remote_agents():
    """
    Register all remote agents by fetching their Agent Cards.
    This allows the Director to know what each agent can do.
    """
    global agent_registry
    
    for url in REMOTE_AGENT_ADDRESSES:
        if not url:
            continue
            
        try:
            # Fetch agent card
            agent_card = await a2a_client.fetch_agent_card(url)
            
            # Register agent
            agent_name = agent_card.get("name", "unknown")
            agent_registry[agent_name] = {
                "url": url,
                "card": agent_card,
                "capabilities": agent_card.get("capabilities", []),
                "status": "available"
            }
            
            logger.info(f"Registered agent: {agent_name} at {url}")
            
        except Exception as e:
            logger.error(f"Failed to register agent at {url}: {e}")
    
    return f"Registered {len(agent_registry)} agents"

async def send_to_agent(
    agent_name: str,
    task_type: str,
    task_data: Dict
) -> Dict:
    """
    Send a task to a remote agent via A2A protocol.
    """
    if agent_name not in agent_registry:
        return {"error": f"Agent {agent_name} not found in registry"}
    
    agent_info = agent_registry[agent_name]
    
    try:
        # Prepare task message
        task = {
            "type": task_type,
            "input": task_data,
            "session_id": f"director_{datetime.utcnow().isoformat()}",
            "sender": "Director"
        }
        
        # Send task via A2A
        response = await a2a_client.send_task(
            agent_url=agent_info["url"],
            task=task
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending task to {agent_name}: {e}")
        return {"error": str(e)}

def create_production_plan(
    script_analysis: Dict,
    project_requirements: Dict
) -> Dict:
    """
    Create a detailed production plan based on script analysis.
    """
    characters = script_analysis.get("characters", [])
    scenes = script_analysis.get("scenes", [])
    
    plan = {
        "project_id": f"proj_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "phases": [],
        "timeline": {},
        "resource_requirements": {},
        "estimated_costs": {}
    }
    
    # Phase 1: Character Design
    character_tasks = []
    for char in characters:
        character_tasks.append({
            "task": "create_character_dna",
            "character": char,
            "priority": "high" if "main" in char.get("description", "").lower() else "normal"
        })
    
    plan["phases"].append({
        "phase": 1,
        "name": "Character Design",
        "tasks": character_tasks,
        "estimated_duration": len(character_tasks) * 10  # 10 minutes per character
    })
    
    # Phase 2: Scene Storyboarding
    scene_tasks = []
    for scene in scenes:
        scene_tasks.append({
            "task": "generate_storyboard",
            "scene": scene,
            "shots_needed": ["establishing", "medium", "close-up"]
        })
    
    plan["phases"].append({
        "phase": 2,
        "name": "Storyboard Generation",
        "tasks": scene_tasks,
        "estimated_duration": len(scene_tasks) * 15  # 15 minutes per scene
    })
    
    # Phase 3: Asset Generation
    generation_tasks = []
    for scene in scenes:
        for char in characters:
            generation_tasks.append({
                "task": "generate_scene_assets",
                "scene": scene,
                "character": char,
                "content_type": "video",
                "duration": 5
            })
    
    plan["phases"].append({
        "phase": 3,
        "name": "Asset Generation",
        "tasks": generation_tasks,
        "estimated_duration": len(generation_tasks) * 5  # 5 minutes per asset
    })
    
    # Calculate timeline
    total_duration = sum(phase["estimated_duration"] for phase in plan["phases"])
    plan["timeline"]["total_minutes"] = total_duration
    plan["timeline"]["total_hours"] = total_duration / 60
    
    # Estimate costs (simplified)
    plan["estimated_costs"]["character_design"] = len(characters) * 10  # $10 per character
    plan["estimated_costs"]["storyboarding"] = len(scenes) * 15  # $15 per scene
    plan["estimated_costs"]["generation"] = len(generation_tasks) * 5  # $5 per generation
    plan["estimated_costs"]["total"] = sum(plan["estimated_costs"].values())
    
    return plan

def track_production_progress(
    project_id: str,
    phase: int,
    task_completed: str
) -> Dict:
    """
    Track progress of production tasks.
    """
    # In production, this would update a database
    progress = {
        "project_id": project_id,
        "phase": phase,
        "task_completed": task_completed,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "in_progress"
    }
    
    logger.info(f"Progress update: {progress}")
    
    return progress

def handle_agent_failure(
    agent_name: str,
    task: Dict,
    error: str
) -> Dict:
    """
    Handle failures from remote agents and determine recovery strategy.
    """
    recovery_strategies = {
        "Script Analyzer": {
            "retry_count": 3,
            "fallback": "manual_script_parsing",
            "alert_level": "medium"
        },
        "Visual Consistency": {
            "retry_count": 2,
            "fallback": "use_default_character_profiles",
            "alert_level": "high"
        },
        "Generation Platform": {
            "retry_count": 5,
            "fallback": "switch_to_alternative_platform",
            "alert_level": "medium"
        }
    }
    
    strategy = recovery_strategies.get(agent_name, {
        "retry_count": 1,
        "fallback": "manual_intervention",
        "alert_level": "high"
    })
    
    return {
        "agent": agent_name,
        "task": task,
        "error": error,
        "recovery_strategy": strategy,
        "timestamp": datetime.utcnow().isoformat()
    }

# Create the Director Orchestrator Agent
director = Agent(
    model="gemini-2.0-flash",
    instructions="""You are the Director Orchestrator for CineVibe film production.
    
    You are the central coordinator managing the entire production pipeline from
    script to final generated content. You delegate tasks to specialized agents
    and ensure consistency and quality throughout the process.
    
    Available Remote Agents (via A2A):
    1. Script Analyzer - Parses scripts and extracts narrative elements
    2. Visual Consistency - Maintains character DNA and style consistency
    3. Generation Platform - Generates videos/images via AI platforms
    
    Your Workflow:
    
    PHASE 1: SCRIPT ANALYSIS
    - Receive screenplay from user
    - Send to Script Analyzer agent
    - Receive character list, scene breakdown, locations
    - Store in production database
    
    PHASE 2: CHARACTER DESIGN
    - For each character from script:
      - Send to Visual Consistency agent for DNA creation
      - Get character profiles with visual specifications
      - Validate consistency tokens
    
    PHASE 3: STYLE GUIDE CREATION
    - For each unique scene:
      - Send scene details to Visual Consistency
      - Get scene-specific style guides
      - Define lighting, mood, color palette
    
    PHASE 4: STORYBOARD GENERATION
    - For each scene:
      - Get character DNA from Visual Consistency
      - Request prompt generation for shots
      - Send to Generation Platform for image creation
      - Validate consistency scores
    
    PHASE 5: VIDEO GENERATION
    - For key scenes:
      - Prepare optimized prompts with character DNA
      - Select best platform via Generation Platform agent
      - Monitor generation progress
      - Validate output quality
    
    PHASE 6: QUALITY ASSURANCE
    - Review all generated assets
    - Check consistency scores
    - Request regeneration if needed
    - Compile final deliverables
    
    Task Management:
    - Use register_remote_agents() to discover available agents
    - Use send_to_agent() to delegate specific tasks
    - Use create_production_plan() to organize workflow
    - Use track_production_progress() to monitor completion
    - Use handle_agent_failure() for error recovery
    
    Quality Standards:
    - Character consistency score must be >= 0.8
    - All scenes must have style guides
    - Generation quality score must be >= 0.8
    - Maintain cinematic quality throughout
    
    Communication Protocol:
    - Always acknowledge user requests
    - Provide progress updates for long operations
    - Report any failures with recovery plans
    - Summarize results at each phase completion
    
    Remember: You are the conductor of this creative orchestra. Ensure every
    agent plays their part in harmony to create a cohesive, professional film.
    """,
    tools=[
        Tool(register_remote_agents),
        Tool(send_to_agent),
        Tool(create_production_plan),
        Tool(track_production_progress),
        Tool(handle_agent_failure)
    ]
)