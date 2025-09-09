#!/bin/bash

# CineVibe Deployment Script
# Deploys all agents and services to Google Cloud

set -e

echo "========================================="
echo "   CineVibe Deployment Script"
echo "========================================="
echo ""

# Load environment variables
source .env

# Check if required variables are set
if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID not set. Run: source set_env.sh"
    exit 1
fi

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable \
    spanner.googleapis.com \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    compute.googleapis.com \
    --project=$PROJECT_ID

# Create Artifact Registry repository
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create $ARTIFACT_REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID || echo "Repository already exists"

# Configure Docker authentication
echo "Configuring Docker authentication..."
gcloud auth configure-docker $REGION-docker.pkg.dev

# Deploy MCP Server
echo ""
echo "Deploying MCP Server for AI Platforms..."
cd tools/ai_platforms

cat > Dockerfile << EOF
FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn httpx pydantic
COPY mcp_server.py .
ENV PORT=8080
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/mcp-ai-platforms:latest
gcloud run deploy mcp-ai-platforms \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/mcp-ai-platforms:latest \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID"

export MCP_AI_PLATFORMS_URL=$(gcloud run services describe mcp-ai-platforms --region=$REGION --format='value(status.url)')
echo "MCP Server deployed at: $MCP_AI_PLATFORMS_URL"

cd ../..

# Deploy Script Analyzer Agent
echo ""
echo "Deploying Script Analyzer Agent..."
cd agents/script_analyzer
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/script-analyzer:latest
gcloud run deploy script-analyzer \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/script-analyzer:latest \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,SPANNER_INSTANCE_ID=$SPANNER_INSTANCE_ID,SPANNER_DATABASE_ID=$SPANNER_DATABASE_ID"

export SCRIPT_ANALYZER_URL=$(gcloud run services describe script-analyzer --region=$REGION --format='value(status.url)')
echo "Script Analyzer deployed at: $SCRIPT_ANALYZER_URL"

cd ../..

# Deploy Visual Consistency Agent
echo ""
echo "Deploying Visual Consistency Agent..."
cd agents/visual_consistency
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/visual-consistency:latest
gcloud run deploy visual-consistency \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/visual-consistency:latest \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,SPANNER_INSTANCE_ID=$SPANNER_INSTANCE_ID,SPANNER_DATABASE_ID=$SPANNER_DATABASE_ID"

export VISUAL_CONSISTENCY_URL=$(gcloud run services describe visual-consistency --region=$REGION --format='value(status.url)')
echo "Visual Consistency deployed at: $VISUAL_CONSISTENCY_URL"

cd ../..

# Deploy Generation Platform Agent
echo ""
echo "Deploying Generation Platform Agent..."
cd agents/generation_platform

cat > Dockerfile << EOF
FROM python:3.12-slim
WORKDIR /app
RUN pip install google-cloud-adk google-cloud-spanner a2a-sdk httpx
COPY agent.py .
COPY a2a_server.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV PORT=8080
CMD ["python", "a2a_server.py"]
EOF

cat > a2a_server.py << 'EOF'
# Minimal A2A server for Generation Platform
import os
from agent import generation_platform

if __name__ == "__main__":
    print("Generation Platform Agent starting on port 8080")
    # Simplified for deployment demo
    import uvicorn
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"agent": "Generation Platform", "status": "ready"}
    
    @app.get("/agent-card")
    def agent_card():
        return {
            "name": "Generation Platform",
            "description": "Interfaces with AI generation platforms",
            "capabilities": ["generate_video", "generate_image"]
        }
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/generation-platform:latest
gcloud run deploy generation-platform \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/generation-platform:latest \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,SPANNER_INSTANCE_ID=$SPANNER_INSTANCE_ID,MCP_AI_PLATFORMS_URL=$MCP_AI_PLATFORMS_URL"

export GENERATION_PLATFORM_URL=$(gcloud run services describe generation-platform --region=$REGION --format='value(status.url)')
echo "Generation Platform deployed at: $GENERATION_PLATFORM_URL"

cd ../..

# Deploy Director Orchestrator (simplified for demo)
echo ""
echo "Deploying Director Orchestrator..."
cd agents/director

cat > Dockerfile << EOF
FROM python:3.12-slim
WORKDIR /app
RUN pip install google-cloud-adk a2a-sdk httpx fastapi uvicorn
COPY agent.py .
ENV PORT=8080
ENV REMOTE_AGENT_ADDRESSES="$SCRIPT_ANALYZER_URL,$VISUAL_CONSISTENCY_URL,$GENERATION_PLATFORM_URL"
CMD ["python", "-c", "from agent import director; print('Director Agent ready')"]
EOF

gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/director:latest
gcloud run deploy director \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/director:latest \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,REMOTE_AGENT_ADDRESSES=$SCRIPT_ANALYZER_URL,$VISUAL_CONSISTENCY_URL,$GENERATION_PLATFORM_URL"

export DIRECTOR_URL=$(gcloud run services describe director --region=$REGION --format='value(status.url)')
echo "Director deployed at: $DIRECTOR_URL"

cd ../..

# Deploy CineVibe Web Application
echo ""
echo "Deploying CineVibe Web Application..."
cd cinevibe

cat > Dockerfile << EOF
FROM python:3.12-slim
WORKDIR /app
RUN pip install flask flask-cors google-cloud-spanner google-cloud-aiplatform httpx
COPY app.py .
COPY templates templates/
ENV PORT=8080
CMD ["python", "app.py"]
EOF

gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/cinevibe-app:latest
gcloud run deploy cinevibe-app \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO_NAME/cinevibe-app:latest \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,SPANNER_INSTANCE_ID=$SPANNER_INSTANCE_ID,SPANNER_DATABASE_ID=$SPANNER_DATABASE_ID,DIRECTOR_AGENT_URL=$DIRECTOR_URL"

export CINEVIBE_APP_URL=$(gcloud run services describe cinevibe-app --region=$REGION --format='value(status.url)')

cd ..

echo ""
echo "========================================="
echo "   Deployment Complete!"
echo "========================================="
echo ""
echo "Service URLs:"
echo "  CineVibe App: $CINEVIBE_APP_URL"
echo "  Director: $DIRECTOR_URL"
echo "  Script Analyzer: $SCRIPT_ANALYZER_URL"
echo "  Visual Consistency: $VISUAL_CONSISTENCY_URL"
echo "  Generation Platform: $GENERATION_PLATFORM_URL"
echo "  MCP Server: $MCP_AI_PLATFORMS_URL"
echo ""
echo "Visit $CINEVIBE_APP_URL to start using CineVibe!"