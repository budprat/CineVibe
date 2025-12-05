"""
Script Analyzer Agent for CineVibe
Parses screenplays and extracts narrative elements
Based on InstaVibe's Social Profiling Agent pattern
"""

from google_cloud_adk import Agent, Tool
import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from google.cloud import spanner
import os
import logging
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils.resilience import retry_with_backoff, circuit_breaker
from utils.logging_utils import AgentLogger, set_correlation_id
from utils.validation import ScriptAnalysisInput, validate_input

# Configure logging
logger = logging.getLogger(__name__)
agent_logger = AgentLogger("script_analyzer")

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


def parse_script_elements(script_text: str) -> Dict:
    """
    Parse all script elements in a single comprehensive call.
    This is the main entry point for complete script analysis.

    Args:
        script_text: The screenplay text to analyze

    Returns:
        Complete script analysis with characters, scenes, dialogue,
        locations, props, action lines, and transitions
    """
    logger.info("Starting comprehensive script parsing")

    if not script_text or not script_text.strip():
        return {
            "error": "Empty script provided",
            "characters": [],
            "scenes": [],
            "dialogue": [],
            "locations": [],
            "props": [],
            "transitions": [],
            "action_lines": []
        }

    # Extract all components
    characters = extract_characters(script_text)
    scenes = extract_scenes(script_text)
    dialogue = extract_dialogue(script_text)

    # Extract unique locations
    locations = list(set(scene.get("location", "") for scene in scenes if scene.get("location")))

    # Extract props (items mentioned in descriptions)
    props = extract_props(script_text)

    # Extract action lines
    action_lines = extract_action_lines(script_text)

    # Extract transitions (CUT TO, FADE IN, etc.)
    transitions = extract_transitions(script_text)

    # Analyze emotional arc
    emotional_arc = analyze_emotional_arc(scenes, dialogue)

    # Map characters to scenes
    characters_in_scenes = map_characters_to_scenes(script_text, characters, scenes)

    # Generate script summary
    summary = generate_script_summary(script_text, characters, scenes)

    result = {
        "characters": characters,
        "scenes": scenes,
        "dialogue": dialogue,
        "locations": locations,
        "props": props,
        "transitions": transitions,
        "action_lines": action_lines,
        "emotional_arc": emotional_arc,
        "characters_in_scenes": characters_in_scenes,
        "summary": summary,
        "statistics": {
            "total_characters": len(characters),
            "total_scenes": len(scenes),
            "total_dialogue_lines": len(dialogue),
            "total_locations": len(locations),
            "total_props": len(props),
            "estimated_pages": len(script_text) // 3000  # Rough estimate
        }
    }

    logger.info(f"Script parsing complete: {len(characters)} characters, {len(scenes)} scenes")
    return result


def extract_props(script_text: str) -> List[Dict]:
    """
    Extract props and important objects from script.
    Looks for emphasized items in action descriptions.
    """
    props = []
    seen_props = set()

    # Pattern for items in ALL CAPS within action lines
    prop_patterns = [
        r'(?:picks up|holds|carries|grabs|looks at|examines|puts down)\s+(?:a\s+)?([A-Z][A-Z\s]+)',
        r'(?:a|an|the)\s+([A-Z][A-Z\s]{2,})\s+(?:sits|lies|rests|hangs)',
        r'(?:hands|gives|takes)\s+(?:a\s+)?([A-Z][A-Z\s]+)',
    ]

    for pattern in prop_patterns:
        for match in re.finditer(pattern, script_text, re.IGNORECASE):
            prop_name = match.group(1).strip().upper()

            # Filter out character names and common words
            if prop_name not in seen_props and len(prop_name) > 2:
                # Check it's not likely a character name
                if not re.match(r'^[A-Z]+$', prop_name) or len(prop_name) > 10:
                    seen_props.add(prop_name)
                    props.append({
                        "name": prop_name.title(),
                        "first_mention": match.start(),
                        "importance": "normal"
                    })

    return props


def extract_action_lines(script_text: str) -> List[Dict]:
    """
    Extract action/description lines from script.
    These are the non-dialogue narrative descriptions.
    """
    action_lines = []

    # Split by scene headings to process each scene
    scene_pattern = r'(INT\.|EXT\.|INT/EXT\.)'
    parts = re.split(scene_pattern, script_text)

    for i, part in enumerate(parts):
        if re.match(scene_pattern, part):
            continue

        # Extract paragraphs that aren't dialogue
        lines = part.split('\n\n')
        for line in lines:
            line = line.strip()

            # Skip empty, dialogue (all caps name followed by text), and scene headings
            if not line:
                continue
            if re.match(r'^[A-Z]{2,}\s*\n', line):  # Character name + dialogue
                continue
            if re.match(r'^(INT\.|EXT\.)', line):
                continue
            if line.startswith('(') and line.endswith(')'):  # Parentheticals
                continue

            # This is likely an action line
            if len(line) > 10 and not line.isupper():
                action_lines.append({
                    "text": line[:500],  # Limit length
                    "position": script_text.find(line)
                })

    return action_lines[:100]  # Limit to first 100 action lines


def extract_transitions(script_text: str) -> List[Dict]:
    """
    Extract scene transitions (CUT TO, FADE IN, DISSOLVE TO, etc.)
    """
    transitions = []

    transition_patterns = [
        r'(FADE IN:?)',
        r'(FADE OUT\.?)',
        r'(FADE TO BLACK\.?)',
        r'(CUT TO:?)',
        r'(DISSOLVE TO:?)',
        r'(SMASH CUT TO:?)',
        r'(MATCH CUT TO:?)',
        r'(JUMP CUT TO:?)',
        r'(WIPE TO:?)',
        r'(TIME CUT:?)',
        r'(THE END\.?)',
    ]

    for pattern in transition_patterns:
        for match in re.finditer(pattern, script_text, re.MULTILINE):
            transitions.append({
                "type": match.group(1).strip().rstrip(':').rstrip('.'),
                "position": match.start()
            })

    # Sort by position
    transitions.sort(key=lambda x: x['position'])

    return transitions


