"""
Client for testing Generation Platform Agent
Tests multi-platform AI generation coordination
"""

import asyncio
import httpx
import json
from typing import Dict, Any

AGENT_URL = "http://localhost:8003"  # Generation Platform A2A server

async def test_storyboard_generation():
    """Test storyboard generation across platforms"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        print("Testing Generation Platform Agent")
        print("=" * 50)
        
        # Test 1: Generate storyboard with Stable Diffusion
        print("\n1. Testing storyboard generation (Stable Diffusion)...")
        generation_request = {
            "action": "generate_storyboard",
            "platform": "stable_diffusion",
            "scene": {
                "scene_id": "scene_001",
                "description": "A cozy coffee shop interior with warm lighting",
                "characters": ["SARAH"],
                "visual_prompt": "young woman sketching in notebook at coffee shop table, warm afternoon light, cozy atmosphere, artistic mood, photorealistic",
                "style_tags": ["warm", "cozy", "artistic", "natural lighting"]
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/generate",
            json=generation_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Storyboard generated successfully")
            print(f"   - Generation ID: {result.get('generation_id', 'Unknown')}")
            print(f"   - Platform: {result.get('platform', 'Unknown')}")
            print(f"   - Status: {result.get('status', 'Unknown')}")
            if 'url' in result:
                print(f"   - Asset URL: {result['url'][:50]}...")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Generate with Midjourney
        print("\n2. Testing storyboard generation (Midjourney)...")
        generation_request = {
            "action": "generate_storyboard",
            "platform": "midjourney",
            "scene": {
                "scene_id": "scene_002",
                "description": "Businessman entering coffee shop nervously",
                "characters": ["JAMES"],
                "visual_prompt": "professional man in business casual entering coffee shop, nervous expression, cinematic lighting, film still",
                "style_tags": ["cinematic", "professional", "nervous mood"]
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/generate",
            json=generation_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Storyboard queued for generation")
            print(f"   - Job ID: {result.get('job_id', 'Unknown')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 3: Generate video with Runway
        print("\n3. Testing video generation (Runway Gen-3)...")
        video_request = {
            "action": "generate_video",
            "platform": "runway",
            "scene": {
                "scene_id": "scene_003",
                "storyboard_url": "https://storage.example.com/storyboard_003.png",
                "motion_prompt": "camera slowly pans from left to right, character turns head to look at door",
                "duration": 5,
                "style": "cinematic, smooth motion"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/generate",
            json=video_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Video generation started")
            print(f"   - Job ID: {result.get('job_id', 'Unknown')}")
            print(f"   - Estimated time: {result.get('estimated_time', 'Unknown')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 4: Check generation status
        print("\n4. Testing status check...")
        status_request = {
            "action": "check_status",
            "job_id": "test_job_123",
            "platform": "runway"
        }
        
        response = await client.post(
            f"{AGENT_URL}/status",
            json=status_request
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"   ✓ Status retrieved")
            print(f"   - Status: {status.get('status', 'Unknown')}")
            print(f"   - Progress: {status.get('progress', 0)}%")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Generation Platform testing complete!")

async def test_batch_generation():
    """Test batch generation for multiple scenes"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        print("\nTesting Batch Generation")
        print("=" * 50)
        
        # Test batch storyboard generation
        print("\n1. Testing batch storyboard generation...")
        batch_request = {
            "action": "batch_generate",
            "type": "storyboard",
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "prompt": "coffee shop interior, warm lighting",
                    "platform": "stable_diffusion"
                },
                {
                    "scene_id": "scene_002",
                    "prompt": "two people talking at table",
                    "platform": "stable_diffusion"
                },
                {
                    "scene_id": "scene_003",
                    "prompt": "close-up of coffee cup",
                    "platform": "dalle3"
                }
            ]
        }
        
        response = await client.post(
            f"{AGENT_URL}/batch",
            json=batch_request
        )
        
        if response.status_code == 200:
            batch_result = response.json()
            print(f"   ✓ Batch generation initiated")
            print(f"   - Batch ID: {batch_result.get('batch_id', 'Unknown')}")
            print(f"   - Total scenes: {len(batch_result.get('jobs', []))}")
            print(f"   - Estimated completion: {batch_result.get('estimated_time', 'Unknown')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")

async def test_platform_selection():
    """Test intelligent platform selection"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\nTesting Platform Selection")
        print("=" * 50)
        
        # Test 1: Get recommended platform
        print("\n1. Testing platform recommendation...")
        recommendation_request = {
            "action": "recommend_platform",
            "requirements": {
                "type": "storyboard",
                "style": "photorealistic",
                "quality": "high",
                "speed": "medium",
                "budget": "moderate"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/recommend",
            json=recommendation_request
        )
        
        if response.status_code == 200:
            recommendation = response.json()
            print(f"   ✓ Platform recommendation received")
            print(f"   - Recommended: {recommendation.get('platform', 'Unknown')}")
            print(f"   - Reason: {recommendation.get('reason', 'Not specified')}")
            print(f"   - Alternatives: {', '.join(recommendation.get('alternatives', []))}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Compare platforms
        print("\n2. Testing platform comparison...")
        comparison_request = {
            "action": "compare_platforms",
            "platforms": ["runway", "pika", "stable_diffusion"],
            "criteria": ["quality", "speed", "cost", "features"]
        }
        
        response = await client.post(
            f"{AGENT_URL}/compare",
            json=comparison_request
        )
        
        if response.status_code == 200:
            comparison = response.json()
            print(f"   ✓ Platform comparison completed")
            for platform, scores in comparison.items():
                if isinstance(scores, dict):
                    print(f"   - {platform}: Quality={scores.get('quality', 0)}/10, "
                          f"Speed={scores.get('speed', 0)}/10, "
                          f"Cost={scores.get('cost', 0)}/10")
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
        
        # Test A2A message from Visual Consistency
        print("\n2. Testing A2A message from Visual Consistency...")
        a2a_message = {
            "from_agent": "visual_consistency",
            "to_agent": "generation_platform",
            "action": "generate_with_dna",
            "payload": {
                "scene_id": "scene_004",
                "character_dna": {
                    "name": "SARAH",
                    "physical_attributes": {
                        "hair_color": "brown",
                        "eye_color": "green",
                        "age": "28"
                    }
                },
                "prompt": "woman with brown hair and green eyes in coffee shop"
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
        
        # Test A2A broadcast
        print("\n3. Testing A2A broadcast...")
        broadcast_message = {
            "from_agent": "generation_platform",
            "action": "broadcast_status",
            "payload": {
                "platform_status": {
                    "runway": "operational",
                    "stable_diffusion": "operational",
                    "midjourney": "rate_limited",
                    "dalle3": "operational"
                }
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/a2a/broadcast",
            json=broadcast_message
        )
        
        if response.status_code == 200:
            print(f"   ✓ Broadcast sent successfully")
        else:
            print(f"   ✗ Broadcast failed: {response.status_code}")

async def main():
    """Main test runner"""
    
    print("\n🎥 CineVibe Generation Platform Client Test")
    print("=" * 50)
    print("\nMake sure the Generation Platform A2A server is running:")
    print("cd agents/generation_platform && python a2a_server.py\n")
    
    try:
        # Test storyboard generation
        await test_storyboard_generation()
        
        # Test batch generation
        await test_batch_generation()
        
        # Test platform selection
        await test_platform_selection()
        
        # Test A2A communication
        await test_a2a_communication()
        
    except httpx.ConnectError:
        print("\n❌ Could not connect to Generation Platform agent")
        print("Please ensure the A2A server is running on port 8003")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())