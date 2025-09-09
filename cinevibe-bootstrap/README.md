# 🎬 CineVibe Bootstrap

**AI-Powered Film Production System** using Google's ADK, A2A Protocol, and Multi-Agent Orchestration

Transform screenplays into consistent, professional video content using a sophisticated multi-agent system that maintains character consistency, manages style guides, and orchestrates AI generation platforms.

## 🌟 Features

- **Script Analysis**: Automatic extraction of characters, scenes, and narrative elements
- **Character DNA**: Maintain perfect visual consistency across all generated content
- **Multi-Platform Generation**: Orchestrate Runway, Pika, Sora, Midjourney, and more
- **Professional Storyboarding**: Auto-generate shot lists and visual planning
- **Quality Assurance**: Automatic validation and regeneration for consistency
- **Production Pipeline**: Complete workflow from script to final video

## 🏗️ Architecture

Based on the InstaVibe multi-agent architecture, adapted for film production:

```
┌─────────────────┐
│   Web App       │
│   (Flask)       │
└────────┬────────┘
         │
┌────────▼────────┐
│    Director     │◄──── Orchestrator (A2A Client)
│  Orchestrator   │
└────────┬────────┘
         │ A2A Protocol
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼───┐ ┌────▼────┐ ┌───▼───┐
│Script │ │Visual│ │Generation│ │  MCP  │
│Analyzer│ │Cons. │ │Platform │ │Server │
└───┬───┘ └──┬───┘ └────┬────┘ └───┬───┘
    │        │          │           │
┌───▼────────▼──────────▼───────────▼───┐
│        Spanner Graph Database          │
│    (Characters, Scenes, Assets)        │
└────────────────────────────────────────┘
```

## 📋 Prerequisites

- Google Cloud Project with billing enabled
- Google Cloud Shell or local environment with `gcloud` CLI
- Python 3.12+
- Docker (for containerization)

## 🚀 Quick Start

### 1. Clone and Initialize

```bash
# Clone the repository
git clone <repository-url>
cd cinevibe-bootstrap

# Make scripts executable
chmod +x init.sh deploy.sh set_env.sh

# Initialize the project
./init.sh
# Enter your Google Cloud Project ID when prompted

# Set environment variables
source set_env.sh
```

### 2. Setup Database

```bash
# Create Spanner instance and database
python setup.py
```

This creates:
- Spanner instance: `cinevibe-graph-instance`
- Graph database with schema for characters, scenes, assets
- Sample data for testing

### 3. Deploy Services

```bash
# Deploy all agents and services
./deploy.sh
```

This deploys:
- MCP Server for AI platforms
- Script Analyzer Agent
- Visual Consistency Agent
- Generation Platform Agent
- Director Orchestrator
- CineVibe Web Application

### 4. Access the Application

After deployment, visit the URL shown in the deployment output to access CineVibe.

## 🎭 Agent Descriptions

### Script Analyzer Agent
- **Purpose**: Parse screenplays and extract narrative elements
- **Capabilities**: Character extraction, scene breakdown, dialogue analysis
- **Tools**: Regular expressions, NLP, Graph DB storage

### Visual Consistency Agent
- **Purpose**: Maintain character and style consistency
- **Capabilities**: Character DNA creation, style guide generation, consistency validation
- **Tools**: Google Search (references), prompt optimization

### Generation Platform Agent
- **Purpose**: Interface with AI generation platforms
- **Capabilities**: Platform selection, prompt formatting, quality validation
- **Tools**: MCP connection to Runway, Pika, Midjourney, etc.

### Director Orchestrator
- **Purpose**: Coordinate the entire production pipeline
- **Capabilities**: Task delegation, progress tracking, quality assurance
- **Protocol**: A2A for agent communication

## 🛠️ Development

### Local Testing

```bash
# Test individual agents
cd agents/script_analyzer
python agent.py

# Run ADK Dev UI
pip install google-cloud-adk
adk dev
```

### Adding New AI Platforms

