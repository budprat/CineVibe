"""
Visual Consistency Agent for CineVibe
Maintains character DNA and visual style consistency across generated content
Based on InstaVibe's Event Planning Agent pattern
"""

from google_cloud_adk import Agent, Tool, ToolSet
from google_cloud_adk.tools import GoogleSearchTool
from google.cloud import spanner
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
import os
import base64
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils.resilience import retry_with_backoff, circuit_breaker
from utils.logging_utils import AgentLogger, set_correlation_id
from utils.validation import CharacterDNAInput, SceneInput, validate_input

# Configure logging
logger = logging.getLogger(__name__)
agent_logger = AgentLogger("visual_consistency")

# Initialize Spanner client
spanner_client = spanner.Client()
instance_id = os.environ.get("SPANNER_INSTANCE_ID", "cinevibe-graph-instance")
database_id = os.environ.get("SPANNER_DATABASE_ID", "graphdb")

def create_character_dna(
    name: str,
    description: str,
    age: Optional[int] = None,
    reference_images: Optional[List[str]] = None
) -> Dict:
    """
    Create a detailed Character DNA profile for consistent generation.
    This is the core of maintaining visual consistency across all content.
    """
    # Generate unique character ID
    char_id = f"char_{name.lower().replace(' ', '_')}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
    
    # Parse description for physical attributes
    physical_attributes = {
        "age": age or "adult",
        "gender": "unspecified",
        "height": "average",
        "build": "average",
        "hair_color": "brown",
        "hair_style": "medium length",
        "eye_color": "brown",
        "skin_tone": "medium",
        "distinguishing_features": []
    }
    
    # Extract attributes from description
    description_lower = description.lower()
    
    # Hair colors
    for color in ["blonde", "brown", "black", "red", "gray", "grey", "white"]:
        if color in description_lower:
            physical_attributes["hair_color"] = color
            break
    
    # Eye colors
    for color in ["blue", "brown", "green", "hazel", "gray", "grey", "black"]:
        if f"{color} eyes" in description_lower or f"eyes {color}" in description_lower:
            physical_attributes["eye_color"] = color
            break
    
    # Build types
    for build in ["athletic", "slim", "muscular", "stocky", "heavy", "thin"]:
        if build in description_lower:
            physical_attributes["build"] = build
            break
    
    # Create prompt templates for different scenarios
    prompt_templates = {
        "base": f"A {age or 'person'} with {physical_attributes['hair_color']} hair and {physical_attributes['eye_color']} eyes, {physical_attributes['build']} build",
        "close_up": f"Close-up portrait of a {age or 'person'} with {physical_attributes['hair_color']} hair and {physical_attributes['eye_color']} eyes, detailed facial features, cinematic lighting",
        "full_body": f"Full body shot of a {age or 'person'}, {physical_attributes['build']} build, {physical_attributes['hair_color']} hair, {physical_attributes['eye_color']} eyes, standing pose",
        "action": f"A {age or 'person'} with {physical_attributes['hair_color']} hair in motion, dynamic pose, {physical_attributes['build']} physique"
    }
    
    # Style guidelines for consistency
    style_guide = {
        "lighting": "cinematic, natural lighting",
        "color_grading": "film-like, slightly desaturated",
        "camera_angle": "eye-level, professional cinematography",
        "quality_markers": ["8k", "high quality", "detailed", "photorealistic"],
        "negative_prompts": ["cartoon", "anime", "illustration", "painting", "low quality"]
    }
    
    character_dna = {
        "character_id": char_id,
        "name": name,
        "physical_attributes": physical_attributes,
        "original_description": description,
        "prompt_templates": prompt_templates,
        "style_guide": style_guide,
        "consistency_tokens": [
            name,
            physical_attributes["hair_color"] + " hair",
            physical_attributes["eye_color"] + " eyes",
            physical_attributes["build"] + " build"
        ],
        "reference_images": reference_images or [],
        "version": 1
    }
    
    return character_dna

