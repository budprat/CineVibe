"""
Client for testing Director Orchestrator Agent
Tests pipeline orchestration and agent coordination
"""

import asyncio
import httpx
import json
from typing import Dict, Any
import time

AGENT_URL = "http://localhost:8000"  # Director A2A server

async def test_pipeline_orchestration():
    """Test full production pipeline orchestration"""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        print("Testing Director Orchestrator Agent")
        print("=" * 50)
        
        # Test 1: Start new production
        print("\n1. Testing new production initialization...")
        
        # Sample script for testing
        test_script = """
        FADE IN:
        
        EXT. CITY PARK - DAY
        
        A beautiful sunny day. EMMA (25, energetic) jogs along the path.
        She stops at a bench where MICHAEL (27, contemplative) sits reading.
        
        EMMA
        Is this seat taken?
        
        MICHAEL
        (looking up, smiling)
        Not at all. Please, join me.
        
        Emma sits, catching her breath.
        
        EMMA
        Beautiful day for a run.
        
        MICHAEL
        Or for reading. Though your way seems healthier.
        
        They both laugh.
        
        FADE OUT.
        """
        
        production_request = {
            "action": "start_production",
            "project": {
                "title": "Park Encounter",
                "genre": "romantic drama",
                "script": test_script,
                "author": "Test Client",
                "settings": {
                    "quality": "high",
                    "style": "cinematic",
                    "target_runtime": 2  # minutes
                }
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/production/start",
            json=production_request
        )
        
        project_id = None
        if response.status_code == 200:
            result = response.json()
            project_id = result.get('project_id')
            print(f"   ✓ Production started successfully")
            print(f"   - Project ID: {project_id}")
            print(f"   - Status: {result.get('status', 'Unknown')}")
            print(f"   - Pipeline phases: {len(result.get('phases', []))}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
            return
        
        # Test 2: Check pipeline status
        print("\n2. Testing pipeline status check...")
        await asyncio.sleep(2)  # Wait for processing
        
        status_request = {
            "action": "get_status",
            "project_id": project_id
        }
        
        response = await client.post(
            f"{AGENT_URL}/production/status",
            json=status_request
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"   ✓ Status retrieved")
            print(f"   - Current phase: {status.get('current_phase', 'Unknown')}")
            print(f"   - Progress: {status.get('progress', 0)}%")
            print(f"   - Completed phases:")
            for phase in status.get('completed_phases', []):
                print(f"     • {phase}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 3: Trigger specific phase
        print("\n3. Testing manual phase trigger...")
        phase_request = {
            "action": "execute_phase",
            "project_id": project_id,
            "phase": "character_dna",
            "force": True  # Force execution even if already completed
        }
        
        response = await client.post(
            f"{AGENT_URL}/production/phase",
            json=phase_request
        )
        
        if response.status_code == 200:
            phase_result = response.json()
            print(f"   ✓ Phase executed")
            print(f"   - Phase: {phase_result.get('phase', 'Unknown')}")
            print(f"   - Duration: {phase_result.get('duration', 'Unknown')}s")
            print(f"   - Results: {phase_result.get('results_count', 0)} items")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Pipeline orchestration testing complete!")

async def test_agent_coordination():
    """Test multi-agent coordination"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        print("\nTesting Agent Coordination")
        print("=" * 50)
        
        # Test 1: Coordinate script analysis
        print("\n1. Testing script analysis coordination...")
        coordination_request = {
            "action": "coordinate",
            "task": "analyze_script",
            "agents": ["script_analyzer", "visual_consistency"],
            "data": {
                "script_content": "INT. OFFICE - DAY\n\nJOHN works at his desk.",
                "extract_characters": True,
                "create_dna": True
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/coordinate",
            json=coordination_request
        )
        
        if response.status_code == 200:
            coordination_result = response.json()
            print(f"   ✓ Coordination completed")
            print(f"   - Agents involved: {len(coordination_result.get('agents', []))}")
            print(f"   - Total duration: {coordination_result.get('duration', 'Unknown')}s")
            for agent, result in coordination_result.get('results', {}).items():
                print(f"   - {agent}: {result.get('status', 'Unknown')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Parallel agent execution
        print("\n2. Testing parallel agent execution...")
        parallel_request = {
            "action": "parallel_execute",
            "tasks": [
                {
                    "agent": "script_analyzer",
                    "action": "extract_scenes",
                    "data": {"script": "test script"}
                },
                {
                    "agent": "visual_consistency",
                    "action": "create_style_guide",
                    "data": {"genre": "drama"}
                },
                {
                    "agent": "generation_platform",
                    "action": "check_platform_status",
                    "data": {}
                }
            ]
        }
        
        response = await client.post(
            f"{AGENT_URL}/parallel",
            json=parallel_request
        )
        
        if response.status_code == 200:
            parallel_result = response.json()
            print(f"   ✓ Parallel execution completed")
            print(f"   - Tasks executed: {len(parallel_result.get('results', []))}")
            print(f"   - Success rate: {parallel_result.get('success_rate', 0)}%")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 3: Sequential workflow
        print("\n3. Testing sequential workflow...")
        workflow_request = {
            "action": "execute_workflow",
            "workflow": "scene_to_video",
            "steps": [
                {"agent": "script_analyzer", "action": "extract_scene"},
                {"agent": "visual_consistency", "action": "generate_prompt"},
                {"agent": "generation_platform", "action": "generate_storyboard"},
                {"agent": "generation_platform", "action": "generate_video"}
            ],
            "initial_data": {
                "scene_text": "A park bench conversation"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/workflow",
            json=workflow_request
        )
        
        if response.status_code == 200:
            workflow_result = response.json()
            print(f"   ✓ Workflow executed")
            print(f"   - Steps completed: {workflow_result.get('completed_steps', 0)}/{len(workflow_request['steps'])}")
            print(f"   - Final output: {workflow_result.get('output_type', 'Unknown')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")

async def test_monitoring():
    """Test production monitoring and metrics"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\nTesting Monitoring & Metrics")
        print("=" * 50)
        
        # Test 1: Get production metrics
        print("\n1. Testing metrics retrieval...")
        metrics_request = {
            "action": "get_metrics",
            "project_id": "test_project",
            "metrics": ["generation_count", "processing_time", "quality_scores"]
        }
        
        response = await client.post(
            f"{AGENT_URL}/metrics",
            json=metrics_request
        )
        
        if response.status_code == 200:
            metrics = response.json()
            print(f"   ✓ Metrics retrieved")
            print(f"   - Generations: {metrics.get('generation_count', 0)}")
            print(f"   - Avg processing time: {metrics.get('avg_processing_time', 0)}s")
            print(f"   - Quality score: {metrics.get('avg_quality_score', 0)}/10")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 2: Get agent health
        print("\n2. Testing agent health monitoring...")
        health_request = {
            "action": "check_agents_health"
        }
        
        response = await client.post(
            f"{AGENT_URL}/health/agents",
            json=health_request
        )
        
        if response.status_code == 200:
            health_status = response.json()
            print(f"   ✓ Agent health checked")
            for agent, status in health_status.items():
                if isinstance(status, dict):
                    print(f"   - {agent}: {status.get('status', 'Unknown')} "
                          f"(response time: {status.get('response_time', 'N/A')}ms)")
        else:
            print(f"   ✗ Failed: {response.status_code}")
        
        # Test 3: Get production logs
        print("\n3. Testing production logs...")
        logs_request = {
            "action": "get_logs",
            "project_id": "test_project",
            "limit": 5,
            "level": "INFO"
        }
        
        response = await client.post(
            f"{AGENT_URL}/logs",
            json=logs_request
        )
        
        if response.status_code == 200:
            logs = response.json()
            print(f"   ✓ Logs retrieved")
            print(f"   - Total entries: {len(logs.get('entries', []))}")
            for entry in logs.get('entries', [])[:3]:
                print(f"   - [{entry.get('timestamp', '')}] {entry.get('message', '')}")
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
            print(f"   ✓ Director is healthy")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
        
        # Test A2A agent registration
        print("\n2. Testing agent registration...")
        registration = {
            "action": "register_agent",
            "agent": {
                "name": "test_agent",
                "url": "http://localhost:9999",
                "capabilities": ["test", "debug"]
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/a2a/register",
            json=registration
        )
        
        if response.status_code == 200:
            print(f"   ✓ Agent registered successfully")
        else:
            print(f"   ✗ Registration failed: {response.status_code}")
        
        # Test A2A broadcast
        print("\n3. Testing director broadcast...")
        broadcast = {
            "action": "broadcast",
            "message": {
                "type": "production_update",
                "project_id": "test_project",
                "status": "processing",
                "phase": "storyboarding"
            }
        }
        
        response = await client.post(
            f"{AGENT_URL}/a2a/broadcast",
            json=broadcast
        )
        
        if response.status_code == 200:
            print(f"   ✓ Broadcast sent to all agents")
        else:
            print(f"   ✗ Broadcast failed: {response.status_code}")

async def main():
    """Main test runner"""
    
    print("\n🎬 CineVibe Director Orchestrator Client Test")
    print("=" * 50)
    print("\nMake sure the Director A2A server is running:")
    print("cd agents/director && python a2a_server.py")
    print("\nNote: Director requires other agents to be running for full functionality\n")
    
    try:
        # Test pipeline orchestration
        await test_pipeline_orchestration()
        
        # Test agent coordination
        await test_agent_coordination()
        
        # Test monitoring
        await test_monitoring()
        
        # Test A2A communication
        await test_a2a_communication()
        
        print("\n" + "=" * 50)
        print("✅ All Director tests completed!")
        print("\nFor full integration testing, ensure all agents are running:")
        print("  - Script Analyzer (port 8001)")
        print("  - Visual Consistency (port 8002)")
        print("  - Generation Platform (port 8003)")
        print("  - Director (port 8000)")
        
    except httpx.ConnectError:
        print("\n❌ Could not connect to Director agent")
        print("Please ensure the A2A server is running on port 8000")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())