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
from typing import Dict, List, Optional, Tuple
import os
import base64

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
        GoogleSearchTool()
    ]
)