def validate_character_consistency(
    character_dna: Dict,
    generated_content: str,
    content_type: str = "image"
) -> Dict:
    """
    Validate if generated content matches the character DNA.
    In production, this would use computer vision APIs.
    """
    # This is a simplified validation
    # In production, you would:
    # 1. Use Google Vision API to analyze the generated image
    # 2. Extract features from the image
    # 3. Compare with character DNA attributes
    
    consistency_score = 0.0
    issues = []
    suggestions = []
    
    # Check if consistency tokens appear in generation prompt
    if content_type == "prompt":
        prompt_lower = generated_content.lower()
        matched_tokens = 0
        
        for token in character_dna.get("consistency_tokens", []):
            if token.lower() in prompt_lower:
                matched_tokens += 1
        
        consistency_score = matched_tokens / len(character_dna.get("consistency_tokens", [1]))
        
        if consistency_score < 0.8:
            issues.append("Missing key consistency tokens in prompt")
            suggestions.append("Include all character-specific tokens: " + 
                             ", ".join(character_dna["consistency_tokens"]))
    
    return {
        "consistency_score": consistency_score,
        "passed": consistency_score >= 0.8,
        "issues": issues,
        "suggestions": suggestions,
        "character_id": character_dna["character_id"]
    }

def create_scene_style_guide(
    scene_description: Dict,
    time_of_day: str,
    location: str,
    mood: Optional[str] = None
) -> Dict:
    """
    Create visual style guide for a specific scene.
    Ensures consistency across all shots in the scene.
    """
    # Lighting based on time of day
    lighting_guides = {
        "DAY": "natural daylight, soft shadows, warm tones",
        "NIGHT": "low key lighting, deep shadows, cool tones, practical lights",
        "DAWN": "golden hour, long shadows, warm orange tones",
        "DUSK": "magic hour, purple/pink sky, silhouettes",
        "AFTERNOON": "harsh sunlight, strong shadows, high contrast"
    }
    
    # Location-specific styling
    location_styles = {
        "INT": "interior lighting, window light, practical lamps",
        "EXT": "natural environment, weather conditions visible",
        "COFFEE SHOP": "warm ambiance, steam from cups, busy background",
        "OFFICE": "fluorescent lighting, clean lines, professional",
        "STREET": "urban environment, pedestrians, vehicles",
        "FOREST": "dappled sunlight, green tones, natural textures"
    }
    
    # Extract style elements
    lighting = lighting_guides.get(time_of_day.upper(), lighting_guides["DAY"])
    
    # Determine location style
    location_upper = location.upper()
    location_style = "neutral environment"
    for key, style in location_styles.items():
        if key in location_upper:
            location_style = style
            break
    
    style_guide = {
        "scene_id": f"scene_{location.replace(' ', '_').lower()}_{time_of_day.lower()}",
        "lighting": lighting,
        "location_style": location_style,
        "color_palette": determine_color_palette(time_of_day, mood),
        "camera_guidelines": {
            "shots": ["wide establishing", "medium shots", "close-ups for emotion"],
            "movement": "smooth, cinematic",
            "focus": "shallow depth of field for narrative focus"
        },
        "mood": mood or "neutral",
        "consistency_markers": [
            f"{time_of_day.lower()} lighting",
            location_style,
            "cinematic composition"
        ]
    }
    
    return style_guide

def determine_color_palette(time_of_day: str, mood: Optional[str]) -> List[str]:
    """Determine color palette based on time and mood"""
    palettes = {
        "DAY": ["warm whites", "soft blues", "natural greens"],
        "NIGHT": ["deep blues", "blacks", "accent lights"],
        "DAWN": ["oranges", "pinks", "soft purples"],
        "DUSK": ["purples", "oranges", "deep blues"]
    }
    
    mood_modifiers = {
        "tense": ["desaturated", "cool tones"],
        "romantic": ["warm", "soft focus"],
        "action": ["high contrast", "dynamic"],
        "sad": ["blue tones", "gray", "muted"]
    }
    
    base_palette = palettes.get(time_of_day.upper(), palettes["DAY"])
    
    if mood and mood.lower() in mood_modifiers:
        base_palette.extend(mood_modifiers[mood.lower()])
    
    return base_palette

def store_character_dna(character_dna: Dict) -> str:
    """
    Store Character DNA in Spanner Graph Database.
    """
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)
    
    with database.batch() as batch:
        batch.insert_or_update(
            table="Character",
            columns=[
                "character_id",
                "name",
                "age",
                "physical_description",
                "visual_dna",
                "created_at"
            ],
            values=[(
                character_dna["character_id"],
                character_dna["name"],
                character_dna["physical_attributes"].get("age"),
                json.dumps(character_dna["physical_attributes"]),
                json.dumps(character_dna),
                spanner.COMMIT_TIMESTAMP
            )]
        )
    
    return f"Character DNA stored: {character_dna['character_id']}"

