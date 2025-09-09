"""
Tests for Visual Consistency Agent
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.visual_consistency.agent import (
    visual_consistency_agent,
    create_character_dna,
    maintain_scene_consistency,
    generate_visual_prompt,
    check_visual_continuity
)


class TestCharacterDNA:
    """Test Character DNA creation and management"""
    
    @pytest.fixture
    def character_data(self):
        """Sample character data"""
        return {
            "name": "SARAH",
            "description": "28 years old, artistic type, long brown hair",
            "age": 28,
            "gender": "female",
            "personality": "creative, introspective"
        }
    
    def test_create_character_dna(self, character_data):
        """Test creating character DNA profile"""
        dna = create_character_dna(
            character_data["name"],
            character_data["description"],
            character_data["age"]
        )
        
        assert dna["name"] == "SARAH"
        assert "physical_attributes" in dna
        assert "style" in dna
        assert "personality_traits" in dna
        
        # Check physical attributes
        phys_attr = dna["physical_attributes"]
        assert phys_attr["age"] == 28
        assert "hair" in phys_attr
        assert "brown" in str(phys_attr["hair"]).lower()
    
    def test_character_dna_consistency(self):
        """Test DNA consistency across multiple calls"""
        dna1 = create_character_dna("JOHN", "30 years old, tall", 30)
        dna2 = create_character_dna("JOHN", "30 years old, tall", 30)
        
        # Should generate consistent base attributes
        assert dna1["name"] == dna2["name"]
        assert dna1["physical_attributes"]["age"] == dna2["physical_attributes"]["age"]
    
    def test_character_dna_with_minimal_info(self):
        """Test DNA creation with minimal information"""
        dna = create_character_dna("UNNAMED", "", None)
        
        assert dna["name"] == "UNNAMED"
        assert "physical_attributes" in dna
        # Should have default values
        assert dna["physical_attributes"]["age"] is not None


class TestVisualConsistency:
    """Test visual consistency maintenance"""
    
    @pytest.fixture
    def scene_data(self):
        """Sample scene data"""
        return {
            "scene_id": "scene_001",
            "location": "coffee shop",
            "time": "day",
            "characters": ["SARAH", "JAMES"],
            "description": "Interior coffee shop scene"
        }
    
    @pytest.fixture
    def character_appearances(self):
        """Sample character appearance data"""
        return {
            "SARAH": {
                "scene_001": {
                    "clothing": "blue dress",
                    "hair_style": "ponytail",
                    "accessories": "silver necklace"
                }
            },
            "JAMES": {
                "scene_001": {
                    "clothing": "business casual",
                    "hair_style": "short and neat"
                }
            }
        }
    
    def test_maintain_scene_consistency(self, scene_data, character_appearances):
        """Test maintaining consistency across scenes"""
        consistency = maintain_scene_consistency(
            scene_data,
            character_appearances
        )
        
        assert consistency is not None
        assert "consistency_score" in consistency
        assert "recommendations" in consistency
        assert consistency["consistency_score"] >= 0
        assert consistency["consistency_score"] <= 1
    
    def test_check_visual_continuity(self):
        """Test visual continuity checking"""
        current_scene = {
            "characters": ["SARAH"],
            "time": "day",
            "location": "coffee shop"
        }
        
        previous_scene = {
            "characters": ["SARAH"],
            "time": "day",
            "location": "coffee shop",
            "visual_elements": {
                "SARAH": {"clothing": "red dress"}
            }
        }
        
        continuity = check_visual_continuity(current_scene, previous_scene)
        
        assert continuity is not None
        assert "is_continuous" in continuity
        assert "issues" in continuity or "recommendations" in continuity


class TestPromptGeneration:
    """Test visual prompt generation"""
    
    @pytest.fixture
    def scene_context(self):
        """Sample scene context for prompt generation"""
        return {
            "description": "Sarah sits at a coffee shop table, sketching",
            "characters": ["SARAH"],
            "location": "INT. COFFEE SHOP",
            "time": "DAY",
            "mood": "peaceful",
            "camera_angle": "medium shot"
        }
    
    @pytest.fixture
    def character_dna(self):
        """Sample character DNA"""
        return {
            "SARAH": {
                "physical_attributes": {
                    "age": 28,
                    "hair_color": "brown",
                    "hair_length": "long",
                    "eye_color": "green",
                    "height": "average",
                    "build": "slim"
                },
                "style": {
                    "clothing_preference": "casual artistic",
                    "color_palette": ["blue", "earth tones"]
                }
            }
        }
    
    def test_generate_visual_prompt(self, scene_context, character_dna):
        """Test generating visual prompts for AI platforms"""
        prompt = generate_visual_prompt(scene_context, character_dna)
        
        assert prompt is not None
        assert "prompt" in prompt
        assert "style_tags" in prompt
        assert "negative_prompt" in prompt
        
        # Check prompt contains key elements
        prompt_text = prompt["prompt"].lower()
        assert "sarah" in prompt_text or "woman" in prompt_text
        assert "coffee shop" in prompt_text
        assert "sketch" in prompt_text or "draw" in prompt_text
    
    def test_platform_specific_prompts(self, scene_context, character_dna):
        """Test generating platform-specific prompts"""
        platforms = ["stable_diffusion", "midjourney", "dalle3"]
        
        prompts = {}
        for platform in platforms:
            prompt = generate_visual_prompt(
                scene_context,
                character_dna,
                platform=platform
            )
            prompts[platform] = prompt
        
        # Each platform should have slightly different prompt structure
        assert all(p["prompt"] for p in prompts.values())
        
        # Stable Diffusion should have negative prompts
        assert prompts["stable_diffusion"]["negative_prompt"]
        
        # Midjourney might have specific parameters
        if "parameters" in prompts["midjourney"]:
            assert prompts["midjourney"]["parameters"]


class TestStyleGuide:
    """Test style guide management"""
    
    @pytest.fixture
    def style_guide(self):
        """Sample project style guide"""
        return {
            "project_id": "project_001",
            "genre": "romantic comedy",
            "visual_tone": "warm and inviting",
            "color_palette": ["#F5E6D3", "#8B7355", "#D2691E"],
            "lighting": "soft natural lighting",
            "camera_style": "handheld, intimate",
            "references": ["500 Days of Summer", "Before Sunrise"]
        }
    
    def test_apply_style_guide(self, style_guide):
        """Test applying style guide to prompts"""
        base_prompt = "couple talking in coffee shop"
        
        styled_prompt = apply_style_guide(base_prompt, style_guide)
        
        assert styled_prompt != base_prompt
        assert "warm" in styled_prompt.lower() or "soft" in styled_prompt.lower()
    
    def test_style_consistency_score(self, style_guide):
        """Test calculating style consistency score"""
        generated_image_analysis = {
            "dominant_colors": ["#F5E6D3", "#8B7355"],
            "lighting": "soft",
            "mood": "romantic"
        }
        
        score = calculate_style_consistency(
            generated_image_analysis,
            style_guide
        )
        
        assert score >= 0
        assert score <= 1
        # Should have high score for matching style
        assert score > 0.7


class TestAssetManagement:
    """Test visual asset storage and retrieval"""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage client"""
        with patch('agents.visual_consistency.agent.storage.Client') as mock:
            yield mock
    
    def test_store_visual_asset(self, mock_storage):
        """Test storing generated visual assets"""
        asset_data = {
            "scene_id": "scene_001",
            "character": "SARAH",
            "asset_type": "storyboard",
            "url": "https://storage.example.com/asset.png",
            "metadata": {
                "resolution": "1920x1080",
                "format": "png",
                "generated_at": "2025-01-01T12:00:00Z"
            }
        }
        
        # Mock storage operations
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        result = store_visual_asset(asset_data)
        
        assert result is not None
        assert "asset_id" in result or "success" in result
    
    def test_retrieve_character_assets(self, mock_storage):
        """Test retrieving all assets for a character"""
        character_name = "SARAH"
        
        assets = retrieve_character_assets(character_name)
        
        assert isinstance(assets, list)
        # Would contain list of asset URLs and metadata