Edit `tools/ai_platforms/mcp_server.py` to add new generation platforms:

```python
async def generate_with_new_platform(prompt, parameters):
    # Your platform integration
    pass
```

### Modifying Agents

Each agent follows the pattern:
1. `agent.py` - ADK agent definition
2. `a2a_server.py` - A2A protocol wrapper
3. `Dockerfile` - Container configuration

## 📊 Graph Database Queries

Example queries for the Spanner Graph Database:

```sql
-- Find all characters in a scene
GRAPH CineGraph
MATCH (c:Character)-[:AppearsIn]->(s:Scene)
WHERE s.scene_id = @scene_id
RETURN c.name, s.location

-- Track scene sequence
GRAPH CineGraph
MATCH (s1:Scene)-[:FollowedBy]->(s2:Scene)
RETURN s1.scene_number, s2.scene_number

-- Find character relationships
GRAPH CineGraph
MATCH (c1:Character)-[:RelatedTo]->(c2:Character)
RETURN c1.name, c2.name, relationship_type
```

## 🔧 Configuration

### Environment Variables

```bash
PROJECT_ID=your-project-id
REGION=us-central1
SPANNER_INSTANCE_ID=cinevibe-graph-instance
SPANNER_DATABASE_ID=graphdb
ARTIFACT_REPO_NAME=cinevibe-agents

# AI Platform API Keys (optional)
RUNWAY_API_KEY=your-runway-key
PIKA_API_KEY=your-pika-key
MIDJOURNEY_API_KEY=your-midjourney-key
```

### Cost Optimization

- Use Spanner with 100 processing units (minimum for development)
- Cloud Run scales to zero when not in use
- Consider using preemptible instances for batch generation

## 📈 Production Considerations

### Scaling

- **Horizontal**: Cloud Run auto-scales agents based on load
- **Vertical**: Increase Spanner processing units for larger databases
- **Caching**: Implement Redis for character DNA and style guides

### Security

- Enable VPC Service Controls
- Use Secret Manager for API keys
- Implement IAM roles for service accounts
- Enable audit logging

### Monitoring

- Cloud Trace for latency analysis
- Cloud Logging for agent communication
- Custom metrics for generation quality scores

## 🧪 Testing

### Unit Tests

```bash
# Run tests for individual agents
cd agents/script_analyzer
python -m pytest tests/
```

### Integration Tests

```bash
# Test A2A communication
python tests/test_a2a_communication.py

# Test MCP server
python tests/test_mcp_integration.py
```

### End-to-End Test

Upload the demo script through the web interface and verify:
1. Script analysis completes
2. Character DNA is created
3. Storyboards are generated
4. Consistency scores > 0.8

## 🚨 Troubleshooting

### Common Issues

1. **Spanner Permission Denied**
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="serviceAccount:$SERVICE_ACCOUNT" \
       --role="roles/spanner.databaseUser"
   ```

2. **MCP Server Connection Failed**
   - Check Cloud Run logs: `gcloud run logs read mcp-ai-platforms`
   - Verify environment variables are set

3. **Agent Registration Failed**
   - Ensure all agents are deployed and running
   - Check A2A endpoints are accessible

### Debug Mode

```bash
# Enable detailed logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Check agent cards
curl https://your-agent-url/agent-card
```

## 📚 Based On

This project adapts the **InstaVibe** multi-agent architecture tutorial for film production, demonstrating:
- ADK for agent development
- A2A protocol for agent communication
- MCP for tool integration
- Spanner Graph Database for relationship modeling
- Cloud Run for scalable deployment

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional AI platform integrations
- Advanced consistency algorithms
- Real-time collaboration features
- Export to editing software
- VR/AR preview capabilities

## 📄 License

Apache 2.0 - See LICENSE file

## 🙏 Acknowledgments

- Google ADK Team for the framework
- InstaVibe tutorial for the architecture pattern
- Open source AI generation communities

---

**Built with ❤️ for filmmakers embracing AI**

For questions or support, please open an issue or contact the maintainers.