def generate_consistency_prompt(
    character_dna: Dict,
    scene_style: Dict,
    action: str,
    shot_type: str = "medium"
) -> str:
    """
    Generate a highly consistent prompt for image/video generation.
    This is the key to maintaining visual consistency.
    """
    # Start with character base
    if shot_type in character_dna["prompt_templates"]:
        base_prompt = character_dna["prompt_templates"][shot_type]
    else:
        base_prompt = character_dna["prompt_templates"]["base"]
    
    # Add action
    prompt_parts = [base_prompt]
    if action:
        prompt_parts.append(action)
    
    # Add scene styling
    prompt_parts.append(scene_style["lighting"])
    prompt_parts.append(scene_style["location_style"])
    
    # Add quality markers
    prompt_parts.extend(character_dna["style_guide"]["quality_markers"])
    
    # Combine into final prompt
    final_prompt = ", ".join(prompt_parts)
    
    # Add negative prompts
    negative_prompt = ", ".join(character_dna["style_guide"]["negative_prompts"])
    
    return {
        "prompt": final_prompt,
        "negative_prompt": negative_prompt,
        "character_id": character_dna["character_id"],
        "scene_id": scene_style["scene_id"],
        "consistency_tokens": character_dna["consistency_tokens"]
    }


def maintain_scene_consistency(
    current_scene: Dict,
    character_appearances: Optional[Dict] = None,
    previous_scenes: Optional[List[Dict]] = None
) -> Dict:
    """
    Maintain visual consistency across scenes.
    Analyzes current scene against previous scenes and character appearances.

    Args:
        current_scene: Current scene data with characters, location, time
        character_appearances: Dict mapping character names to their appearance in scenes
        previous_scenes: List of previous scene data for continuity checking

    Returns:
        Consistency analysis with score, recommendations, and issues
    """
    logger.info(f"Analyzing scene consistency for scene {current_scene.get('scene_id', 'unknown')}")

    consistency_score = 1.0
    recommendations = []
    issues = []
    continuity_checks = []

    characters_in_scene = current_scene.get("characters", [])
    current_time = current_scene.get("time", "DAY")
    current_location = current_scene.get("location", "")

    # Check character appearance consistency
    if character_appearances and characters_in_scene:
        for char_name in characters_in_scene:
            if char_name in character_appearances:
                char_history = character_appearances[char_name]

                # Check for costume changes within same time period
                if previous_scenes:
                    for prev_scene in previous_scenes:
                        if char_name in prev_scene.get("characters", []):
                            prev_time = prev_scene.get("time", "DAY")

                            # Same time period should have same costume
                            if prev_time == current_time and prev_scene.get("location") == current_location:
                                # Check for costume consistency
                                scene_id = prev_scene.get("scene_id", "")
                                if scene_id in char_history:
                                    prev_costume = char_history[scene_id].get("clothing", "")
                                    current_costume = char_history.get(current_scene.get("scene_id", ""), {}).get("clothing", "")

                                    if prev_costume and current_costume and prev_costume != current_costume:
                                        issues.append(f"{char_name}: costume changed from '{prev_costume}' to '{current_costume}' in same location/time")
                                        consistency_score -= 0.15

    # Check lighting consistency with time of day
    lighting_map = {
        "DAY": ["natural", "bright", "warm", "sunlight"],
        "NIGHT": ["dark", "low-key", "moonlight", "artificial"],
        "DAWN": ["golden", "soft", "warm", "orange"],
        "DUSK": ["purple", "orange", "magic hour", "golden"],
    }

    expected_lighting = lighting_map.get(current_time.upper(), lighting_map["DAY"])
    continuity_checks.append({
        "check": "lighting_consistency",
        "expected": expected_lighting,
        "time_of_day": current_time
    })

    # Check scene transition logic
    if previous_scenes:
        last_scene = previous_scenes[-1]
        last_location = last_scene.get("location", "")
        last_time = last_scene.get("time", "DAY")

        # Flag unrealistic time jumps without transition
        time_order = ["DAWN", "MORNING", "DAY", "AFTERNOON", "DUSK", "NIGHT"]

        if last_time.upper() in time_order and current_time.upper() in time_order:
            last_idx = time_order.index(last_time.upper())
            curr_idx = time_order.index(current_time.upper())

            # Backwards time jump without scene break
            if curr_idx < last_idx and curr_idx != 0:
                recommendations.append(
                    f"Consider adding transition for time change from {last_time} to {current_time}"
                )

        # Check for character continuity
        last_chars = set(last_scene.get("characters", []))
        curr_chars = set(characters_in_scene)

        # Characters that disappeared without exit
        disappeared = last_chars - curr_chars
        if disappeared and last_location == current_location:
            recommendations.append(
                f"Characters {list(disappeared)} were in previous scene at same location but not in current"
            )

    # Calculate final score
    consistency_score = max(0.0, min(1.0, consistency_score))

    return {
        "consistency_score": consistency_score,
        "passed": consistency_score >= 0.8,
        "issues": issues,
        "recommendations": recommendations,
        "continuity_checks": continuity_checks,
        "scene_id": current_scene.get("scene_id"),
        "characters_analyzed": characters_in_scene
    }


