"""
Client for testing Script Analyzer Agent
Tests the agent's ability to parse scripts and extract data
"""

import asyncio
import httpx
import json
from typing import Dict, Any

AGENT_URL = "http://localhost:8001"  # Script Analyzer A2A server

async def test_script_analyzer():
    """Test script analyzer functionality"""
    
    # Sample screenplay content
    test_script = """
    FADE IN:
    
    EXT. COFFEE SHOP - DAY
    
    A cozy neighborhood coffee shop. SARAH (28, artistic type) sits at 
    a corner table, sketching in her notebook.
    
    JAMES (30, business casual) enters, looking around nervously.
    
    JAMES
    Excuse me, is this seat taken?
    
    SARAH
    (looking up, smiling)
    No, please, sit down.
    
    James sits, placing his laptop on the table.
    
    JAMES
    I'm James. I haven't seen you here before.
    
    SARAH
    Sarah. I just moved to the neighborhood.
    First time at this coffee shop actually.
    
    INT. COFFEE SHOP - CONTINUOUS
    
    The BARISTA (20s, cheerful) approaches their table.
    
    BARISTA
    What can I get you folks today?
    
    FADE OUT.
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("Testing Script Analyzer Agent")
        print("=" * 50)
        
        # Test 1: Parse script
        print("\n1. Testing script parsing...")
        response = await client.post(
            f"{AGENT_URL}/analyze",
            json={
                "action": "parse_script",
                "script_content": test_script
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Script parsed successfully")
            print(f"   - Characters found: {len(result.get('characters', []))}")
            print(f"   - Scenes found: {len(result.get('scenes', []))}")
            print(f"   - Dialogue blocks: {len(result.get('dialogue', []))}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Extract characters
        print("\n2. Testing character extraction...")
        response = await client.post(
            f"{AGENT_URL}/analyze",
            json={
                "action": "extract_characters",
                "script_content": test_script
            }
        )
        
        if response.status_code == 200:
            characters = response.json()
            print(f"   ✓ Characters extracted:")
            for char in characters:
                print(f"     - {char['name']}: {char.get('description', 'No description')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 3: Extract scenes
        print("\n3. Testing scene extraction...")
        response = await client.post(
            f"{AGENT_URL}/analyze",
            json={
                "action": "extract_scenes",
                "script_content": test_script
            }
        )
        
        if response.status_code == 200:
            scenes = response.json()
            print(f"   ✓ Scenes extracted:")
            for scene in scenes:
                print(f"     - {scene['heading']}")
                if 'characters' in scene:
                    print(f"       Characters: {', '.join(scene['characters'])}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 4: Generate scene breakdown
        print("\n4. Testing scene breakdown generation...")
        response = await client.post(
            f"{AGENT_URL}/analyze",
            json={
                "action": "generate_breakdown",
                "script_content": test_script
            }
        )
        
        if response.status_code == 200:
            breakdown = response.json()
            print(f"   ✓ Breakdown generated")
            print(f"   - Total pages: {breakdown.get('page_count', 'Unknown')}")
            print(f"   - Estimated runtime: {breakdown.get('runtime_minutes', 'Unknown')} minutes")
            print(f"   - Locations: {len(breakdown.get('locations', []))}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Script Analyzer testing complete!")

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
        
        # Test A2A message
        print("\n2. Testing A2A message handling...")
        a2a_message = {
            "from_agent": "test_client",
            "to_agent": "script_analyzer",
            "action": "ping",
            "payload": {"timestamp": "2025-01-01T00:00:00Z"}
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
    
    print("\n🎬 CineVibe Script Analyzer Client Test")
    print("=" * 50)
    print("\nMake sure the Script Analyzer A2A server is running:")
    print("cd agents/script_analyzer && python a2a_server.py\n")
    
    try:
        # Test script analysis
        await test_script_analyzer()
        
        # Test A2A communication
        await test_a2a_communication()
        
    except httpx.ConnectError:
        print("\n❌ Could not connect to Script Analyzer agent")
        print("Please ensure the A2A server is running on port 8001")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())