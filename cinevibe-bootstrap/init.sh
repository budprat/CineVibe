#!/bin/bash

# CineVibe Bootstrap Initialization Script
# Based on InstaVibe architecture for film production

set -e

echo "========================================="
echo "   CineVibe Bootstrap Initialization"
echo "========================================="
echo ""

# Check if running in Google Cloud Shell
if [ -z "$DEVSHELL_PROJECT_ID" ]; then
    echo "Warning: Not running in Google Cloud Shell"
    echo "Please ensure you have gcloud CLI configured"
fi

# Prompt for project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID cannot be empty"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Create .env file
cat > .env << EOF
PROJECT_ID=$PROJECT_ID
REGION=us-central1
SPANNER_INSTANCE_ID=cinevibe-graph-instance
SPANNER_DATABASE_ID=graphdb
ARTIFACT_REPO_NAME=cinevibe-agents
EOF

echo "✅ Created .env file with project configuration"

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv env
source env/bin/activate

# Install base requirements
echo "Installing Python dependencies..."
cat > requirements.txt << EOF
google-cloud-spanner==3.49.1
google-cloud-spanner-admin-database-v1==3.49.1
Flask==3.1.0
Flask-Cors==5.0.0
google-cloud-logging==3.11.3
google-cloud-aiplatform==1.73.0
httpx==0.28.1
httpx-sse==0.4.0
pydantic==2.10.6
uvicorn==0.34.0
python-socketio==5.12.1
jinja2==3.1.5
a2a-sdk>=0.2.6
fastapi==0.115.6
google-cloud-adk==0.1.0
EOF

pip install -r requirements.txt

echo "✅ Python environment setup complete"

# Create project structure documentation
cat > README.md << EOF
# CineVibe Bootstrap

AI-powered film production system using Google's ADK, A2A, and MCP protocols.

## Architecture

- **Script Analyzer Agent**: Parses screenplays and extracts narrative elements
- **Visual Consistency Agent**: Maintains character DNA and style consistency
- **Generation Platform Agent**: Interfaces with AI video/image generation platforms
- **Director Orchestrator**: Coordinates the entire production pipeline

## Setup

1. Run \`./init.sh\` to initialize the project
2. Run \`./set_env.sh\` to set environment variables
3. Deploy agents using deployment scripts

## Based on InstaVibe Architecture

This project adapts the InstaVibe multi-agent system for film production workflows.
EOF

echo "✅ Project structure created"

# Create set_env.sh script
cat > set_env.sh << EOF
#!/bin/bash
# Set environment variables for CineVibe

source .env

export PROJECT_ID=\$PROJECT_ID
export REGION=\$REGION
export SPANNER_INSTANCE_ID=\$SPANNER_INSTANCE_ID
export SPANNER_DATABASE_ID=\$SPANNER_DATABASE_ID
export ARTIFACT_REPO_NAME=\$ARTIFACT_REPO_NAME

# Service account
export SERVICE_ACCOUNT=\$(gcloud iam service-accounts list --format="value(email)" | grep compute@ | head -n 1)

echo "Environment variables set:"
echo "  PROJECT_ID: \$PROJECT_ID"
echo "  REGION: \$REGION"
echo "  SPANNER_INSTANCE_ID: \$SPANNER_INSTANCE_ID"
echo "  SERVICE_ACCOUNT: \$SERVICE_ACCOUNT"
EOF

chmod +x set_env.sh

echo ""
echo "========================================="
echo "   Initialization Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Run: source set_env.sh"
echo "2. Enable required APIs"
echo "3. Create Spanner instance"
echo "4. Deploy agents"