def check_visual_continuity(
    current_scene: Dict,
    previous_scene: Dict
) -> Dict:
    """
    Check visual continuity between two consecutive scenes.
    Validates that visual elements maintain logical consistency.

    Args:
        current_scene: Current scene data
        previous_scene: Previous scene data with visual elements

    Returns:
        Continuity analysis with issues and recommendations
    """
    logger.info("Checking visual continuity between scenes")

    is_continuous = True
    issues = []
    recommendations = []
    visual_checks = []

    # Extract visual elements
    prev_visuals = previous_scene.get("visual_elements", {})
    curr_time = current_scene.get("time", "DAY")
    prev_time = previous_scene.get("time", "DAY")
    curr_location = current_scene.get("location", "")
    prev_location = previous_scene.get("location", "")

    # Same location checks
    if curr_location == prev_location:
        # Check for set dressing consistency
        visual_checks.append({
            "check": "same_location_continuity",
            "location": curr_location,
            "status": "requires_same_set"
        })

        # Time progression should be logical
        if curr_time != prev_time:
            recommendations.append(
                f"Time changed from {prev_time} to {curr_time} at same location - ensure lighting reflects this"
            )

    # Character visual continuity
    curr_chars = set(current_scene.get("characters", []))
    prev_chars = set(previous_scene.get("characters", []))
    common_chars = curr_chars & prev_chars

    for char in common_chars:
        if char in prev_visuals:
            char_visual = prev_visuals[char]

            # Check if character should maintain appearance
            if curr_location == prev_location:
                visual_checks.append({
                    "check": "character_appearance",
                    "character": char,
                    "expected_clothing": char_visual.get("clothing"),
                    "expected_hair": char_visual.get("hair_style")
                })

            # Note any injuries or changes that should persist
            if char_visual.get("injuries") or char_visual.get("damage"):
                recommendations.append(
                    f"Character {char} had visible injuries/damage in previous scene - maintain continuity"
                )

    # Prop continuity
    prev_props = set(previous_scene.get("props", []))
    curr_props = set(current_scene.get("props", []))

    if curr_location == prev_location:
        missing_props = prev_props - curr_props
        if missing_props:
            issues.append(f"Props missing from same location: {list(missing_props)}")
            is_continuous = False

    # Weather continuity (if outdoor)
    if "EXT" in curr_location or "EXT" in prev_location:
        prev_weather = previous_scene.get("weather", "clear")
        curr_weather = current_scene.get("weather", "clear")

        if prev_weather != curr_weather and curr_time == prev_time:
            recommendations.append(
                f"Weather changed from {prev_weather} to {curr_weather} - add transition if intentional"
            )

    return {
        "is_continuous": is_continuous and len(issues) == 0,
        "issues": issues,
        "recommendations": recommendations,
        "visual_checks": visual_checks,
        "common_characters": list(common_chars),
        "same_location": curr_location == prev_location
    }


