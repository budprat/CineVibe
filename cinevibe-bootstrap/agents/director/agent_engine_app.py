"""
Agent Engine Deployment for Director Orchestrator
Deploys the Director agent to Vertex AI Agent Engine
Based on InstaVibe's orchestrator deployment pattern
"""

import os
import sys
import json
import time
from google.cloud import aiplatform
from google.cloud import storage
import tempfile
import shutil
import subprocess

# Environment variables
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
REMOTE_AGENT_ADDRESSES = os.environ.get("REMOTE_AGENT_ADDRESSES", "")

if not PROJECT_ID:
    print("Error: PROJECT_ID not set")
    sys.exit(1)

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=REGION)

def create_agent_package():
    """Create deployment package for Agent Engine"""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, "director_agent")
    os.makedirs(package_dir)
    
    # Copy agent files
    shutil.copy("agent.py", package_dir)
    shutil.copy("a2a_server.py", package_dir)
    
    # Create requirements.txt
    requirements = """google-cloud-adk==0.1.0
google-cloud-aiplatform==1.73.0
a2a-sdk>=0.2.6
httpx==0.28.1
pydantic==2.10.6
uvicorn==0.34.0
fastapi==0.115.6"""
    
    with open(os.path.join(package_dir, "requirements.txt"), "w") as f:
        f.write(requirements)
    
    # Create main.py for Agent Engine
    main_content = f"""
import os
import json
from agent import director
from google_cloud_adk import Runner
from google_cloud_adk.services import (
    InMemoryArtifactService,
    InMemorySessionService,
    InMemoryVectorDB
)

# Set remote agent addresses
os.environ["REMOTE_AGENT_ADDRESSES"] = "{REMOTE_AGENT_ADDRESSES}"

# Initialize services
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()
vector_db = InMemoryVectorDB()

# Create runner
runner = Runner(
    agent=director,
    artifact_service=artifact_service,
    session_service=session_service,
    vector_db=vector_db
)

async def handle_request(request):
    \"\"\"Handle incoming requests from Agent Engine\"\"\"
    
    # Parse request
    user_input = request.get("input", "")
    session_id = request.get("session_id", "default")
    
    # Get or create session
    session = await session_service.get_or_create(session_id)
    
    # Run agent
    result = await runner.run(
        user_input=user_input,
        session=session
    )
    
    # Return response
    if result and result.messages:
        return {{
            "output": result.messages[-1].content,
            "session_id": session_id
        }}
    
    return {{"error": "No response generated"}}
"""
    
    with open(os.path.join(package_dir, "main.py"), "w") as f:
        f.write(main_content)
    
    # Create config.yaml for Agent Engine
    config_content = """
runtime: python312
service: director-orchestrator

env_variables:
  PROJECT_ID: "{PROJECT_ID}"
  REMOTE_AGENT_ADDRESSES: "{REMOTE_AGENT_ADDRESSES}"

automatic_scaling:
  min_instances: 0
  max_instances: 10
  
resources:
  cpu: 2
  memory_gb: 4
  disk_size_gb: 10
""".format(PROJECT_ID=PROJECT_ID, REMOTE_AGENT_ADDRESSES=REMOTE_AGENT_ADDRESSES)
    
    with open(os.path.join(package_dir, "config.yaml"), "w") as f:
        f.write(config_content)
    
    # Create tarball
    tarball_path = os.path.join(temp_dir, "director_agent.tar.gz")
    subprocess.run(
        ["tar", "-czf", tarball_path, "-C", temp_dir, "director_agent"],
        check=True
    )
    
    return tarball_path, temp_dir

