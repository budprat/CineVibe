"""
Client for testing Visual Consistency Agent
Tests character DNA creation and consistency maintenance
"""

import asyncio
import httpx
import json
from typing import Dict, Any

AGENT_URL = "http://localhost:8002"  # Visual Consistency A2A server

async def test_character_dna():
    """Test character DNA creation and management"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("Testing Visual Consistency Agent")
        print("=" * 50)
        
        # Test 1: Create character DNA
        print("\n1. Testing character DNA creation...")
        character_data = {
            "action": "create_character_dna",
            "character": {
                "name": "SARAH",
                "description": "28 years old, artistic type, long brown hair",
                "age": 28,
                "gender": "female",
                "personality": "creative, introspective, friendly"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/character",
            json=character_data
        )
        
        sarah_dna = None
        if response.status_code == 200:
            sarah_dna = response.json()
            print(f"   ✓ Character DNA created for SARAH")
            print(f"   - DNA ID: {sarah_dna.get('dna_id', 'Unknown')}")
            print(f"   - Physical attributes: {len(sarah_dna.get('physical_attributes', {}))}")
            print(f"   - Style elements: {len(sarah_dna.get('style', {}))}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Create another character
        print("\n2. Creating second character DNA...")
        character_data = {
            "action": "create_character_dna",
            "character": {
                "name": "JAMES",
                "description": "30 years old, business professional, short dark hair",
                "age": 30,
                "gender": "male",
                "personality": "analytical, ambitious, reserved"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/character",
            json=character_data
        )
        
        if response.status_code == 200:
            james_dna = response.json()
            print(f"   ✓ Character DNA created for JAMES")
            print(f"   - DNA ID: {james_dna.get('dna_id', 'Unknown')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 3: Check consistency
        print("\n3. Testing visual consistency check...")
        consistency_check = {
            "action": "check_consistency",
            "scene": {
                "characters": ["SARAH", "JAMES"],
                "location": "coffee shop",
                "time": "day"
            },
            "previous_scenes": [
                {
                    "scene_id": "scene_001",
                    "characters": ["SARAH"],
                    "visual_elements": {
                        "SARAH": {
                            "clothing": "blue dress",
                            "hair_style": "ponytail"
                        }
                    }
                }
            ]
        }
        
        response = await client.post(
            f"{AGENT_URL}/consistency",
            json=consistency_check
        )
        
        if response.status_code == 200:
            consistency = response.json()
            print(f"   ✓ Consistency check completed")
            print(f"   - Consistency score: {consistency.get('score', 'Unknown')}")
            if 'recommendations' in consistency:
                print(f"   - Recommendations: {len(consistency['recommendations'])}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 4: Generate visual prompt
        print("\n4. Testing visual prompt generation...")
        prompt_request = {
            "action": "generate_prompt",
            "scene": {
                "description": "Sarah sits at a coffee shop table, sketching",
                "characters": ["SARAH"],
                "location": "INT. COFFEE SHOP",
                "time": "DAY"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/prompt",
            json=prompt_request
        )
        
        if response.status_code == 200:
            prompt_data = response.json()
            print(f"   ✓ Visual prompt generated")
            print(f"   - Prompt length: {len(prompt_data.get('prompt', ''))} characters")
            print(f"   - Style tags: {', '.join(prompt_data.get('style_tags', []))}")
            print(f"   - Negative prompt included: {bool(prompt_data.get('negative_prompt'))}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 5: Store visual asset
        print("\n5. Testing visual asset storage...")
        asset_data = {
            "action": "store_asset",
            "asset": {
                "scene_id": "scene_001",
                "character": "SARAH",
                "asset_type": "storyboard",
                "url": "https://storage.example.com/assets/scene_001_sarah.png",
                "metadata": {
                    "resolution": "1920x1080",
                    "format": "png",
                    "generated_at": "2025-01-01T12:00:00Z"
                }
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/asset",
            json=asset_data
        )
        
        if response.status_code == 200:
            print(f"   ✓ Visual asset stored successfully")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Visual Consistency testing complete!")

async def test_style_management():
    """Test style guide and visual reference management"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\nTesting Style Management")
        print("=" * 50)
        
        # Test 1: Create style guide
        print("\n1. Creating project style guide...")
        style_guide = {
            "action": "create_style_guide",
            "project_id": "project_001",
            "style": {
                "genre": "romantic comedy",
                "visual_tone": "warm and inviting",
                "color_palette": ["#F5E6D3", "#8B7355", "#D2691E", "#FFE4B5"],
                "lighting": "soft natural lighting",
                "camera_style": "handheld, intimate framing",
                "references": [
                    "500 Days of Summer",
                    "Before Sunrise",
                    "Lost in Translation"
                ]
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/style",
            json=style_guide
        )
        
        if response.status_code == 200:
            print(f"   ✓ Style guide created successfully")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Get style recommendations
        print("\n2. Getting style recommendations...")
        scene_request = {
            "action": "get_style_recommendations",
            "scene": {
                "mood": "romantic",
                "time": "sunset",
                "location": "rooftop"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/style/recommend",
            json=scene_request
        )
        
        if response.status_code == 200:
            recommendations = response.json()
            print(f"   ✓ Style recommendations received")
            print(f"   - Lighting: {recommendations.get('lighting', 'Not specified')}")
            print(f"   - Color tone: {recommendations.get('color_tone', 'Not specified')}")
            print(f"   - Camera angle: {recommendations.get('camera_angle', 'Not specified')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")

async def test_a2a_communication():
    """Test A2A protocol communication"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\nTesting A2A Communication")
        print("=" * 50)
        
        # Test health check
        print("\n1. Testing health check...")
        response = await client.get(f"{AGENT_URL}/health")
        
        if response.status_code == 200:
            print(f"   ✓ Agent is healthy")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
        
        # Test A2A message from Script Analyzer
        print("\n2. Testing A2A message from Script Analyzer...")
        a2a_message = {
            "from_agent": "script_analyzer",
            "to_agent": "visual_consistency",
            "action": "new_characters",
            "payload": {
                "characters": [
                    {"name": "ALICE", "description": "25, energetic, red hair"},
                    {"name": "BOB", "description": "35, serious, bald"}
                ]
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/a2a/message",
            json=a2a_message
        )
        
        if response.status_code == 200:
            print(f"   ✓ A2A message handled successfully")
        else:
            print(f"   ✗ A2A message failed: {response.status_code}")

async def main():
    """Main test runner"""
    
    print("\n🎨 CineVibe Visual Consistency Client Test")
    print("=" * 50)
    print("\nMake sure the Visual Consistency A2A server is running:")
    print("cd agents/visual_consistency && python a2a_server.py\n")
    
    try:
        # Test character DNA
        await test_character_dna()
        
        # Test style management
        await test_style_management()
        
        # Test A2A communication
        await test_a2a_communication()
        
    except httpx.ConnectError:
        print("\n❌ Could not connect to Visual Consistency agent")
        print("Please ensure the A2A server is running on port 8002")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())