def generate_visual_prompt(
    scene_context: Dict,
    character_dna: Optional[Dict] = None,
    platform: str = "stable_diffusion"
) -> Dict:
    """
    Generate optimized visual prompt for AI generation platforms.
    Creates platform-specific prompts with character DNA integration.

    Args:
        scene_context: Scene description, location, time, mood, camera_angle
        character_dna: Dict of character DNAs keyed by name
        platform: Target platform (stable_diffusion, midjourney, dalle3, runway, etc.)

    Returns:
        Platform-optimized prompt with style tags and negative prompts
    """
    logger.info(f"Generating visual prompt for platform: {platform}")

    description = scene_context.get("description", "")
    characters = scene_context.get("characters", [])
    location = scene_context.get("location", "")
    time_of_day = scene_context.get("time", "DAY")
    mood = scene_context.get("mood", "neutral")
    camera_angle = scene_context.get("camera_angle", "medium shot")

    # Build character descriptions from DNA
    char_descriptions = []
    if character_dna and characters:
        for char_name in characters:
            if char_name in character_dna:
                dna = character_dna[char_name]
                phys = dna.get("physical_attributes", {})

                char_desc = f"{char_name.lower()}"

                if phys.get("age"):
                    char_desc = f"{phys['age']}-year-old {char_desc}"

                if phys.get("hair_color"):
                    char_desc += f" with {phys['hair_color']} hair"

                if phys.get("eye_color"):
                    char_desc += f" and {phys['eye_color']} eyes"

                if phys.get("build") and phys["build"] != "average":
                    char_desc += f", {phys['build']} build"

                char_descriptions.append(char_desc)

    # Build lighting based on time
    lighting_styles = {
        "DAY": "natural daylight, soft shadows",
        "NIGHT": "low-key lighting, cinematic shadows, practical lights",
        "DAWN": "golden hour lighting, warm orange tones, long shadows",
        "DUSK": "magic hour, purple and orange sky, soft diffused light",
        "AFTERNOON": "harsh sunlight, high contrast, strong shadows",
        "MORNING": "soft morning light, gentle warmth"
    }
    lighting = lighting_styles.get(time_of_day.upper(), lighting_styles["DAY"])

    # Build mood modifiers
    mood_modifiers = {
        "tense": "dramatic lighting, high contrast, moody atmosphere",
        "romantic": "soft focus, warm tones, intimate lighting",
        "action": "dynamic angle, motion blur hints, intense",
        "sad": "muted colors, overcast, melancholic atmosphere",
        "happy": "bright, vibrant colors, warm sunlight",
        "mysterious": "fog, shadows, dramatic chiaroscuro",
        "peaceful": "serene, calm, gentle light"
    }
    mood_style = mood_modifiers.get(mood.lower(), "")

    # Platform-specific prompt construction
    style_tags = []
    negative_prompt = ""
    parameters = {}

    if platform in ["stable_diffusion", "midjourney", "dalle3"]:
        # Image generation platforms
        style_tags = [
            "cinematic",
            "professional photography",
            "8k resolution",
            "detailed",
            "photorealistic"
        ]

        negative_prompt = "cartoon, anime, illustration, painting, drawing, " \
                         "low quality, blurry, distorted, disfigured, " \
                         "bad anatomy, bad proportions, watermark, text"

        if platform == "midjourney":
            # Midjourney-specific formatting
            prompt_parts = [description]
            if char_descriptions:
                prompt_parts.append(", ".join(char_descriptions))
            prompt_parts.extend([location, lighting, mood_style, camera_angle])

            prompt = ", ".join(filter(None, prompt_parts))
            prompt += " --ar 16:9 --style raw --v 6"

            parameters = {
                "aspect_ratio": "16:9",
                "version": "6",
                "style": "raw"
            }

        elif platform == "dalle3":
            prompt_parts = [
                f"Cinematic {camera_angle} of",
                description
            ]
            if char_descriptions:
                prompt_parts.append("featuring " + " and ".join(char_descriptions))
            prompt_parts.extend([f"in {location}", lighting, mood_style])

            prompt = " ".join(filter(None, prompt_parts))

            parameters = {
                "quality": "hd",
                "size": "1792x1024"
            }

        else:  # stable_diffusion
            prompt_parts = [
                f"({camera_angle}:1.2)",
                description
            ]
            if char_descriptions:
                prompt_parts.append(", ".join(char_descriptions))
            prompt_parts.extend([location, f"({lighting}:1.1)", mood_style])
            prompt_parts.extend(style_tags)

            prompt = ", ".join(filter(None, prompt_parts))

            parameters = {
                "steps": 30,
                "cfg_scale": 7.5,
                "sampler": "DPM++ 2M Karras",
                "width": 1920,
                "height": 1080
            }

    elif platform in ["runway", "pika", "veo2", "sora"]:
        # Video generation platforms
        style_tags = [
            "cinematic",
            "professional film",
            "high quality",
            "smooth motion"
        ]

        negative_prompt = "glitchy, flickering, morphing, distorted, low quality"

        prompt_parts = [
            f"Cinematic {camera_angle}:",
            description
        ]
        if char_descriptions:
            prompt_parts.append(", ".join(char_descriptions))
        prompt_parts.extend([location, lighting, mood_style])

        prompt = " ".join(filter(None, prompt_parts))

        if platform == "runway":
            parameters = {
                "motion_amount": 5,
                "camera_motion": "smooth",
                "duration": 5
            }
        elif platform == "pika":
            parameters = {
                "aspect_ratio": "16:9",
                "fps": 24,
                "motion_strength": 0.7
            }
        elif platform == "veo2":
            parameters = {
                "duration": 8,
                "quality": "high",
                "style": "cinematic"
            }
        elif platform == "sora":
            parameters = {
                "duration": 10,
                "quality": "hd",
                "style": "cinematic"
            }

    else:
        # Default/generic platform
        prompt = f"{camera_angle}: {description}"
        if char_descriptions:
            prompt += f", featuring {', '.join(char_descriptions)}"
        prompt += f", {location}, {lighting}"

    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "style_tags": style_tags,
        "parameters": parameters,
        "platform": platform,
        "scene_context": {
            "location": location,
            "time_of_day": time_of_day,
            "mood": mood,
            "camera_angle": camera_angle
        },
        "characters_included": characters
    }