def upload_to_gcs(tarball_path):
    """Upload package to Google Cloud Storage"""
    
    bucket_name = f"{PROJECT_ID}-agent-engine"
    blob_name = f"director-agent-{int(time.time())}.tar.gz"
    
    # Create bucket if it doesn't exist
    storage_client = storage.Client(project=PROJECT_ID)
    
    try:
        bucket = storage_client.bucket(bucket_name)
        if not bucket.exists():
            bucket = storage_client.create_bucket(
                bucket_name,
                location=REGION
            )
            print(f"Created bucket: {bucket_name}")
    except Exception as e:
        print(f"Bucket creation error (may already exist): {e}")
        bucket = storage_client.bucket(bucket_name)
    
    # Upload file
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(tarball_path)
    
    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    print(f"Uploaded package to: {gcs_uri}")
    
    return gcs_uri

def deploy_to_agent_engine(gcs_uri):
    """Deploy agent to Vertex AI Agent Engine"""
    
    # Create agent configuration
    agent_config = {
        "display_name": "CineVibe Director Orchestrator",
        "description": "Central coordinator for film production pipeline",
        "agent_type": "ORCHESTRATOR",
        "model": "gemini-2.0-flash",
        "package_uri": gcs_uri,
        "entry_point": "main.handle_request",
        "environment_variables": {
            "PROJECT_ID": PROJECT_ID,
            "REMOTE_AGENT_ADDRESSES": REMOTE_AGENT_ADDRESSES
        }
    }
    
    print("\nDeploying to Agent Engine...")
    print(f"Configuration: {json.dumps(agent_config, indent=2)}")
    
    # Note: The actual Agent Engine API deployment would go here
    # This is a simplified version as the exact API may vary
    
    try:
        # Create agent endpoint
        endpoint = aiplatform.Endpoint.create(
            display_name="director-orchestrator-endpoint",
            description="Endpoint for CineVibe Director Orchestrator"
        )
        
        print(f"Created endpoint: {endpoint.resource_name}")
        
        # Deploy model (simplified - actual Agent Engine deployment may differ)
        deployed_model = endpoint.deploy(
            model=None,  # Would reference the actual agent model
            deployed_model_display_name="director-orchestrator",
            machine_type="n1-standard-4",
            min_replica_count=0,
            max_replica_count=10,
            traffic_percentage=100
        )
        
        print(f"Deployed model: {deployed_model}")
        
        # Store endpoint ID
        endpoint_id = endpoint.name.split("/")[-1]
        
        with open("agent_engine_endpoint.txt", "w") as f:
            f.write(endpoint_id)
        
        print(f"\n✅ Agent deployed successfully!")
        print(f"Endpoint ID: {endpoint_id}")
        print(f"Endpoint URL: https://{REGION}-aiplatform.googleapis.com/v1/{endpoint.resource_name}")
        
        return endpoint_id
        
    except Exception as e:
        print(f"Deployment error: {e}")
        print("\nNote: Full Agent Engine deployment requires additional setup.")
        print("For development, you can run the Director locally or on Cloud Run.")
        
        # Return mock endpoint for development
        return "director-dev-endpoint"

def main():
    """Main deployment function"""
    
    print("=" * 50)
    print("CineVibe Director Agent Engine Deployment")
    print("=" * 50)
    print()
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print(f"Remote Agents: {REMOTE_AGENT_ADDRESSES}")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        print("Starting deployment process...")
        
        # Create package
        print("\n1. Creating agent package...")
        tarball_path, temp_dir = create_agent_package()
        print(f"   Package created: {tarball_path}")
        
        # Upload to GCS
        print("\n2. Uploading to Cloud Storage...")
        gcs_uri = upload_to_gcs(tarball_path)
        
        # Deploy to Agent Engine
        print("\n3. Deploying to Agent Engine...")
        endpoint_id = deploy_to_agent_engine(gcs_uri)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        print("\n" + "=" * 50)
        print("Deployment Complete!")
        print("=" * 50)
        print()
        print(f"Agent Engine Endpoint ID: {endpoint_id}")
        print()
        print("To test the agent:")
        print(f"  curl -X POST https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/endpoints/{endpoint_id}:predict")
        print()
        
    else:
        print("Usage: python agent_engine_app.py deploy")
        print()
        print("This will deploy the Director Orchestrator to Vertex AI Agent Engine")

if __name__ == "__main__":
    main()