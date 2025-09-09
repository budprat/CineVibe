"""
Script Analyzer Agent for CineVibe
Parses screenplays and extracts narrative elements
Based on InstaVibe's Social Profiling Agent pattern
"""

from google_cloud_adk import Agent, Tool
import re
import json
from typing import Dict, List, Optional
from google.cloud import spanner
import os

# Initialize Spanner client
spanner_client = spanner.Client()
instance_id = os.environ.get("SPANNER_INSTANCE_ID", "cinevibe-graph-instance")
database_id = os.environ.get("SPANNER_DATABASE_ID", "graphdb")

def extract_characters(script_text: str) -> List[Dict]:
    """
    Extract character names and descriptions from screenplay format.
    Looks for CHARACTER NAME (age, description) patterns.
    """
    characters = []
    
    # Pattern for character introductions: NAME (age, description)
    char_pattern = r'^([A-Z][A-Z\s]+)\s*\(([^)]+)\)'
    
    for match in re.finditer(char_pattern, script_text, re.MULTILINE):
        name = match.group(1).strip()
        description = match.group(2).strip()
        
        # Parse age if present
        age_match = re.search(r'(\d+)', description)
        age = int(age_match.group(1)) if age_match else None
        
        characters.append({
            "name": name,
            "description": description,
            "age": age,
            "first_appearance": match.start()
        })
    
    return characters

def extract_scenes(script_text: str) -> List[Dict]:
    """
    Extract scene headings from screenplay.
    Parses INT./EXT. LOCATION - TIME patterns.
    """
    scenes = []
    
    # Standard screenplay scene heading format
    scene_pattern = r'^(INT\.|EXT\.|INT/EXT\.)\s+([^-\n]+)(?:\s*-\s*(.+))?$'
    
    scene_number = 1
    for match in re.finditer(scene_pattern, script_text, re.MULTILINE):
        scenes.append({
            "scene_number": scene_number,
            "type": match.group(1).strip(),
            "location": match.group(2).strip(),
            "time": match.group(3).strip() if match.group(3) else "DAY",
            "position": match.start()
        })
        scene_number += 1
    
    return scenes

def extract_dialogue(script_text: str) -> List[Dict]:
    """
    Extract dialogue with speaker and emotional context.
    """
    dialogue_entries = []
    
    # Pattern to match character name followed by dialogue
    dialogue_pattern = r'^([A-Z][A-Z\s]+)\n(?:\(([^)]+)\)\n)?(.+?)(?=\n[A-Z]|\n\n|$)'
    
    for match in re.finditer(dialogue_pattern, script_text, re.MULTILINE | re.DOTALL):
        dialogue_entries.append({
            "character": match.group(1).strip(),
            "direction": match.group(2) if match.group(2) else None,
            "text": match.group(3).strip()
        })
    
    return dialogue_entries

def analyze_emotional_arc(scenes: List[Dict], dialogue: List[Dict]) -> Dict:
    """
    Analyze the emotional progression of the script.
    """
    # Simple emotional analysis based on scene progression
    arc = {
        "act_structure": [],
        "tension_points": [],
        "character_arcs": {}
    }
    
    # Divide into three acts
    total_scenes = len(scenes)
    if total_scenes > 0:
        act1_end = total_scenes // 4
        act2_end = (total_scenes * 3) // 4
        
        arc["act_structure"] = [
            {"act": 1, "scenes": scenes[:act1_end], "type": "setup"},
            {"act": 2, "scenes": scenes[act1_end:act2_end], "type": "confrontation"},
            {"act": 3, "scenes": scenes[act2_end:], "type": "resolution"}
        ]
    
    return arc

def store_in_graph_database(script_data: Dict) -> str:
    """
    Store extracted script elements in Spanner Graph Database.
    """
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)
    
    with database.batch() as batch:
        # Store characters
        for char in script_data.get("characters", []):
            batch.insert(
                table="Character",
                columns=["character_id", "name", "age", "physical_description", "personality_traits"],
                values=[(
                    f"char_{char['name'].lower().replace(' ', '_')}",
                    char["name"],
                    char.get("age"),
                    json.dumps({"description": char["description"]}),
                    []
                )]
            )
        
        # Store scenes
        for scene in script_data.get("scenes", []):
            batch.insert(
                table="Scene",
                columns=["scene_id", "script_id", "scene_number", "location", "time_of_day"],
                values=[(
                    f"scene_{scene['scene_number']:03d}",
                    script_data.get("script_id", "default"),
                    scene["scene_number"],
                    scene["location"],
                    scene["time"]
                )]
            )
    
    return "Script data stored in graph database"

# Create the Script Analyzer Agent
script_analyzer = Agent(
    model="gemini-2.0-flash",
    instructions="""You are the Script Analyzer Agent for CineVibe film production.
    
    Your responsibilities:
    1. Parse screenplays in standard format (Final Draft, Fountain, plain text)
    2. Extract all narrative elements:
       - Characters with descriptions and ages
       - Scene locations and times
       - Dialogue with emotional context
       - Props and important objects
    3. Analyze story structure and emotional arc
    4. Store all elements in the graph database for other agents
    
    When you receive a script:
    1. Use extract_characters() to find all characters
    2. Use extract_scenes() to identify all scenes
    3. Use extract_dialogue() to capture conversations
    4. Use analyze_emotional_arc() to understand pacing
    5. Store everything with store_in_graph_database()
    
    Output format:
    {
        "script_id": "unique_id",
        "title": "extracted or generated",
        "characters": [...],
        "scenes": [...],
        "locations": [...],
        "props": [...],
        "emotional_arc": {...},
        "summary": "brief story summary"
    }
    
    Be thorough and precise - other agents depend on your analysis for visual consistency.
    """,
    tools=[
        Tool(extract_characters),
        Tool(extract_scenes),
        Tool(extract_dialogue),
        Tool(analyze_emotional_arc),
        Tool(store_in_graph_database)
    ]
)