def get_character_dna(character_id: str) -> Optional[Dict]:
    """
    Retrieve Character DNA from database.

    Args:
        character_id: Character ID to retrieve

    Returns:
        Character DNA dict or None if not found
    """
    try:
        instance = spanner_client.instance(instance_id)
        database = instance.database(database_id)

        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                "SELECT visual_dna FROM Character WHERE character_id = @char_id",
                params={"char_id": character_id},
                param_types={"char_id": spanner.param_types.STRING}
            )

            for row in results:
                if row[0]:
                    return json.loads(row[0])

        return None

    except Exception as e:
        logger.error(f"Error retrieving character DNA: {e}")
        return None


def batch_create_character_dnas(characters: List[Dict]) -> List[Dict]:
    """
    Create Character DNA profiles for multiple characters.

    Args:
        characters: List of character dicts with name, description, age

    Returns:
        List of created Character DNA profiles
    """
    logger.info(f"Creating Character DNA for {len(characters)} characters")

    dnas = []
    for char in characters:
        try:
            dna = create_character_dna(
                name=char.get("name", "Unknown"),
                description=char.get("description", ""),
                age=char.get("age"),
                reference_images=char.get("reference_images")
            )
            dnas.append(dna)

            # Store in database
            store_character_dna(dna)

        except Exception as e:
            logger.error(f"Error creating DNA for {char.get('name')}: {e}")
            dnas.append({
                "error": str(e),
                "name": char.get("name")
            })

    return dnas


# Create the Visual Consistency Agent
visual_consistency = Agent(
    model="gemini-2.0-flash",
    instructions="""You are the Visual Consistency Agent for CineVibe film production.
    
    Your critical responsibilities:
    1. Create and maintain Character DNA profiles with exact visual specifications
    2. Generate consistent prompts that maintain character appearance across all content
    3. Validate all generated content against character DNA profiles
    4. Create scene-specific style guides for visual consistency
    5. Use Google Search to find visual references and inspiration
    
    Character DNA Management:
    - Every character must have a detailed DNA profile before any generation
    - Track physical attributes that NEVER change (eye color, facial structure)
    - Track variable attributes (clothing, aging, injuries) per scene
    - Maintain version history for any character updates
    
    Consistency Enforcement:
    - Review EVERY generated image/video for character accuracy
    - Reject any content with consistency score below 0.8
    - Provide specific feedback for regeneration
    - Track successful prompts for reuse
    
    Style Guide Creation:
    - Define visual style for each scene (lighting, color, mood)
    - Ensure continuity between connected scenes
    - Account for time of day and location changes
    - Maintain cinematic quality throughout
    
    Tools available:
    - create_character_dna(): Build detailed character profiles
    - validate_character_consistency(): Check generation accuracy
    - create_scene_style_guide(): Define scene visuals
    - generate_consistency_prompt(): Create optimized prompts
    - GoogleSearchTool(): Find visual references
    
    Remember: Visual consistency is CRITICAL for professional film production.
    One inconsistent frame can break audience immersion.
    """,
    tools=[
        Tool(create_character_dna),
        Tool(validate_character_consistency),
        Tool(create_scene_style_guide),
        Tool(generate_consistency_prompt),
        Tool(store_character_dna),
        Tool(maintain_scene_consistency),
        Tool(check_visual_continuity),
        Tool(generate_visual_prompt),
        Tool(get_character_dna),
        Tool(batch_create_character_dnas),
        GoogleSearchTool()
    ]
)