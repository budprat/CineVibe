"""
Validation Schemas for CineVibe
Pydantic models for input validation across agents and A2A communication
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
import functools


# ============================================
# Enums
# ============================================

class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentType(str, Enum):
    """Type of content to generate"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class Platform(str, Enum):
    """AI generation platforms"""
    RUNWAY = "runway"
    PIKA = "pika"
    SORA = "sora"
    VEO2 = "veo2"
    MIDJOURNEY = "midjourney"
    STABLE_DIFFUSION = "stable_diffusion"
    NANO_BANANA = "nano_banana"


class QualityPriority(str, Enum):
    """Quality vs speed vs cost priority"""
    QUALITY = "quality"
    SPEED = "speed"
    COST = "cost"
    BALANCED = "balanced"


class ShotType(str, Enum):
    """Camera shot types"""
    ESTABLISHING = "establishing"
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    ACTION = "action"


class TimeOfDay(str, Enum):
    """Time of day for scenes"""
    DAY = "day"
    NIGHT = "night"
    DAWN = "dawn"
    DUSK = "dusk"
    AFTERNOON = "afternoon"
    MORNING = "morning"


# ============================================
# Base Models
# ============================================

class CineVibeBaseModel(BaseModel):
    """Base model with common configuration"""

    class Config:
        use_enum_values = True
        extra = "allow"  # Allow extra fields for flexibility


# ============================================
# Character Models
# ============================================

class PhysicalAttributes(CineVibeBaseModel):
    """Physical attributes for character DNA"""
    age: Optional[Union[int, str]] = Field(None, description="Character age")
    gender: Optional[str] = Field(None, description="Character gender")
    height: Optional[str] = Field("average", description="Height description")
    build: Optional[str] = Field("average", description="Body build")
    hair_color: Optional[str] = Field(None, description="Hair color")
    hair_style: Optional[str] = Field(None, description="Hair style")
    eye_color: Optional[str] = Field(None, description="Eye color")
    skin_tone: Optional[str] = Field(None, description="Skin tone")
    distinguishing_features: List[str] = Field(default_factory=list)


class StyleGuide(CineVibeBaseModel):
    """Visual style guide for character"""
    lighting: str = Field("cinematic, natural lighting")
    color_grading: str = Field("film-like, slightly desaturated")
    camera_angle: str = Field("eye-level, professional cinematography")
    quality_markers: List[str] = Field(
        default_factory=lambda: ["8k", "high quality", "detailed", "photorealistic"]
    )
    negative_prompts: List[str] = Field(
        default_factory=lambda: ["cartoon", "anime", "illustration", "low quality"]
    )


class CharacterDNAInput(CineVibeBaseModel):
    """Input for creating character DNA"""
    name: str = Field(..., min_length=1, max_length=100, description="Character name")
    description: str = Field(..., description="Character description")
    age: Optional[int] = Field(None, ge=0, le=150, description="Character age")
    reference_images: Optional[List[str]] = Field(None, description="Reference image URLs")

    @validator("name")
    def validate_name(cls, v):
        """Clean and validate character name"""
        return v.strip().upper()


class CharacterDNA(CineVibeBaseModel):
    """Complete character DNA profile"""
    character_id: str
    name: str
    physical_attributes: PhysicalAttributes
    original_description: str
    prompt_templates: Dict[str, str]
    style_guide: StyleGuide
    consistency_tokens: List[str]
    reference_images: List[str] = Field(default_factory=list)
    version: int = 1


# ============================================
# Scene Models
# ============================================

class SceneInput(CineVibeBaseModel):
    """Scene information from script analysis"""
    scene_number: int = Field(..., ge=1)
    scene_type: str = Field(..., description="INT/EXT")
    location: str = Field(..., min_length=1)
    time_of_day: TimeOfDay = Field(TimeOfDay.DAY)
    description: Optional[str] = None
    characters: List[str] = Field(default_factory=list)
    mood: Optional[str] = None


class SceneStyleGuide(CineVibeBaseModel):
    """Style guide for a specific scene"""
    scene_id: str
    lighting: str
    location_style: str
    color_palette: List[str]
    camera_guidelines: Dict[str, Any]
    mood: str
    consistency_markers: List[str]


# ============================================
# Script Analysis Models
# ============================================

class ExtractedCharacter(CineVibeBaseModel):
    """Character extracted from script"""
    name: str
    description: str
    age: Optional[int] = None
    first_appearance: Optional[int] = None


class ExtractedScene(CineVibeBaseModel):
    """Scene extracted from script"""
    scene_number: int
    type: str  # INT/EXT
    location: str
    time: str
    position: Optional[int] = None


class ExtractedDialogue(CineVibeBaseModel):
    """Dialogue extracted from script"""
    character: str
    direction: Optional[str] = None
    text: str