def map_characters_to_scenes(
    script_text: str,
    characters: List[Dict],
    scenes: List[Dict]
) -> Dict[str, List[int]]:
    """
    Map which characters appear in which scenes.
    Returns dict mapping character names to scene numbers.
    """
    character_scenes = {char['name']: [] for char in characters}

    # Get scene boundaries
    scene_boundaries = []
    for i, scene in enumerate(scenes):
        start = scene.get('position', 0)
        end = scenes[i + 1]['position'] if i + 1 < len(scenes) else len(script_text)
        scene_boundaries.append((scene['scene_number'], start, end))

    # For each scene, check which characters appear
    for scene_num, start, end in scene_boundaries:
        scene_text = script_text[start:end]

        for char in characters:
            char_name = char['name']
            # Check if character name appears (as dialogue header or in description)
            if re.search(rf'\b{re.escape(char_name)}\b', scene_text, re.IGNORECASE):
                character_scenes[char_name].append(scene_num)

    return character_scenes


def generate_script_summary(
    script_text: str,
    characters: List[Dict],
    scenes: List[Dict]
) -> str:
    """
    Generate a brief summary of the script.
    """
    # Get main characters (those that appear first or most)
    main_chars = [c['name'] for c in characters[:3]] if characters else ["Unknown characters"]

    # Get key locations
    locations = list(set(s.get('location', '') for s in scenes[:5]))

    # Build summary
    summary_parts = []

    if main_chars:
        summary_parts.append(f"A story featuring {', '.join(main_chars)}")

    if locations:
        summary_parts.append(f"set in locations including {', '.join(locations[:3])}")

    if scenes:
        summary_parts.append(f"told across {len(scenes)} scenes")

    return ". ".join(summary_parts) + "." if summary_parts else "Script summary unavailable."


def extract_title_and_metadata(script_text: str) -> Dict:
    """
    Extract title and metadata from script header.
    """
    metadata = {
        "title": None,
        "author": None,
        "draft": None,
        "date": None
    }

    # Look for title in first 500 characters
    header = script_text[:500]

    # Title patterns
    title_patterns = [
        r'Title:\s*(.+?)(?:\n|$)',
        r'^"(.+?)"',
        r'^([A-Z][A-Za-z\s]+)\s*\n\s*(?:by|written by)',
    ]

    for pattern in title_patterns:
        match = re.search(pattern, header, re.MULTILINE | re.IGNORECASE)
        if match:
            metadata["title"] = match.group(1).strip()
            break

    # Author pattern
    author_match = re.search(r'(?:by|written by)[:\s]+(.+?)(?:\n|$)', header, re.IGNORECASE)
    if author_match:
        metadata["author"] = author_match.group(1).strip()

    # Draft pattern
    draft_match = re.search(r'((?:first|second|third|final|revised)\s+draft)', header, re.IGNORECASE)
    if draft_match:
        metadata["draft"] = draft_match.group(1).strip()

    return metadata


def full_script_analysis(
    script_text: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    store_results: bool = False
) -> Dict:
    """
    Perform complete script analysis and optionally store in database.
    This is the comprehensive analysis function.

    Args:
        script_text: The screenplay text
        title: Optional title (will be extracted if not provided)
        author: Optional author (will be extracted if not provided)
        store_results: Whether to store results in database

    Returns:
        Complete script analysis with all elements
    """
    logger.info("Starting full script analysis")
    agent_logger.log_task_start("full_script_analysis", "analysis_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"))

    start_time = datetime.utcnow()

    # Extract metadata if not provided
    metadata = extract_title_and_metadata(script_text)
    title = title or metadata.get("title") or "Untitled Script"
    author = author or metadata.get("author") or "Unknown"

    # Generate script ID
    script_id = f"script_{hashlib.md5(f'{title}_{datetime.utcnow()}'.encode()).hexdigest()[:12]}"

    # Parse all elements
    elements = parse_script_elements(script_text)

    # Build complete analysis result
    analysis = {
        "script_id": script_id,
        "title": title,
        "author": author,
        "draft": metadata.get("draft"),
        "characters": elements["characters"],
        "scenes": elements["scenes"],
        "dialogue": elements["dialogue"],
        "locations": elements["locations"],
        "props": elements["props"],
        "transitions": elements["transitions"],
        "action_lines": elements.get("action_lines", []),
        "emotional_arc": elements["emotional_arc"],
        "characters_in_scenes": elements.get("characters_in_scenes", {}),
        "summary": elements["summary"],
        "statistics": elements["statistics"],
        "analyzed_at": datetime.utcnow().isoformat()
    }

    # Store in database if requested
    if store_results:
        try:
            store_in_graph_database(analysis)
            analysis["stored"] = True
        except Exception as e:
            logger.error(f"Failed to store script data: {e}")
            analysis["stored"] = False
            analysis["store_error"] = str(e)

    elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    agent_logger.log_task_complete("full_script_analysis", script_id, elapsed_ms)

    return analysis


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
        Tool(store_in_graph_database),
        Tool(parse_script_elements),
        Tool(extract_props),
        Tool(extract_transitions),
        Tool(extract_title_and_metadata),
        Tool(full_script_analysis),
    ]
)