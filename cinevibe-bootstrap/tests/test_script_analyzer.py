"""
Tests for Script Analyzer Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.script_analyzer.agent import (
    script_analyzer,
    extract_characters,
    extract_scenes,
    extract_dialogue,
    parse_script_elements
)


class TestScriptAnalyzer:
    """Test suite for Script Analyzer agent"""
    
    @pytest.fixture
    def sample_script(self):
        """Sample screenplay for testing"""
        return """
        FADE IN:
        
        INT. COFFEE SHOP - DAY
        
        SARAH (28), artistic type with long brown hair, sits at a corner table.
        
        JAMES (30), business casual, enters looking around.
        
        JAMES
        Is this seat taken?
        
        SARAH
        (smiling)
        No, please sit.
        
        FADE OUT.
        """
    
    @pytest.fixture
    def mock_spanner_client(self):
        """Mock Spanner client"""
        with patch('agents.script_analyzer.agent.spanner.Client') as mock:
            yield mock
    
    def test_extract_characters(self, sample_script):
        """Test character extraction from script"""
        characters = extract_characters(sample_script)
        
        assert len(characters) == 2
        assert any(c['name'] == 'SARAH' for c in characters)
        assert any(c['name'] == 'JAMES' for c in characters)
        
        sarah = next(c for c in characters if c['name'] == 'SARAH')
        assert '28' in sarah['description']
        assert 'artistic' in sarah['description'].lower()
    
    def test_extract_scenes(self, sample_script):
        """Test scene extraction from script"""
        scenes = extract_scenes(sample_script)
        
        assert len(scenes) >= 1
        assert scenes[0]['location'] == 'COFFEE SHOP'
        assert scenes[0]['time'] == 'DAY'
        assert scenes[0]['setting'] == 'INT'
    
    def test_extract_dialogue(self, sample_script):
        """Test dialogue extraction from script"""
        dialogue = extract_dialogue(sample_script)
        
        assert len(dialogue) == 2
        assert dialogue[0]['character'] == 'JAMES'
        assert 'seat taken' in dialogue[0]['text'].lower()
        assert dialogue[1]['character'] == 'SARAH'
    
    def test_parse_script_elements(self, sample_script):
        """Test complete script parsing"""
        elements = parse_script_elements(sample_script)
        
        assert 'characters' in elements
        assert 'scenes' in elements
        assert 'dialogue' in elements
        assert 'transitions' in elements
        
        assert len(elements['characters']) == 2
        assert len(elements['scenes']) >= 1
        assert len(elements['dialogue']) == 2
    
    @pytest.mark.asyncio
    async def test_script_analyzer_agent(self, sample_script):
        """Test the script analyzer agent with ADK"""
        # This would require mocking the ADK agent
        # For now, just verify the agent is properly configured
        
        assert script_analyzer is not None
        assert script_analyzer.model == "gemini-2.0-flash"
        assert len(script_analyzer.tools) > 0
    
    def test_empty_script(self):
        """Test handling of empty script"""
        empty_script = ""
        
        characters = extract_characters(empty_script)
        scenes = extract_scenes(empty_script)
        dialogue = extract_dialogue(empty_script)
        
        assert characters == []
        assert scenes == []
        assert dialogue == []
    
    def test_malformed_script(self):
        """Test handling of malformed script"""
        malformed = "This is not a proper screenplay format"
        
        # Should handle gracefully without crashing
        elements = parse_script_elements(malformed)
        
        assert elements is not None
        assert isinstance(elements, dict)
    
    @pytest.mark.asyncio
    async def test_database_storage(self, sample_script, mock_spanner_client):
        """Test storing script data in Spanner"""
        # Mock the database operations
        mock_instance = Mock()
        mock_database = Mock()
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_database
        
        # Test would verify database storage
        # Implementation depends on actual storage function
        pass


class TestScriptFormats:
    """Test different screenplay formats"""
    
    def test_fountain_format(self):
        """Test parsing Fountain format"""
        fountain_script = """
        Title: Test Script
        Author: Test Author
        
        = This is a synopsis
        
        INT. LOCATION - DAY
        
        CHARACTER
        Some dialogue here.
        """
        
        elements = parse_script_elements(fountain_script)
        assert elements is not None
    
    def test_final_draft_format(self):
        """Test parsing Final Draft format markers"""
        fd_script = """
        INT. LOCATION - DAY
        
                    CHARACTER
            Some centered dialogue.
        
        (MORE)
        
                    CHARACTER (CONT'D)
            Continued dialogue.
        """
        
        dialogue = extract_dialogue(fd_script)
        assert len(dialogue) >= 1
    
    def test_action_lines(self):
        """Test parsing action lines"""
        script_with_action = """
        INT. ROOM - DAY
        
        The room is dimly lit. A FIGURE moves in the shadows.
        
        FIGURE
        Who's there?
        
        The door SLAMS shut.
        """
        
        elements = parse_script_elements(script_with_action)
        assert 'action_lines' in elements or 'description' in elements


class TestCharacterAnalysis:
    """Test character analysis features"""
    
    def test_character_relationships(self):
        """Test extracting character relationships"""
        script = """
        INT. HOUSE - DAY
        
        MOTHER hugs her SON.
        
        MOTHER
        I love you, son.
        
        SON
        Love you too, mom.
        """
        
        characters = extract_characters(script)
        # Could analyze for family relationships
        assert len(characters) == 2
    
    def test_character_traits(self):
        """Test extracting character traits"""
        script = """
        JOHN (40s, gruff, tired detective with a drinking problem)
        """
        
        characters = extract_characters(script)
        if characters:
            john = characters[0]
            assert 'detective' in john.get('description', '').lower()
            assert '40s' in john.get('description', '')
    
    def test_character_arc_tracking(self):
        """Test tracking character development"""
        # This would be more complex in real implementation
        script_beginning = """
        INT. OFFICE - DAY
        JANE (shy, nervous) enters.
        """
        
        script_end = """
        INT. STAGE - NIGHT
        JANE (confident, commanding) addresses the crowd.
        """
        
        # Would track character state changes
        chars_begin = extract_characters(script_beginning)
        chars_end = extract_characters(script_end)
        
        assert len(chars_begin) == 1
        assert len(chars_end) == 1


@pytest.mark.integration
class TestScriptAnalyzerIntegration:
    """Integration tests for Script Analyzer"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, sample_script):
        """Test complete script analysis pipeline"""
        # Parse script
        elements = parse_script_elements(sample_script)
        
        # Verify all components extracted
        assert elements['characters']
        assert elements['scenes']
        assert elements['dialogue']
        
        # Verify data structure integrity
        for scene in elements['scenes']:
            assert 'location' in scene
            assert 'time' in scene
        
        for char in elements['characters']:
            assert 'name' in char
        
        for dial in elements['dialogue']:
            assert 'character' in dial
            assert 'text' in dial
    
    @pytest.mark.asyncio
    async def test_a2a_communication(self):
        """Test A2A server communication"""
        # Would test actual A2A server endpoints
        pass