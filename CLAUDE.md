# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

This is a Google Cloud Shell environment with multiple projects. The main projects are:

### a2a-inspector
A web-based tool for inspecting and debugging servers that implement the Google A2A (Agent-to-Agent) protocol.

**Tech Stack:**
- Backend: FastAPI (Python 3.12+)
- Frontend: TypeScript with esbuild
- Package Management: uv for Python, npm for frontend

**Commands:**
```bash
# Install dependencies
cd a2a-inspector
uv sync
cd frontend && npm install

# Run locally (requires two terminals)
# Terminal 1 - Frontend
cd a2a-inspector/frontend
npm run build -- --watch

# Terminal 2 - Backend
cd a2a-inspector/backend
uv run app.py

# Run with Docker
cd a2a-inspector
docker build -t a2a-inspector .
docker run -d -p 8080:8080 a2a-inspector

# Linting and formatting
nox -s format  # Formats Python code using ruff
```

### instavibe-bootstrap
A project with Python backend services and MCP server tools.

**Structure:**
- `instavibe/`: Main application code
- `agents/`: Platform MCP client code
- `tools/`: Additional tools including MCP server
- `env/`: Virtual environment (Python)

## Google Cloud Shell Context

- 5GB persistent home directory
- VM is ephemeral (resets ~20 minutes after session ends)
- Pre-installed with Google Cloud SDK
- Current GCP project: gen-lang-client-0871164439
- Use `gcloud` commands for GCP interactions

## Key Files

- `/home/p_budhwar/.claude.json`: Claude configuration
- `/home/p_budhwar/.gemini/`: Gemini CLI configuration
- `/home/p_budhwar/project_id.txt`: Contains GCP project ID