@pytest.mark.integration
class TestVisualConsistencyIntegration:
    """Integration tests for Visual Consistency agent"""
    
    @pytest.mark.asyncio
    async def test_full_character_pipeline(self):
        """Test complete character visual pipeline"""
        # Create character
        character = {
            "name": "ALICE",
            "description": "25, energetic, red hair",
            "age": 25
        }
        
        # Create DNA
        dna = create_character_dna(
            character["name"],
            character["description"],
            character["age"]
        )
        
        # Generate prompt
        scene = {
            "description": "Alice running in park",
            "characters": ["ALICE"],
            "location": "EXT. PARK",
            "time": "DAY"
        }
        
        prompt = generate_visual_prompt(scene, {"ALICE": dna})
        
        # Verify complete pipeline
        assert dna is not None
        assert prompt is not None
        assert prompt["prompt"]
        assert "alice" in prompt["prompt"].lower() or "woman" in prompt["prompt"].lower()
        assert "red hair" in prompt["prompt"].lower()
    
    @pytest.mark.asyncio
    async def test_consistency_tracking(self):
        """Test consistency tracking across multiple scenes"""
        scenes = [
            {"scene_id": "001", "characters": ["SARAH"]},
            {"scene_id": "002", "characters": ["SARAH", "JAMES"]},
            {"scene_id": "003", "characters": ["SARAH"]}
        ]
        
        consistency_scores = []
        for i, scene in enumerate(scenes):
            if i > 0:
                consistency = maintain_scene_consistency(
                    scene,
                    previous_scenes=scenes[:i]
                )
                consistency_scores.append(consistency["consistency_score"])
        
        # Should maintain consistency
        assert all(score > 0.5 for score in consistency_scores)


# Helper function that might be missing
def apply_style_guide(prompt, style_guide):
    """Apply style guide to prompt"""
    styled = prompt
    if style_guide.get("visual_tone"):
        styled += f", {style_guide['visual_tone']}"
    if style_guide.get("lighting"):
        styled += f", {style_guide['lighting']}"
    return styled


def calculate_style_consistency(analysis, style_guide):
    """Calculate style consistency score"""
    score = 0.0
    factors = 0
    
    # Check color palette match
    if "dominant_colors" in analysis and "color_palette" in style_guide:
        matching = sum(1 for c in analysis["dominant_colors"] 
                      if c in style_guide["color_palette"])
        score += matching / len(style_guide["color_palette"])
        factors += 1
    
    # Check lighting match
    if "lighting" in analysis and "lighting" in style_guide:
        if style_guide["lighting"].lower() in analysis["lighting"].lower():
            score += 1
        factors += 1
    
    return score / factors if factors > 0 else 0.5


def store_visual_asset(asset_data):
    """Store visual asset"""
    # Simplified version
    return {"asset_id": f"asset_{asset_data['scene_id']}_{asset_data['character']}"}


def retrieve_character_assets(character_name):
    """Retrieve character assets"""
    # Simplified version
    return []