class ScriptAnalysisInput(CineVibeBaseModel):
    """Input for script analysis"""
    script_content: str = Field(..., min_length=10, description="Script text content")
    title: Optional[str] = Field(None, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    format: Optional[str] = Field("auto", description="Script format: auto, fountain, final_draft")

    @validator("script_content")
    def validate_script_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Script content cannot be empty")
        return v


class ScriptAnalysisOutput(CineVibeBaseModel):
    """Output from script analysis"""
    script_id: str
    title: str
    characters: List[ExtractedCharacter]
    scenes: List[ExtractedScene]
    dialogue: List[ExtractedDialogue]
    locations: List[str]
    props: List[str] = Field(default_factory=list)
    emotional_arc: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None


# ============================================
# Generation Models
# ============================================

class GenerationRequest(CineVibeBaseModel):
    """Request for content generation"""
    prompt: str = Field(..., min_length=1, max_length=4000)
    content_type: ContentType = Field(ContentType.IMAGE)
    platform: Optional[Platform] = Field(None, description="Specific platform or auto-select")
    duration: Optional[int] = Field(None, ge=1, le=60, description="Video duration in seconds")
    quality_priority: QualityPriority = Field(QualityPriority.BALANCED)
    character_dna: Optional[CharacterDNA] = None
    scene_style: Optional[SceneStyleGuide] = None
    negative_prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @root_validator
    def validate_duration_for_video(cls, values):
        if values.get("content_type") == ContentType.VIDEO and not values.get("duration"):
            values["duration"] = 5  # Default 5 seconds
        return values


class GenerationResult(CineVibeBaseModel):
    """Result from content generation"""
    job_id: str
    platform: Platform
    status: TaskStatus
    url: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    consistency_score: Optional[float] = Field(None, ge=0, le=1)
    cost: Optional[float] = Field(None, ge=0)
    generation_time_seconds: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# A2A Communication Models
# ============================================

class A2ATaskRequest(CineVibeBaseModel):
    """Request for A2A task execution"""
    type: str = Field(..., description="Task type identifier")
    input: Dict[str, Any] = Field(..., description="Task input data")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    sender: Optional[str] = Field(None, description="Sending agent name")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    timeout: Optional[float] = Field(60.0, ge=1, le=600, description="Task timeout in seconds")
    priority: Optional[str] = Field("normal", description="Task priority")

    @validator("type")
    def validate_task_type(cls, v):
        valid_types = {
            "analyze_script",
            "create_character_dna",
            "create_scene_style",
            "generate_content",
            "validate_consistency",
            "get_status",
            "start_production",
            "generate_storyboard",
            "generate_videos",
        }
        if v not in valid_types:
            # Allow custom types but log warning
            pass
        return v


class A2ATaskResponse(CineVibeBaseModel):
    """Response from A2A task execution"""
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    agent_name: Optional[str] = None


# ============================================
# Pipeline Models
# ============================================

class ProductionPhase(CineVibeBaseModel):
    """Phase in production pipeline"""
    phase: int
    name: str
    tasks: List[Dict[str, Any]]
    estimated_duration: int  # minutes
    status: TaskStatus = TaskStatus.PENDING


class ProductionPlan(CineVibeBaseModel):
    """Complete production plan"""
    project_id: str
    title: str
    phases: List[ProductionPhase]
    timeline: Dict[str, Any]
    estimated_costs: Dict[str, float]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Generic Task Input
# ============================================

class TaskInput(CineVibeBaseModel):
    """Generic task input that can contain various types"""
    script: Optional[str] = None
    script_content: Optional[str] = None
    character: Optional[CharacterDNAInput] = None
    scene: Optional[SceneInput] = None
    generation: Optional[GenerationRequest] = None
    production_id: Optional[str] = None
    project_id: Optional[str] = None

    # Additional flexible fields
    title: Optional[str] = None
    characters: Optional[List[Dict[str, Any]]] = None
    scenes: Optional[List[Dict[str, Any]]] = None


# ============================================
# Validation Decorator
# ============================================

def validate_input(model_class: type):
    """
    Decorator for validating function inputs with Pydantic models.

    Example:
        @validate_input(ScriptAnalysisInput)
        async def analyze_script(input_data: ScriptAnalysisInput):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Find the input argument
            if args:
                input_data = args[0]
            elif "input_data" in kwargs:
                input_data = kwargs["input_data"]
            elif "data" in kwargs:
                input_data = kwargs["data"]
            else:
                input_data = kwargs

            # Validate with Pydantic
            if isinstance(input_data, dict):
                validated = model_class(**input_data)
            elif isinstance(input_data, model_class):
                validated = input_data
            else:
                validated = model_class(**input_data.dict() if hasattr(input_data, 'dict') else input_data)

            # Replace input with validated model
            if args:
                args = (validated,) + args[1:]
            else:
                kwargs["input_data"] = validated

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if args:
                input_data = args[0]
            elif "input_data" in kwargs:
                input_data = kwargs["input_data"]
            elif "data" in kwargs:
                input_data = kwargs["data"]
            else:
                input_data = kwargs

            if isinstance(input_data, dict):
                validated = model_class(**input_data)
            elif isinstance(input_data, model_class):
                validated = input_data
            else:
                validated = model_class(**input_data.dict() if hasattr(input_data, 'dict') else input_data)

            if args:
                args = (validated,) + args[1:]
            else:
                kwargs["input_data"] = validated

            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
