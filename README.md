# 🎬 CineVibe - AI-Powered Film Production Platform

**Transform Screenplays into Professional Video Content with Multi-Agent AI Orchestration**

CineVibe is an innovative AI-powered film production system that uses Google's Agent Development Kit (ADK), Agent-to-Agent (A2A) Protocol, and Multi-Agent Orchestration to transform screenplays into consistent, professional video content. Built on the InstaVibe architecture pattern and extended for comprehensive film production workflows.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Security & Best Practices](#-security--best-practices)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Environment Configuration](#-environment-configuration)
- [Project Structure](#-project-structure)
- [Agent System](#-agent-system)
- [Development](#-development)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Features

### Core Capabilities
- **🎭 Intelligent Script Analysis**: Automatic extraction of characters, scenes, dialogue, and narrative elements
- **👤 Character DNA System**: Maintain perfect visual consistency across all generated content
- **🎨 Style Guide Management**: Consistent artistic direction throughout production
- **🎬 Professional Storyboarding**: Auto-generate shot lists, camera angles, and visual planning
- **🌐 Multi-Platform Generation**: Orchestrate Runway, Pika, Sora, Midjourney, Stable Diffusion, and more
- **✅ Quality Assurance**: Automatic validation and regeneration for consistency
- **📊 Real-time Pipeline Monitoring**: Track production progress with WebSocket updates
- **📈 Production Analytics**: Quality scores, completion metrics, and performance tracking

### Technical Features
- **Agent-to-Agent (A2A) Protocol**: Sophisticated inter-agent communication
- **Model Context Protocol (MCP)**: Standardized AI platform integration
- **Graph Database**: Spanner-based relationship modeling for characters, scenes, and assets
- **Scalable Architecture**: Cloud Run auto-scaling and serverless deployment
- **Real-time Updates**: WebSocket integration for live production monitoring

---

## 🏗️ Architecture

CineVibe uses a multi-agent architecture pattern with specialized AI agents coordinated by a central orchestrator:

```
┌─────────────────────────────────────────┐
│        CineVibe Web Application         │
│         (Flask + SocketIO)              │
│    Real-time Production Dashboard       │
└──────────────┬──────────────────────────┘
               │
               │ HTTP/WebSocket
               │
┌──────────────▼──────────────────────────┐
│       Director Orchestrator             │
│    (A2A Client + Coordinator)           │
│  - Task delegation                      │
│  - Progress tracking                    │
│  - Quality assurance                    │
└──────────────┬──────────────────────────┘
               │
               │ A2A Protocol
               │
    ┌──────────┴──────┬──────────┬─────────────┐
    │                 │          │             │
┌───▼───────┐  ┌─────▼─────┐  ┌─▼────────┐  ┌─▼────────┐
│  Script   │  │  Visual   │  │Generation│  │   MCP    │
│ Analyzer  │  │Consistency│  │ Platform │  │  Server  │
│  Agent    │  │   Agent   │  │  Agent   │  │ (Tools)  │
└───┬───────┘  └─────┬─────┘  └─┬────────┘  └─┬────────┘
    │                │           │              │
    │ Character      │ Style     │ Video        │ AI APIs
    │ Extraction     │ Guides    │ Generation   │ Integration
    │                │           │              │
    └────────────────┴───────────┴──────────────┘
                      │
         ┌────────────▼────────────────┐
         │  Spanner Graph Database     │
         │  - Characters               │
         │  - Scenes & Relationships   │
         │  - Generated Assets         │
         │  - Production Metadata      │
         └─────────────────────────────┘
```

### Agent Responsibilities

| Agent | Purpose | Key Capabilities |
|-------|---------|------------------|
| **Script Analyzer** | Parse screenplays and extract narrative elements | Character extraction, scene breakdown, dialogue analysis, plot structure identification |
| **Visual Consistency** | Maintain character and style consistency | Character DNA creation, style guide generation, visual validation, reference management |
| **Generation Platform** | Interface with AI generation platforms | Platform selection, prompt optimization, quality validation, retry logic |
| **Director Orchestrator** | Coordinate the entire production pipeline | Task delegation, progress tracking, quality assurance, agent communication |
| **MCP Server** | Provide tools for AI platform integration | API abstraction, rate limiting, error handling, response parsing |

---

## 🔒 Security & Best Practices

### Recent Security Improvements

This repository has undergone a comprehensive security audit and the following improvements have been implemented:

#### ✅ Secrets Management
- **All exposed secrets replaced with placeholders**
- **Environment variable configuration**: All sensitive credentials now use `.env` file
- **`.gitignore` protection**: Comprehensive exclusions prevent future secret exposure
- **Template file**: `.env.example` provides safe configuration template

#### 🔐 Protected Credentials

The following credentials have been secured and moved to environment variables:

1. **Google Maps API Key** → `GOOGLE_MAPS_API_KEY`
2. **Google Cloud Project ID** → `GOOGLE_CLOUD_PROJECT`
3. **Flask Secret Key** → `SECRET_KEY` (required, no fallback)
4. **Claude AI OAuth Tokens** → Managed by Claude CLI (not in .env)
5. **AI Platform API Keys** → Individual environment variables

#### 🛡️ Security Best Practices Implemented

- ✅ **No hardcoded secrets** in source code
- ✅ **Strong secret key requirement** for Flask sessions
- ✅ **Comprehensive .gitignore** excludes sensitive files
- ✅ **Environment variable separation** for dev/staging/production
- ✅ **API key restrictions** recommended in Google Cloud Console
- ✅ **Shell history sanitized** to remove exposed credentials
- ✅ **Documentation** for secure deployment practices

#### ⚠️ Security Checklist for Production

Before deploying to production, ensure:

- [ ] All API keys have been rotated and restricted (IP/referrer/API limits)
- [ ] `SECRET_KEY` is set to a strong, randomly generated value
- [ ] Google Secret Manager is used for production credentials
- [ ] IAM roles follow principle of least privilege
- [ ] VPC Service Controls are enabled
- [ ] Audit logging is configured
- [ ] `.env` file is NEVER committed to version control
- [ ] Pre-commit hooks prevent secret exposure (consider `detect-secrets`)

---

## 📋 Prerequisites

### Required
- **Google Cloud Project** with billing enabled
- **Google Cloud Shell** or local environment with `gcloud` CLI installed
- **Python 3.12+** (3.12 recommended)
- **Docker** for containerization
- **Node.js 18+** and npm (for frontend development)

### GCP Services Required
```bash
# These will be enabled during setup
- Cloud Run (serverless deployment)
- Cloud Functions (event-driven compute)
- Cloud Build (CI/CD)
- Artifact Registry (container storage)
- Cloud Spanner (graph database)
- API Keys (credentials management)
- IAM (access control)
- Compute Engine (infrastructure)
- Vertex AI Platform (AI/ML services)
- Cloud Resource Manager (project management)
- Maps Backend (Google Maps integration)
```

### API Keys (Optional, for AI Generation)
- Runway ML API key
- Pika Labs API key
- Midjourney API key
- Stability AI API key

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/budprat/CineVibe.git
cd CineVibe
```

### 2. Configure Environment Variables

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required environment variables:**
```bash
# Generate a strong secret key
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Add to .env:
SECRET_KEY=<generated-secret-key>
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### 3. Initialize the Project

```bash
cd cinevibe-bootstrap

# Make scripts executable
chmod +x init.sh deploy.sh set_env.sh

# Initialize GCP project and services
./init.sh
# Follow the prompts to enter your GCP project ID

# Load environment variables
source set_env.sh
```

### 4. Setup Database

```bash
# Create Spanner instance and database schema
cd cinevibe-bootstrap/cinevibe
python setup.py
```

This creates:
- Spanner instance: `cinevibe-graph-instance`
- Graph database: `graphdb`
- Complete schema for characters, scenes, assets, and relationships
- Sample data for testing (optional)

### 5. Deploy Services

```bash
# Deploy all agents and services to Cloud Run
cd cinevibe-bootstrap
./deploy.sh
```

This deploys:
- MCP Server (AI platform tools)
- Script Analyzer Agent
- Visual Consistency Agent
- Generation Platform Agent
- Director Orchestrator
- CineVibe Web Application

### 6. Access the Application

After successful deployment, the script will output the web application URL:

```
Service URL: https://cinevibe-<hash>-<region>.run.app
```

Visit this URL to access the CineVibe production dashboard.

---

## ⚙️ Environment Configuration

### Environment Variables Reference

Create a `.env` file in the root directory with the following variables:

```bash
# ==================================
# Flask Application Configuration
# ==================================
SECRET_KEY=your-64-char-hex-secret-key
FLASK_ENV=development
DEBUG=True
PORT=8080

# ==================================
# Google Cloud Platform
# ==================================
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
PROJECT_ID=your-gcp-project-id
REGION=us-central1

# ==================================
# Google Maps API
# ==================================
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# ==================================
# Spanner Database
# ==================================
SPANNER_INSTANCE_ID=cinevibe-graph-instance
SPANNER_DATABASE_ID=graphdb

# ==================================
# Agent URLs (after deployment)
# ==================================
DIRECTOR_AGENT_URL=http://localhost:8000
SCRIPT_ANALYZER_URL=http://localhost:8001
VISUAL_CONSISTENCY_URL=http://localhost:8002
GENERATION_PLATFORM_URL=http://localhost:8003

# ==================================
# AI Platform API Keys (Optional)
# ==================================
RUNWAY_API_KEY=your-runway-api-key
PIKA_API_KEY=your-pika-api-key
MIDJOURNEY_API_KEY=your-midjourney-api-key
STABILITY_AI_API_KEY=your-stability-ai-api-key

# ==================================
# Vertex AI Configuration
# ==================================
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# ==================================
# Artifact Registry
# ==================================
ARTIFACT_REPO_NAME=cinevibe-agents
```

### Generating Strong Secrets

```bash
# Generate SECRET_KEY for Flask
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Generate other random secrets if needed
openssl rand -hex 32
```

### Environment-Specific Configuration

Create separate environment files for different deployment stages:

```bash
.env.development   # Local development
.env.staging       # Staging environment
.env.production    # Production deployment
```

Load the appropriate file:
```bash
# Development
cp .env.development .env
source .env

# Production
cp .env.production .env
source .env
```

---

## 📁 Project Structure

```
CineVibe/
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusion rules (includes security protections)
├── README.md                    # This file
├── CLAUDE.md                    # Claude Code assistant instructions
├── mapkey.txt                   # Google Maps API key (placeholder)
├── project_id.txt               # GCP project ID (placeholder)
│
├── cinevibe-bootstrap/          # Main application directory
│   ├── README.md                # Detailed project documentation
│   ├── init.sh                  # GCP initialization script
│   ├── deploy.sh                # Deployment automation script
│   ├── set_env.sh               # Environment setup script
│   ├── requirements.txt         # Python dependencies
│   │
│   ├── cinevibe/                # Flask web application
│   │   ├── app.py               # Main Flask application (app.py:28 - secure SECRET_KEY)
│   │   ├── setup.py             # Database schema setup
│   │   ├── templates/           # HTML templates
│   │   │   ├── index.html       # Landing page
│   │   │   └── dashboard.html   # Production dashboard
│   │   ├── static/              # Static assets (CSS, JS, images)
│   │   └── Dockerfile           # Web app containerization
│   │
│   ├── agents/                  # AI Agent implementations
│   │   ├── director/            # Director Orchestrator Agent
│   │   │   ├── agent.py         # ADK agent definition
│   │   │   ├── a2a_server.py    # A2A protocol implementation
│   │   │   └── Dockerfile       # Container configuration
│   │   │
│   │   ├── script_analyzer/     # Script Analysis Agent
│   │   │   ├── agent.py         # Screenplay parsing logic
│   │   │   ├── a2a_server.py    # A2A server wrapper
│   │   │   └── Dockerfile
│   │   │
│   │   ├── visual_consistency/  # Visual Consistency Agent
│   │   │   ├── agent.py         # Character DNA & style guide logic
│   │   │   ├── a2a_server.py    # A2A server wrapper
│   │   │   └── Dockerfile
│   │   │
│   │   └── generation_platform/ # Generation Platform Agent
│   │       ├── agent.py         # AI platform orchestration
│   │       ├── a2a_server.py    # A2A server wrapper
│   │       └── Dockerfile
│   │
│   ├── tools/                   # MCP Server and Tools
│   │   ├── mcp_server.py        # Model Context Protocol server
│   │   ├── ai_platforms/        # AI platform integrations
│   │   │   ├── runway.py
│   │   │   ├── pika.py
│   │   │   ├── midjourney.py
│   │   │   └── stable_diffusion.py
│   │   └── Dockerfile
│   │
│   ├── database/                # Database schemas and migrations
│   │   ├── schema.sql           # Spanner graph schema
│   │   └── migrations/          # Schema migration scripts
│   │
│   ├── tests/                   # Test suites
│   │   ├── test_agents.py       # Agent unit tests
│   │   ├── test_a2a.py          # A2A protocol tests
│   │   ├── test_mcp.py          # MCP integration tests
│   │   └── test_integration.py  # End-to-end tests
│   │
│   └── utils/                   # Utility scripts
│       ├── remote_delete.py     # Cleanup script
│       └── helpers.py           # Common utilities
│
├── a2a-inspector/               # A2A Protocol debugging tool
│   ├── frontend/                # TypeScript frontend
│   │   ├── src/
│   │   └── package.json
│   ├── backend/                 # FastAPI backend
│   │   └── app.py
│   └── Dockerfile
│
└── .claude/                     # Claude AI configuration (excluded from git)
    └── .credentials.json        # OAuth tokens (placeholder)
```

---

## 🤖 Agent System

### Agent Communication Flow

1. **User uploads screenplay** via web interface
2. **Web app** sends to Director Orchestrator
3. **Director** delegates to Script Analyzer Agent
4. **Script Analyzer** parses screenplay, stores in Spanner
5. **Director** delegates to Visual Consistency Agent
6. **Visual Consistency** creates Character DNA profiles
7. **Director** delegates to Generation Platform Agent
8. **Generation Platform** uses MCP Server to call AI platforms
9. **Generated assets** stored in Spanner with quality scores
10. **Real-time updates** pushed to web interface via WebSocket

### Agent Development Kit (ADK) Integration

Each agent is built using Google's ADK framework:

```python
from google.cloud import adk

# Define agent
agent = adk.Agent(
    name="script_analyzer",
    description="Analyzes screenplays and extracts narrative elements",
    tools=[parse_screenplay, extract_characters, identify_scenes]
)

# A2A protocol wrapper
server = A2AServer(agent)
server.start()
```

### Inter-Agent Communication (A2A Protocol)

Agents communicate using the Agent-to-Agent protocol:

```python
# Director sends task to Script Analyzer
response = await a2a_client.send_task(
    agent="script_analyzer",
    task_type="analyze_screenplay",
    payload={
        "script_id": "script_abc123",
        "script_content": screenplay_text
    }
)
```

---

## 🛠️ Development

### Local Development Setup

```bash
# 1. Create Python virtual environment
cd cinevibe-bootstrap
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set environment variables
source set_env.sh

# 4. Run Flask application locally
cd cinevibe
python app.py
# Application runs on http://localhost:5000
```

### Running Individual Agents Locally

```bash
# Terminal 1: Script Analyzer Agent
cd agents/script_analyzer
python agent.py
# Agent runs on http://localhost:8001

# Terminal 2: Visual Consistency Agent
cd agents/visual_consistency
python agent.py
# Agent runs on http://localhost:8002

# Terminal 3: Generation Platform Agent
cd agents/generation_platform
python agent.py
# Agent runs on http://localhost:8003

# Terminal 4: Director Orchestrator
cd agents/director
python agent.py
# Agent runs on http://localhost:8000
```

### ADK Development UI

Google's ADK provides a development UI for testing agents:

```bash
pip install google-cloud-adk
adk dev
# Opens development UI on http://localhost:3000
```

### Adding New AI Platforms

To integrate a new AI generation platform:

1. **Create platform integration** in `tools/ai_platforms/`:

```python
# tools/ai_platforms/new_platform.py
async def generate_video(prompt: str, parameters: dict) -> dict:
    """Generate video using NewPlatform API"""
    api_key = os.environ.get("NEW_PLATFORM_API_KEY")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.newplatform.com/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": prompt, **parameters}
        )
        return response.json()
```

2. **Register in MCP Server** (`tools/mcp_server.py`):

```python
from ai_platforms import new_platform

@mcp_server.tool()
async def generate_with_new_platform(prompt: str, **kwargs):
    """MCP tool for NewPlatform"""
    return await new_platform.generate_video(prompt, kwargs)
```

3. **Add environment variable** to `.env.example`:

```bash
NEW_PLATFORM_API_KEY=your-new-platform-api-key
```

### Database Schema Modifications

To modify the Spanner graph schema:

```bash
# 1. Edit schema file
nano database/schema.sql

# 2. Create migration script
nano database/migrations/002_add_new_table.sql

# 3. Apply migration
gcloud spanner databases ddl update $SPANNER_DATABASE_ID \
    --instance=$SPANNER_INSTANCE_ID \
    --ddl-file=database/migrations/002_add_new_table.sql
```

---

## 🚀 Deployment

### Cloud Run Deployment

```bash
# Deploy all services
cd cinevibe-bootstrap
./deploy.sh

# Or deploy individual services
gcloud run deploy cinevibe-webapp \
    --source=./cinevibe \
    --region=us-central1 \
    --allow-unauthenticated \
    --set-env-vars="SPANNER_INSTANCE_ID=$SPANNER_INSTANCE_ID"
```

### Docker Build

```bash
# Build individual agent image
cd agents/script_analyzer
docker build -t script-analyzer:latest .

# Build all images
for agent in director script_analyzer visual_consistency generation_platform; do
    cd agents/$agent
    docker build -t cinevibe-$agent:latest .
    cd ../..
done
```

### Environment Configuration per Deployment

```bash
# Development
gcloud run deploy cinevibe-webapp \
    --set-env-vars="FLASK_ENV=development,DEBUG=True"

# Production
gcloud run deploy cinevibe-webapp \
    --set-env-vars="FLASK_ENV=production,DEBUG=False" \
    --min-instances=1 \
    --max-instances=10
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
cd cinevibe-bootstrap
python -m pytest tests/ -v

# Run specific agent tests
python -m pytest tests/test_agents.py::test_script_analyzer -v

# Run with coverage
python -m pytest tests/ --cov=cinevibe --cov-report=html
```

### Integration Tests

```bash
# Test A2A communication
python tests/test_a2a.py

# Test MCP server
python tests/test_mcp.py

# Test database operations
python tests/test_database.py
```

### End-to-End Test

```bash
# Upload demo screenplay and verify complete pipeline
cd cinevibe-bootstrap/tests
python test_integration.py --screenplay=demo_script.txt

# Expected results:
# ✓ Script uploaded successfully
# ✓ Characters extracted (5 found)
# ✓ Scenes identified (12 found)
# ✓ Character DNA created
# ✓ Storyboards generated
# ✓ Consistency scores > 0.8
```

### Manual Testing Checklist

- [ ] Upload screenplay via web interface
- [ ] Verify script analysis completes
- [ ] Check Character DNA profiles created
- [ ] Validate storyboard generation
- [ ] Test video generation with each platform
- [ ] Verify consistency validation works
- [ ] Check real-time WebSocket updates
- [ ] Test quality score calculation
- [ ] Verify database relationships correct

---

## 🔧 Troubleshooting

### Common Issues

#### 1. SECRET_KEY Environment Variable Not Set

**Error:**
```
ValueError: SECRET_KEY environment variable must be set
```

**Solution:**
```bash
# Generate a strong secret key
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Add to .env file
echo "SECRET_KEY=<generated-key>" >> .env

# Load environment variables
source .env
```

#### 2. Spanner Permission Denied

**Error:**
```
google.api_core.exceptions.PermissionDenied: 403 Permission denied on resource
```

**Solution:**
```bash
# Grant necessary IAM roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME" \
    --role="roles/spanner.databaseUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME" \
    --role="roles/spanner.databaseAdmin"
```

#### 3. MCP Server Connection Failed

**Error:**
```
ConnectionError: Failed to connect to MCP server
```

**Solution:**
```bash
# Check MCP server logs
gcloud run logs read mcp-tool-server --region=$REGION

# Verify MCP server is running
gcloud run services describe mcp-tool-server --region=$REGION

# Check environment variables are set
gcloud run services describe mcp-tool-server \
    --region=$REGION \
    --format="value(spec.template.spec.containers[0].env)"
```

#### 4. Agent Registration Failed

**Error:**
```
A2AError: Agent registration failed
```

**Solution:**
```bash
# Ensure all agents are deployed
gcloud run services list --region=$REGION

# Check agent health endpoints
curl https://script-analyzer-url/health
curl https://visual-consistency-url/health
curl https://generation-platform-url/health

# Verify A2A endpoints are accessible
curl https://director-url/agent-card
```

#### 5. Google Maps API Key Invalid

**Error:**
```
Google Maps API error: API key not valid
```

**Solution:**
```bash
# Verify API key is set correctly
echo $GOOGLE_MAPS_API_KEY

# Check API key restrictions in Google Cloud Console
# Navigate to: APIs & Services > Credentials
# Ensure Maps Backend API is enabled
gcloud services enable maps-backend.googleapis.com

# Test API key
curl "https://maps.googleapis.com/maps/api/geocode/json?address=Hollywood&key=$GOOGLE_MAPS_API_KEY"
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Set debug environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run application with debug logging
python app.py

# Check Cloud Run logs with filters
gcloud run logs read cinevibe-webapp \
    --region=$REGION \
    --filter="severity>=DEBUG" \
    --limit=100
```

### Health Checks

All services provide health endpoints:

```bash
# Check web application
curl https://your-webapp-url/health

# Check agent cards (A2A protocol)
curl https://your-agent-url/agent-card

# Check all services
for service in cinevibe-webapp director script-analyzer visual-consistency generation-platform mcp-tool-server; do
    echo "Checking $service..."
    gcloud run services describe $service --region=$REGION --format="value(status.url)"
done
```

---

## 🤝 Contributing

We welcome contributions to CineVibe! Here are areas where you can help:

### Priority Areas
- **AI Platform Integrations**: Add support for new video/image generation platforms
- **Consistency Algorithms**: Improve character DNA and style guide validation
- **Performance Optimization**: Enhance generation speed and quality
- **UI/UX Improvements**: Better production dashboard and real-time monitoring
- **Export Capabilities**: Integration with video editing software (Premiere, DaVinci Resolve)
- **VR/AR Preview**: 3D visualization and virtual production tools

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Ensure tests pass**: `pytest tests/ -v`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Style

- Follow PEP 8 for Python code
- Use type hints for function signatures
- Add docstrings to all functions and classes
- Write unit tests for new functionality
- Update documentation for significant changes

### Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

---

## 📊 Graph Database Queries

### Example Spanner Graph Queries

```sql
-- Find all characters in a specific scene
GRAPH CineGraph
MATCH (c:Character)-[:AppearsIn]->(s:Scene)
WHERE s.scene_id = @scene_id
RETURN c.character_id, c.name, c.age, s.location
ORDER BY c.name

-- Track scene sequence and flow
GRAPH CineGraph
MATCH (s1:Scene)-[:FollowedBy]->(s2:Scene)
WHERE s1.script_id = @script_id
RETURN s1.scene_number, s1.location, s2.scene_number, s2.location
ORDER BY s1.scene_number

-- Find character relationships and interactions
GRAPH CineGraph
MATCH (c1:Character)-[r:RelatedTo]->(c2:Character)
WHERE c1.script_id = @script_id
RETURN c1.name, r.relationship_type, c2.name

-- Find all generated assets for a project
GRAPH CineGraph
MATCH (s:Scene)<-[:GeneratedFor]-(a:Asset)
WHERE s.script_id = @script_id
RETURN s.scene_number, a.asset_type, a.platform, a.url, a.quality_score
ORDER BY s.scene_number, a.quality_score DESC

-- Character consistency analysis
GRAPH CineGraph
MATCH (c:Character)-[:HasDNA]->(dna:CharacterDNA)
WHERE c.script_id = @script_id
RETURN c.name, dna.visual_description, dna.consistency_score
ORDER BY dna.consistency_score DESC
```

---

## 📈 Production Considerations

### Scaling

**Horizontal Scaling:**
- Cloud Run automatically scales agents based on request load
- Configure `--max-instances` to control scaling limits
- Use `--min-instances=1` to reduce cold start latency

**Vertical Scaling:**
- Increase Spanner processing units for larger databases (start: 100, production: 1000+)
- Adjust Cloud Run CPU and memory allocation per service
- Implement connection pooling for database connections

**Caching:**
- Use Redis/Memorystore for Character DNA and style guides
- Cache generation results to avoid redundant API calls
- Implement CDN for static assets and generated videos

### Cost Optimization

```bash
# Development (low cost)
- Spanner: 100 processing units
- Cloud Run: Scale to zero when idle
- No min instances

# Production (optimized)
- Spanner: 1000 processing units with autoscaling
- Cloud Run: Min 1-2 instances for low latency
- Cloud CDN for asset delivery
- Cloud Storage lifecycle policies for old assets
```

### Monitoring & Observability

```bash
# Enable Cloud Trace for latency analysis
gcloud services enable cloudtrace.googleapis.com

# Enable Cloud Logging for agent communication
gcloud services enable logging.googleapis.com

# Create custom metrics for quality scores
gcloud monitoring metrics-descriptors create quality_score \
    --description="Video generation quality score" \
    --metric-kind=GAUGE

# Set up alerts
gcloud monitoring policies create \
    --notification-channels=$CHANNEL_ID \
    --display-name="High Error Rate Alert" \
    --condition-threshold-value=0.05
```

### Security Hardening

- **VPC Service Controls**: Isolate services within a security perimeter
- **Secret Manager**: Store all credentials in Google Secret Manager
- **IAM Best Practices**: Use service accounts with least privilege
- **Audit Logging**: Enable data access logs for Spanner
- **API Key Restrictions**: Restrict by IP address, HTTP referrer, and API methods
- **HTTPS Only**: Enforce TLS for all communications
- **Authentication**: Implement Identity-Aware Proxy (IAP) for production

---

## 📚 Based On & Technologies

### Core Technologies
- **Google Agent Development Kit (ADK)**: Agent framework and orchestration
- **Agent-to-Agent (A2A) Protocol**: Standardized inter-agent communication
- **Model Context Protocol (MCP)**: AI platform integration standard
- **Google Cloud Spanner**: Globally distributed graph database
- **Google Cloud Run**: Serverless container platform
- **Flask + SocketIO**: Web application and real-time communication

### AI Platforms Supported
- **Runway ML**: Video generation and editing
- **Pika Labs**: AI video creation
- **Midjourney**: Image generation
- **Stable Diffusion**: Open-source image generation
- **Google Vertex AI**: AI/ML infrastructure

### Inspired By
This project adapts the **InstaVibe** multi-agent architecture tutorial for film production, demonstrating best practices for:
- Multi-agent orchestration
- Graph database relationship modeling
- Scalable cloud-native deployment
- Real-time production monitoring

---

## 📄 License

Apache License 2.0

Copyright 2025 CineVibe Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

## 🙏 Acknowledgments

- **Google ADK Team** for the agent development framework
- **Google A2A Protocol Team** for standardized agent communication
- **InstaVibe Tutorial** for the multi-agent architecture pattern
- **Open Source AI Community** for platform integrations
- **Filmmakers and Content Creators** for feedback and testing

---

## 📞 Support & Contact

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Comprehensive guides in `/docs`
- **Email**: [Your contact email for support]

---

**Built with ❤️ for filmmakers embracing AI technology**

*Transform your screenplays into stunning visual content with CineVibe*

---

### Quick Links

- [Installation Guide](./cinevibe-bootstrap/README.md)
- [API Documentation](#)
- [Security Best Practices](#-security--best-practices)
- [Contributing Guidelines](#-contributing)
- [Changelog](#)
- [Roadmap](#)

---

**Last Updated**: November 4, 2025
**Version**: 1.0.0
**Status**: Active Development
