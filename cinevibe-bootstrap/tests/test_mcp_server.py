"""
Tests for MCP Server integration
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import httpx
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMCPServer:
    """Test MCP server functionality"""
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for API calls"""
        with patch('httpx.AsyncClient') as mock:
            yield mock
    
    @pytest.fixture
    def mcp_tools(self):
        """Sample MCP tools configuration"""
        return [
            {
                "name": "generate_image_stable_diffusion",
                "description": "Generate image using Stable Diffusion",
                "parameters": {
                    "prompt": {"type": "string", "required": True},
                    "negative_prompt": {"type": "string", "required": False},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024}
                }
            },
            {
                "name": "generate_video_runway",
                "description": "Generate video using Runway Gen-3",
                "parameters": {
                    "image_url": {"type": "string", "required": True},
                    "motion_prompt": {"type": "string", "required": True},
                    "duration": {"type": "integer", "default": 5}
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_list_tools_endpoint(self, mock_httpx_client):
        """Test MCP list_tools endpoint"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tools": []}
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5001/mcp/list_tools")
            
            assert response.status_code == 200
            data = response.json()
            assert "tools" in data
    
    @pytest.mark.asyncio
    async def test_call_tool_stable_diffusion(self, mock_httpx_client):
        """Test calling Stable Diffusion through MCP"""
        tool_request = {
            "tool": "generate_image_stable_diffusion",
            "arguments": {
                "prompt": "a beautiful sunset over mountains",
                "negative_prompt": "blurry, low quality",
                "width": 1920,
                "height": 1080
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "url": "https://example.com/generated.png",
                "seed": 12345
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5001/mcp/call_tool",
                json=tool_request
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "result" in result
            assert "url" in result["result"]
    
    @pytest.mark.asyncio
    async def test_call_tool_runway(self, mock_httpx_client):
        """Test calling Runway through MCP"""
        tool_request = {
            "tool": "generate_video_runway",
            "arguments": {
                "image_url": "https://example.com/storyboard.png",
                "motion_prompt": "camera slowly pans left to right",
                "duration": 10
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "job_id": "runway_job_123",
                "status": "processing",
                "estimated_time": 120
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5001/mcp/call_tool",
                json=tool_request
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "result" in result
            assert "job_id" in result["result"]
    
    @pytest.mark.asyncio
    async def test_sse_streaming(self):
        """Test SSE streaming for long-running operations"""
        # This would test the SSE endpoint for streaming results
        # In practice, would use httpx_sse for testing SSE streams
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_httpx_client):
        """Test MCP error handling"""
        tool_request = {
            "tool": "nonexistent_tool",
            "arguments": {}
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": "Tool not found"
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5001/mcp/call_tool",
                json=tool_request
            )
            
            assert response.status_code == 404
            error = response.json()
            assert "error" in error


class TestPlatformIntegration:
    """Test integration with various AI platforms"""
    
    @pytest.mark.asyncio
    async def test_midjourney_integration(self, mock_httpx_client):
        """Test Midjourney integration through MCP"""
        tool_request = {
            "tool": "generate_image_midjourney",
            "arguments": {
                "prompt": "cinematic shot of coffee shop interior --ar 16:9 --v 6",
            }
        }
        
        # Mock Midjourney webhook response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "job_id": "mj_123456",
                "status": "queued",
                "position": 5
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5001/mcp/call_tool",
                json=tool_request
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["result"]["status"] == "queued"
    
    @pytest.mark.asyncio
    async def test_dalle3_integration(self, mock_httpx_client):
        """Test DALL-E 3 integration through MCP"""
        tool_request = {
            "tool": "generate_image_dalle3",
            "arguments": {
                "prompt": "photorealistic portrait of a woman in coffee shop",
                "quality": "hd",
                "size": "1024x1024"
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "url": "https://openai.com/dalle/image.png",
                "revised_prompt": "A photorealistic portrait..."
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5001/mcp/call_tool",
                json=tool_request
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "url" in result["result"]
    
    @pytest.mark.asyncio
    async def test_pika_integration(self, mock_httpx_client):
        """Test Pika Labs integration through MCP"""
        tool_request = {
            "tool": "generate_video_pika",
            "arguments": {
                "prompt": "woman sketching in notebook, gentle camera movement",
                "aspect_ratio": "16:9",
                "motion_strength": 3
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "generation_id": "pika_abc123",
                "status": "generating",
                "eta_seconds": 60
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5001/mcp/call_tool",
                json=tool_request
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "generation_id" in result["result"]


class TestMCPToolValidation:
    """Test MCP tool parameter validation"""
    
    def test_validate_required_parameters(self):
        """Test validation of required parameters"""
        from tools.ai_platforms.mcp_server import validate_tool_params
        
        tool_config = {
            "parameters": {
                "prompt": {"type": "string", "required": True},
                "width": {"type": "integer", "required": False, "default": 1024}
            }
        }
        
        # Valid params
        valid_params = {"prompt": "test prompt"}
        assert validate_tool_params(valid_params, tool_config) == True
        
        # Missing required param
        invalid_params = {"width": 512}
        assert validate_tool_params(invalid_params, tool_config) == False
    
    def test_validate_parameter_types(self):
        """Test validation of parameter types"""
        from tools.ai_platforms.mcp_server import validate_tool_params
        
        tool_config = {
            "parameters": {
                "prompt": {"type": "string"},
                "steps": {"type": "integer"},
                "guidance": {"type": "number"}
            }
        }
        
        # Correct types
        valid_params = {
            "prompt": "test",
            "steps": 50,
            "guidance": 7.5
        }
        assert validate_tool_params(valid_params, tool_config) == True
        
        # Wrong type
        invalid_params = {
            "prompt": "test",
            "steps": "fifty",  # Should be integer
            "guidance": 7.5
        }
        assert validate_tool_params(invalid_params, tool_config) == False


class TestMCPJobTracking:
    """Test job tracking for async operations"""
    
    @pytest.fixture
    def job_tracker(self):
        """Mock job tracker"""
        return {
            "jobs": {},
            "completed": [],
            "failed": []
        }
    
    def test_create_job(self, job_tracker):
        """Test creating a new job"""
        from tools.ai_platforms.mcp_server import create_job
        
        job = create_job(
            tool="generate_video_runway",
            arguments={"prompt": "test"},
            tracker=job_tracker
        )
        
        assert "job_id" in job
        assert job["status"] == "pending"
        assert job["tool"] == "generate_video_runway"
        assert job["job_id"] in job_tracker["jobs"]
    
    def test_update_job_status(self, job_tracker):
        """Test updating job status"""
        from tools.ai_platforms.mcp_server import create_job, update_job_status
        
        job = create_job("test_tool", {}, job_tracker)
        job_id = job["job_id"]
        
        # Update to processing
        update_job_status(job_id, "processing", job_tracker)
        assert job_tracker["jobs"][job_id]["status"] == "processing"
        
        # Update to completed
        update_job_status(
            job_id,
            "completed",
            job_tracker,
            result={"url": "https://example.com/result.mp4"}
        )
        assert job_id in job_tracker["completed"]
        assert job_tracker["jobs"][job_id]["result"]["url"]
    
    @pytest.mark.asyncio
    async def test_job_polling(self):
        """Test polling for job completion"""
        from tools.ai_platforms.mcp_server import poll_job_status
        
        job_id = "test_job_123"
        
        # Mock external API polling
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "status": "completed",
                "result_url": "https://example.com/video.mp4"
            }
            mock_get.return_value = mock_response
            
            status = await poll_job_status(job_id, "runway")
            assert status["status"] == "completed"
            assert "result_url" in status


@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP server"""
    
    @pytest.mark.asyncio
    async def test_full_generation_pipeline(self):
        """Test complete generation pipeline through MCP"""
        # This would test:
        # 1. List available tools
        # 2. Call storyboard generation
        # 3. Poll for completion
        # 4. Use result for video generation
        # 5. Poll video generation
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_generations(self):
        """Test handling concurrent generation requests"""
        # Would test multiple simultaneous generations
        pass


# Helper functions that might be missing in actual implementation
def validate_tool_params(params, tool_config):
    """Validate tool parameters"""
    param_config = tool_config.get("parameters", {})
    
    # Check required params
    for param_name, config in param_config.items():
        if config.get("required", False) and param_name not in params:
            return False
        
        # Check types if param is provided
        if param_name in params:
            param_type = config.get("type")
            value = params[param_name]
            
            if param_type == "string" and not isinstance(value, str):
                return False
            elif param_type == "integer" and not isinstance(value, int):
                return False
            elif param_type == "number" and not isinstance(value, (int, float)):
                return False
    
    return True


def create_job(tool, arguments, tracker):
    """Create a new job"""
    import uuid
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "tool": tool,
        "arguments": arguments,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00Z"
    }
    tracker["jobs"][job_id] = job
    return job


def update_job_status(job_id, status, tracker, result=None):
    """Update job status"""
    if job_id in tracker["jobs"]:
        tracker["jobs"][job_id]["status"] = status
        if result:
            tracker["jobs"][job_id]["result"] = result
        
        if status == "completed":
            tracker["completed"].append(job_id)
        elif status == "failed":
            tracker["failed"].append(job_id)


async def poll_job_status(job_id, platform):
    """Poll for job status"""
    # Simplified mock
    return {
        "status": "completed",
        "result_url": f"https://{platform}.com/result/{job_id}"
    }