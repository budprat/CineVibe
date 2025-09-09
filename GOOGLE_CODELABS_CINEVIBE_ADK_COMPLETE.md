# Building CineVibe: AI-Powered Film Production System with Google ADK & A2A Protocol

## Codelab Overview

**Duration**: 120 minutes  
**Difficulty**: Intermediate  
**Prerequisites**: Basic Python, Docker, Google Cloud Platform knowledge  
**What you'll build**: A complete AI-powered film production system using multi-agent orchestration

### What you'll learn
- Build autonomous AI agents using Google's Agent Development Kit (ADK)
- Implement Agent-to-Agent (A2A) protocol for inter-agent communication
- Create an MCP server for AI platform integration
- Use Spanner Graph Database for relationship modeling
- Deploy a complete multi-agent system on Google Cloud
- Orchestrate AI generation platforms for video production

### What you'll need
- Google Cloud account with billing enabled
- Google Cloud Shell or local development environment
- Basic familiarity with Python and REST APIs
- Understanding of containerization concepts

## Step 1: Environment Setup (10 minutes)

### Create a new Google Cloud Project

Open Google Cloud Shell and set up your project:

```bash
# Set your project ID
export PROJECT_ID="cinevibe-production-$(date +%s)"
gcloud projects create $PROJECT_ID --name="CineVibe Production"

# Switch to the new project
gcloud config set project $PROJECT_ID

# Enable billing (replace with your billing account ID)
gcloud beta billing projects link $PROJECT_ID \
  --billing-account=BILLING_ACCOUNT_ID

# Store project ID for later use
echo $PROJECT_ID > ~/project_id.txt
```

### Enable Required APIs

```bash
# Enable all necessary APIs
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  spanner.googleapis.com \
  compute.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com
```

### Install ADK and Dependencies

```bash
# Install Python 3.12 if not available
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip

# Create and activate virtual environment
python3.12 -m venv cinevibe-env
source cinevibe-env/bin/activate

# Install Google ADK and required packages
pip install --upgrade pip
pip install google-cloud-adk google-cloud-spanner flask grpcio-tools
```

### Clone the Repository Structure

```bash
# Create project structure
mkdir -p cinevibe-bootstrap/{agents,tools,cinevibe,tests,utils,shortcut}
cd cinevibe-bootstrap

# Initialize git repository
git init
echo "# CineVibe Bootstrap" > README.md
git add README.md
git commit -m "Initial commit"
```

✅ **Checkpoint**: You should now have a Google Cloud project with all APIs enabled and a basic project structure.

## Step 2: Understanding the Architecture (15 minutes)

### System Architecture Overview

CineVibe uses a sophisticated multi-agent architecture:

```
┌─────────────────────────────────────────────────┐
│                  User Interface                  │
│              (Web Application - Flask)           │
└─────────────────────┬───────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼───────────────────────────┐
│             Director Orchestrator                │
│         (Main Coordination Agent - ADK)          │
│                                                  │
│  • Receives production requests                  │
│  • Delegates tasks to specialized agents         │
│  • Manages production pipeline                   │
│  • Ensures quality and consistency              │
└─────────────────────┬───────────────────────────┘
                      │ A2A Protocol
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
┌───────▼────┐ ┌─────▼─────┐ ┌────▼──────┐ ┌────▼─────┐
│   Script   │ │  Visual   │ │Generation │ │   MCP    │
│  Analyzer  │ │Consistency│ │ Platform  │ │  Server  │
│   Agent    │ │   Agent   │ │   Agent   │ │(AI Tools)│
└───────┬────┘ └─────┬─────┘ └────┬──────┘ └────┬─────┘
        │             │             │              │
┌───────▼─────────────▼─────────────▼──────────────▼─────┐
│              Spanner Graph Database                     │
│                                                         │
│  Nodes: Characters, Scenes, Assets, Styles            │
│  Edges: Relationships, Sequences, Dependencies         │
└─────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

**Director Orchestrator**
- Central coordination hub
- Manages production workflow
- Quality assurance and validation
- Progress tracking and reporting

**Script Analyzer Agent**
- Parses screenplay formats (PDF, FDX, plain text)
- Extracts characters, scenes, and dialogue
- Creates scene breakdowns
- Identifies narrative elements

**Visual Consistency Agent**
- Creates "Character DNA" profiles
- Manages style guides
- Validates generated content
- Ensures visual continuity

**Generation Platform Agent**
- Interfaces with AI platforms (Runway, Pika, Midjourney)
- Formats platform-specific prompts
- Manages generation queues
- Handles retries and failures

**MCP Server**
- Provides tools for AI platform access
- Manages API credentials
- Handles rate limiting
- Provides unified interface

### Data Flow

1. **Script Upload** → Web App → Director
2. **Analysis** → Director → Script Analyzer → Database
3. **Character Creation** → Director → Visual Consistency → Database
4. **Generation** → Director → Generation Platform → MCP Server → AI Platforms
5. **Validation** → Visual Consistency → Director
6. **Output** → Director → Web App → User

✅ **Checkpoint**: You understand the multi-agent architecture and data flow.

## Step 3: Setting Up Spanner Graph Database (20 minutes)

### Create Spanner Instance

```bash
# Set environment variables
export SPANNER_INSTANCE_ID="cinevibe-graph-instance"
export SPANNER_DATABASE_ID="cinevibe-graphdb"
export REGION="us-central1"

# Create Spanner instance (100 processing units for development)
gcloud spanner instances create $SPANNER_INSTANCE_ID \
  --config=regional-$REGION \
  --description="CineVibe Graph Database Instance" \
  --processing-units=100
```

### Create Graph Database Schema

Create `setup_database.py`:

```python
from google.cloud import spanner
from google.cloud.spanner_admin_database_v1 import CreateDatabaseRequest
import os

def create_graph_database():
    project_id = os.environ.get('PROJECT_ID')
    instance_id = os.environ.get('SPANNER_INSTANCE_ID')
    database_id = os.environ.get('SPANNER_DATABASE_ID')
    
    spanner_client = spanner.Client(project=project_id)
    instance = spanner_client.instance(instance_id)
    
    # Define the DDL with property graph
    ddl_statements = [
        """CREATE TABLE Character (
            character_id STRING(36) NOT NULL,
            name STRING(100) NOT NULL,
            description STRING(MAX),
            dna_profile JSON,
            visual_references JSON,
            created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
            updated_at TIMESTAMP OPTIONS (allow_commit_timestamp=true),
        ) PRIMARY KEY (character_id)""",
        
        """CREATE TABLE Scene (
            scene_id STRING(36) NOT NULL,
            scene_number INT64 NOT NULL,
            location STRING(200),
            time_of_day STRING(50),
            description STRING(MAX),
            dialogue JSON,
            shot_list JSON,
            created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
        ) PRIMARY KEY (scene_id)""",
        
        """CREATE TABLE Asset (
            asset_id STRING(36) NOT NULL,
            asset_type STRING(50) NOT NULL,
            platform STRING(50),
            prompt STRING(MAX),
            url STRING(500),
            metadata JSON,
            quality_score FLOAT64,
            created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
        ) PRIMARY KEY (asset_id)""",
        
        """CREATE TABLE CharacterAppearance (
            appearance_id STRING(36) NOT NULL,
            character_id STRING(36) NOT NULL,
            scene_id STRING(36) NOT NULL,
            costume_description STRING(MAX),
            emotional_state STRING(100),
            FOREIGN KEY (character_id) REFERENCES Character (character_id),
            FOREIGN KEY (scene_id) REFERENCES Scene (scene_id),
        ) PRIMARY KEY (appearance_id)""",
        
        """CREATE TABLE SceneSequence (
            sequence_id STRING(36) NOT NULL,
            from_scene_id STRING(36) NOT NULL,
            to_scene_id STRING(36) NOT NULL,
            transition_type STRING(50),
            FOREIGN KEY (from_scene_id) REFERENCES Scene (scene_id),
            FOREIGN KEY (to_scene_id) REFERENCES Scene (scene_id),
        ) PRIMARY KEY (sequence_id)""",
        
        """CREATE PROPERTY GRAPH CineGraph
            NODE TABLES (
                Character,
                Scene,
                Asset
            )
            EDGE TABLES (
                CharacterAppearance
                    SOURCE KEY (character_id) REFERENCES Character (character_id)
                    DESTINATION KEY (scene_id) REFERENCES Scene (scene_id)
                    LABEL AppearsIn,
                SceneSequence
                    SOURCE KEY (from_scene_id) REFERENCES Scene (scene_id)
                    DESTINATION KEY (to_scene_id) REFERENCES Scene (scene_id)
                    LABEL FollowedBy
            )"""
    ]
    
    # Create database with DDL
    operation = instance.database(
        database_id,
        ddl_statements=ddl_statements
    ).create()
    
    print(f"Creating database {database_id}...")
    database = operation.result(120)  # Wait up to 120 seconds
    print(f"Created database {database.name}")
    
    return database

if __name__ == "__main__":
    create_graph_database()
```

Run the database setup:

```bash
python setup_database.py
```

### Test Graph Queries

Create `test_graph.py`:

```python
from google.cloud import spanner
import uuid

def test_graph_queries():
    client = spanner.Client()
    instance = client.instance(os.environ['SPANNER_INSTANCE_ID'])
    database = instance.database(os.environ['SPANNER_DATABASE_ID'])
    
    with database.snapshot() as snapshot:
        # Find all characters in a specific scene
        query = """
        GRAPH CineGraph
        MATCH (c:Character)-[:AppearsIn]->(s:Scene)
        WHERE s.location = @location
        RETURN c.name, s.scene_number
        """
        
        results = snapshot.execute_sql(
            query,
            params={'location': 'INT. COFFEE SHOP - DAY'},
            param_types={'location': spanner.param_types.STRING}
        )
        
        for row in results:
            print(f"Character: {row[0]}, Scene: {row[1]}")

if __name__ == "__main__":
    test_graph_queries()
```

✅ **Checkpoint**: You have a working Spanner Graph Database with schema for film production data.

## Step 4: Building the Script Analyzer Agent (20 minutes)

### Create Agent Structure

```bash
mkdir -p agents/script_analyzer
cd agents/script_analyzer
```

### Implement the Agent

Create `agent.py`:

```python
import os
import json
import re
import uuid
from typing import Dict, List, Any
from google.cloud import spanner
from flask import Flask, request, jsonify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class ScriptAnalyzer:
    def __init__(self):
        self.client = spanner.Client()
        self.instance = self.client.instance(os.environ['SPANNER_INSTANCE_ID'])
        self.database = self.instance.database(os.environ['SPANNER_DATABASE_ID'])
    
    def parse_screenplay(self, script_text: str) -> Dict[str, Any]:
        """Parse screenplay text and extract elements"""
        
        # Regular expressions for screenplay elements
        scene_pattern = r'^(INT\.|EXT\.|INT/EXT\.).*$'
        character_pattern = r'^[A-Z][A-Z\s]+(\(.*\))?$'
        dialogue_pattern = r'^[A-Z][a-z].*$'
        
        scenes = []
        characters = set()
        current_scene = None
        current_character = None
        
        lines = script_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for scene heading
            if re.match(scene_pattern, line):
                if current_scene:
                    scenes.append(current_scene)
                
                current_scene = {
                    'id': str(uuid.uuid4()),
                    'heading': line,
                    'location': self.extract_location(line),
                    'time': self.extract_time(line),
                    'characters': set(),
                    'dialogue': []
                }
            
            # Check for character name
            elif re.match(character_pattern, line) and not re.match(dialogue_pattern, line):
                character_name = line.split('(')[0].strip()
                characters.add(character_name)
                current_character = character_name
                if current_scene:
                    current_scene['characters'].add(character_name)
            
            # Check for dialogue
            elif current_character and re.match(dialogue_pattern, line):
                if current_scene:
                    current_scene['dialogue'].append({
                        'character': current_character,
                        'text': line
                    })
        
        # Add last scene
        if current_scene:
            scenes.append(current_scene)
        
        # Convert sets to lists for JSON serialization
        for scene in scenes:
            scene['characters'] = list(scene['characters'])
        
        return {
            'scenes': scenes,
            'characters': list(characters),
            'scene_count': len(scenes),
            'character_count': len(characters)
        }
    
    def extract_location(self, scene_heading: str) -> str:
        """Extract location from scene heading"""
        # Remove INT./EXT. prefix and time suffix
        location = re.sub(r'^(INT\.|EXT\.|INT/EXT\.)\s*', '', scene_heading)
        location = re.sub(r'\s*-\s*(DAY|NIGHT|DAWN|DUSK|CONTINUOUS).*$', '', location)
        return location.strip()
    
    def extract_time(self, scene_heading: str) -> str:
        """Extract time of day from scene heading"""
        time_match = re.search(r'(DAY|NIGHT|DAWN|DUSK|CONTINUOUS)', scene_heading)
        return time_match.group(1) if time_match else 'UNSPECIFIED'
    
    def store_in_database(self, analysis_result: Dict[str, Any]) -> None:
        """Store analysis results in Spanner"""
        
        def insert_data(transaction):
            # Insert characters
            character_data = []
            for char_name in analysis_result['characters']:
                character_data.append({
                    'character_id': str(uuid.uuid4()),
                    'name': char_name,
                    'description': f"Character from screenplay",
                    'dna_profile': json.dumps({}),
                    'visual_references': json.dumps([]),
                    'created_at': spanner.COMMIT_TIMESTAMP
                })
            
            if character_data:
                transaction.insert(
                    table='Character',
                    columns=['character_id', 'name', 'description', 'dna_profile', 
                            'visual_references', 'created_at'],
                    values=[[d['character_id'], d['name'], d['description'], 
                            d['dna_profile'], d['visual_references'], d['created_at']] 
                           for d in character_data]
                )
            
            # Insert scenes
            scene_data = []
            for idx, scene in enumerate(analysis_result['scenes']):
                scene_data.append({
                    'scene_id': scene['id'],
                    'scene_number': idx + 1,
                    'location': scene['location'],
                    'time_of_day': scene['time'],
                    'description': scene['heading'],
                    'dialogue': json.dumps(scene['dialogue']),
                    'shot_list': json.dumps([]),
                    'created_at': spanner.COMMIT_TIMESTAMP
                })
            
            if scene_data:
                transaction.insert(
                    table='Scene',
                    columns=['scene_id', 'scene_number', 'location', 'time_of_day',
                            'description', 'dialogue', 'shot_list', 'created_at'],
                    values=[[d['scene_id'], d['scene_number'], d['location'], 
                            d['time_of_day'], d['description'], d['dialogue'],
                            d['shot_list'], d['created_at']] for d in scene_data]
                )
        
        self.database.run_in_transaction(insert_data)
        logger.info(f"Stored {len(analysis_result['characters'])} characters and "
                   f"{len(analysis_result['scenes'])} scenes in database")

analyzer = ScriptAnalyzer()

@app.route('/analyze', methods=['POST'])
def analyze_script():
    """Analyze screenplay endpoint"""
    try:
        data = request.json
        script_text = data.get('script_text', '')
        
        if not script_text:
            return jsonify({'error': 'No script text provided'}), 400
        
        # Analyze the script
        result = analyzer.parse_screenplay(script_text)
        
        # Store in database
        analyzer.store_in_database(result)
        
        return jsonify({
            'status': 'success',
            'analysis': result
        })
    
    except Exception as e:
        logger.error(f"Error analyzing script: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/agent-card', methods=['GET'])
def agent_card():
    """Return agent card for A2A protocol"""
    return jsonify({
        'name': 'Script Analyzer Agent',
        'version': '1.0.0',
        'description': 'Analyzes screenplays and extracts narrative elements',
        'capabilities': [
            'screenplay_parsing',
            'character_extraction',
            'scene_breakdown',
            'dialogue_analysis'
        ],
        'endpoints': {
            'analyze': '/analyze'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "agent.py"]
```

Create `requirements.txt`:

```
Flask==3.0.0
google-cloud-spanner==3.40.1
google-cloud-adk==0.1.0
uuid
```

### Deploy the Agent

```bash
# Build and push container
export ARTIFACT_REPO="cinevibe-agents"
export REGION="us-central1"

# Create artifact repository
gcloud artifacts repositories create $ARTIFACT_REPO \
  --repository-format=docker \
  --location=$REGION

# Configure docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/script-analyzer:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/script-analyzer:latest

# Deploy to Cloud Run
gcloud run deploy script-analyzer \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/script-analyzer:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},SPANNER_INSTANCE_ID=${SPANNER_INSTANCE_ID},SPANNER_DATABASE_ID=${SPANNER_DATABASE_ID}"
```

✅ **Checkpoint**: You have deployed the Script Analyzer Agent that can parse screenplays and store data in Spanner.

## Step 5: Building the Visual Consistency Agent (15 minutes)

### Create Visual Consistency Agent

```bash
mkdir -p agents/visual_consistency
cd agents/visual_consistency
```

Create `agent.py`:

```python
import os
import json
import uuid
from typing import Dict, List, Any
from google.cloud import spanner
from flask import Flask, request, jsonify
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class VisualConsistencyAgent:
    def __init__(self):
        self.client = spanner.Client()
        self.instance = self.client.instance(os.environ['SPANNER_INSTANCE_ID'])
        self.database = self.instance.database(os.environ['SPANNER_DATABASE_ID'])
    
    def create_character_dna(self, character_name: str, description: str = None) -> Dict[str, Any]:
        """Create a Character DNA profile for consistent generation"""
        
        # Generate unique seed for consistency
        seed = hashlib.md5(character_name.encode()).hexdigest()
        
        # Build comprehensive character profile
        dna_profile = {
            'id': str(uuid.uuid4()),
            'name': character_name,
            'seed': seed,
            'physical_attributes': {
                'age_range': self.infer_age_range(description),
                'gender': self.infer_gender(description),
                'ethnicity': 'diverse',  # Default to diverse representation
                'height': 'average',
                'build': 'average',
                'distinctive_features': []
            },
            'style_guide': {
                'clothing_style': 'contemporary casual',
                'color_palette': ['neutral', 'earth tones'],
                'accessories': [],
                'grooming': 'well-groomed'
            },
            'personality_traits': {
                'primary': [],
                'secondary': [],
                'mood_default': 'neutral'
            },
            'visual_references': {
                'celebrity_likeness': [],
                'art_style': 'photorealistic',
                'lighting_preference': 'natural',
                'camera_angle_preference': 'eye-level'
            },
            'generation_parameters': {
                'consistency_weight': 0.8,
                'style_weight': 0.7,
                'quality_threshold': 0.85,
                'preferred_platforms': ['midjourney', 'runway']
            },
            'prompt_template': self.create_prompt_template(character_name)
        }
        
        # Store in database
        self.store_character_dna(dna_profile)
        
        return dna_profile
    
    def infer_age_range(self, description: str) -> str:
        """Infer age range from description"""
        if not description:
            return "25-45"
        
        description_lower = description.lower()
        if any(word in description_lower for word in ['young', 'teen', 'youth']):
            return "18-25"
        elif any(word in description_lower for word in ['middle-aged', 'mature']):
            return "40-55"
        elif any(word in description_lower for word in ['elderly', 'old', 'senior']):
            return "60+"
        else:
            return "25-45"
    
    def infer_gender(self, description: str) -> str:
        """Infer gender from description"""
        if not description:
            return "unspecified"
        
        description_lower = description.lower()
        if any(word in description_lower for word in ['he', 'him', 'his', 'man', 'male']):
            return "male"
        elif any(word in description_lower for word in ['she', 'her', 'woman', 'female']):
            return "female"
        else:
            return "unspecified"
    
    def create_prompt_template(self, character_name: str) -> str:
        """Create a reusable prompt template for the character"""
        return f"[Character: {character_name}] [Consistent appearance] [Seed: {{seed}}] {{additional_context}}"
    
    def validate_consistency(self, asset_id: str, character_dna: Dict) -> Dict[str, Any]:
        """Validate if generated asset matches character DNA"""
        
        # In production, this would use computer vision models
        # For now, return mock validation
        consistency_score = 0.85  # Placeholder
        
        validation_result = {
            'asset_id': asset_id,
            'character_id': character_dna['id'],
            'consistency_score': consistency_score,
            'passed': consistency_score >= character_dna['generation_parameters']['quality_threshold'],
            'issues': [],
            'recommendations': []
        }
        
        if consistency_score < 0.7:
            validation_result['issues'].append("Low consistency detected")
            validation_result['recommendations'].append("Regenerate with higher consistency weight")
        
        return validation_result
    
    def create_style_guide(self, project_name: str, style_references: List[str] = None) -> Dict[str, Any]:
        """Create a project-wide style guide"""
        
        style_guide = {
            'id': str(uuid.uuid4()),
            'project_name': project_name,
            'visual_style': {
                'genre': 'cinematic',
                'mood': 'dramatic',
                'color_grading': 'film-like',
                'aspect_ratio': '2.35:1',
                'resolution': '4K'
            },
            'lighting': {
                'primary': 'natural',
                'secondary': 'motivated',
                'style': 'high contrast'
            },
            'camera': {
                'movement': 'smooth',
                'angles': ['wide', 'medium', 'close-up'],
                'depth_of_field': 'cinematic'
            },
            'post_processing': {
                'color_correction': True,
                'film_grain': 'subtle',
                'vignette': 'light'
            },
            'reference_images': style_references or [],
            'created_at': str(uuid.uuid4())
        }
        
        return style_guide
    
    def store_character_dna(self, dna_profile: Dict) -> None:
        """Store character DNA in database"""
        
        def update_character(transaction):
            # Update character with DNA profile
            transaction.execute_update(
                f"""UPDATE Character 
                SET dna_profile = @dna_profile,
                    updated_at = CURRENT_TIMESTAMP()
                WHERE name = @name""",
                params={
                    'dna_profile': json.dumps(dna_profile),
                    'name': dna_profile['name']
                },
                param_types={
                    'dna_profile': spanner.param_types.STRING,
                    'name': spanner.param_types.STRING
                }
            )
        
        self.database.run_in_transaction(update_character)
        logger.info(f"Stored DNA profile for character: {dna_profile['name']}")

consistency_agent = VisualConsistencyAgent()

@app.route('/create-dna', methods=['POST'])
def create_character_dna():
    """Create character DNA endpoint"""
    try:
        data = request.json
        character_name = data.get('character_name')
        description = data.get('description', '')
        
        if not character_name:
            return jsonify({'error': 'Character name required'}), 400
        
        dna_profile = consistency_agent.create_character_dna(character_name, description)
        
        return jsonify({
            'status': 'success',
            'dna_profile': dna_profile
        })
    
    except Exception as e:
        logger.error(f"Error creating DNA: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/validate', methods=['POST'])
def validate_consistency():
    """Validate asset consistency endpoint"""
    try:
        data = request.json
        asset_id = data.get('asset_id')
        character_dna = data.get('character_dna')
        
        if not asset_id or not character_dna:
            return jsonify({'error': 'Asset ID and character DNA required'}), 400
        
        validation = consistency_agent.validate_consistency(asset_id, character_dna)
        
        return jsonify({
            'status': 'success',
            'validation': validation
        })
    
    except Exception as e:
        logger.error(f"Error validating: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/style-guide', methods=['POST'])
def create_style_guide():
    """Create style guide endpoint"""
    try:
        data = request.json
        project_name = data.get('project_name', 'Untitled Project')
        references = data.get('references', [])
        
        style_guide = consistency_agent.create_style_guide(project_name, references)
        
        return jsonify({
            'status': 'success',
            'style_guide': style_guide
        })
    
    except Exception as e:
        logger.error(f"Error creating style guide: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/agent-card', methods=['GET'])
def agent_card():
    """Return agent card for A2A protocol"""
    return jsonify({
        'name': 'Visual Consistency Agent',
        'version': '1.0.0',
        'description': 'Maintains visual consistency across generated content',
        'capabilities': [
            'character_dna_creation',
            'style_guide_management',
            'consistency_validation',
            'prompt_optimization'
        ],
        'endpoints': {
            'create_dna': '/create-dna',
            'validate': '/validate',
            'style_guide': '/style-guide'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

Deploy the Visual Consistency Agent:

```bash
# Build and deploy
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/visual-consistency:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/visual-consistency:latest

gcloud run deploy visual-consistency \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/visual-consistency:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},SPANNER_INSTANCE_ID=${SPANNER_INSTANCE_ID},SPANNER_DATABASE_ID=${SPANNER_DATABASE_ID}"
```

✅ **Checkpoint**: Visual Consistency Agent is deployed and can create Character DNA profiles.

## Step 6: Building the MCP Server for AI Platforms (15 minutes)

### Create MCP Server

```bash
mkdir -p tools/mcp_server
cd tools/mcp_server
```

Create `mcp_server.py`:

```python
import os
import json
import asyncio
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import aiohttp
from flask import Flask, request, jsonify
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class Platform(Enum):
    MIDJOURNEY = "midjourney"
    RUNWAY = "runway"
    PIKA = "pika"
    STABLE_DIFFUSION = "stable_diffusion"
    DALLE = "dalle"

@dataclass
class GenerationRequest:
    platform: Platform
    prompt: str
    parameters: Dict[str, Any]
    character_dna: Dict[str, Any] = None
    style_guide: Dict[str, Any] = None

class AIGenerationPlatform:
    def __init__(self):
        self.platforms = {
            Platform.MIDJOURNEY: self.generate_midjourney,
            Platform.RUNWAY: self.generate_runway,
            Platform.PIKA: self.generate_pika,
            Platform.STABLE_DIFFUSION: self.generate_stable_diffusion,
            Platform.DALLE: self.generate_dalle
        }
        self.session = None
    
    async def initialize(self):
        """Initialize async session"""
        self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Cleanup async session"""
        if self.session:
            await self.session.close()
    
    async def generate(self, request: GenerationRequest) -> Dict[str, Any]:
        """Route generation request to appropriate platform"""
        
        if request.platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {request.platform}")
        
        # Enhance prompt with character DNA if provided
        enhanced_prompt = self.enhance_prompt(request)
        
        # Call platform-specific generation method
        result = await self.platforms[request.platform](enhanced_prompt, request.parameters)
        
        # Add metadata
        result['metadata'] = {
            'platform': request.platform.value,
            'original_prompt': request.prompt,
            'enhanced_prompt': enhanced_prompt,
            'timestamp': time.time(),
            'character_dna_used': bool(request.character_dna),
            'style_guide_used': bool(request.style_guide)
        }
        
        return result
    
    def enhance_prompt(self, request: GenerationRequest) -> str:
        """Enhance prompt with character DNA and style guide"""
        
        enhanced = request.prompt
        
        # Add character DNA elements
        if request.character_dna:
            dna = request.character_dna
            character_desc = []
            
            if 'physical_attributes' in dna:
                attrs = dna['physical_attributes']
                character_desc.append(f"{attrs.get('age_range', '')} years old")
                character_desc.append(attrs.get('gender', ''))
                character_desc.append(attrs.get('ethnicity', ''))
            
            if 'style_guide' in dna:
                style = dna['style_guide']
                character_desc.append(f"wearing {style.get('clothing_style', '')}")
            
            if character_desc:
                enhanced = f"{enhanced}, {', '.join(filter(None, character_desc))}"
            
            # Add consistency seed
            if 'seed' in dna:
                enhanced = f"{enhanced} --seed {dna['seed']}"
        
        # Add style guide elements
        if request.style_guide:
            guide = request.style_guide
            if 'visual_style' in guide:
                style = guide['visual_style']
                enhanced = f"{enhanced}, {style.get('genre', '')} style"
                enhanced = f"{enhanced}, {style.get('mood', '')} mood"
        
        return enhanced
    
    async def generate_midjourney(self, prompt: str, parameters: Dict) -> Dict[str, Any]:
        """Generate using Midjourney API"""
        
        # Placeholder for Midjourney API integration
        # In production, this would call actual Midjourney API
        
        await asyncio.sleep(2)  # Simulate API call
        
        return {
            'status': 'success',
            'platform': 'midjourney',
            'url': f"https://placeholder.midjourney.com/{hash(prompt)}.png",
            'generation_time': 2.0,
            'parameters_used': {
                'model': 'v6',
                'quality': parameters.get('quality', 1),
                'stylize': parameters.get('stylize', 100)
            }
        }
    
    async def generate_runway(self, prompt: str, parameters: Dict) -> Dict[str, Any]:
        """Generate using Runway API"""
        
        # Placeholder for Runway API integration
        await asyncio.sleep(3)
        
        return {
            'status': 'success',
            'platform': 'runway',
            'url': f"https://placeholder.runway.com/{hash(prompt)}.mp4",
            'generation_time': 3.0,
            'parameters_used': {
                'model': 'gen-2',
                'duration': parameters.get('duration', 4),
                'fps': parameters.get('fps', 24)
            }
        }
    
    async def generate_pika(self, prompt: str, parameters: Dict) -> Dict[str, Any]:
        """Generate using Pika API"""
        
        # Placeholder for Pika API integration
        await asyncio.sleep(2.5)
        
        return {
            'status': 'success',
            'platform': 'pika',
            'url': f"https://placeholder.pika.com/{hash(prompt)}.mp4",
            'generation_time': 2.5,
            'parameters_used': {
                'model': 'pika-1.0',
                'motion': parameters.get('motion', 'medium'),
                'camera': parameters.get('camera', 'static')
            }
        }
    
    async def generate_stable_diffusion(self, prompt: str, parameters: Dict) -> Dict[str, Any]:
        """Generate using Stable Diffusion API"""
        
        # Placeholder for Stable Diffusion API integration
        await asyncio.sleep(1.5)
        
        return {
            'status': 'success',
            'platform': 'stable_diffusion',
            'url': f"https://placeholder.sd.com/{hash(prompt)}.png",
            'generation_time': 1.5,
            'parameters_used': {
                'model': 'sdxl-1.0',
                'steps': parameters.get('steps', 50),
                'cfg_scale': parameters.get('cfg_scale', 7.5)
            }
        }
    
    async def generate_dalle(self, prompt: str, parameters: Dict) -> Dict[str, Any]:
        """Generate using DALL-E API"""
        
        # Placeholder for DALL-E API integration
        await asyncio.sleep(2)
        
        return {
            'status': 'success',
            'platform': 'dalle',
            'url': f"https://placeholder.dalle.com/{hash(prompt)}.png",
            'generation_time': 2.0,
            'parameters_used': {
                'model': 'dall-e-3',
                'size': parameters.get('size', '1024x1024'),
                'quality': parameters.get('quality', 'standard')
            }
        }
    
    def get_platform_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of all platforms"""
        
        return {
            'midjourney': {
                'types': ['image'],
                'max_resolution': '2048x2048',
                'features': ['style transfer', 'variations', 'upscaling']
            },
            'runway': {
                'types': ['video'],
                'max_duration': 16,
                'features': ['text-to-video', 'image-to-video', 'video-to-video']
            },
            'pika': {
                'types': ['video'],
                'max_duration': 3,
                'features': ['text-to-video', 'image animation']
            },
            'stable_diffusion': {
                'types': ['image'],
                'max_resolution': '1024x1024',
                'features': ['controlnet', 'inpainting', 'upscaling']
            },
            'dalle': {
                'types': ['image'],
                'max_resolution': '1024x1024',
                'features': ['variations', 'editing']
            }
        }

# Global platform instance
platform_manager = AIGenerationPlatform()

@app.route('/generate', methods=['POST'])
async def generate():
    """Generate content endpoint"""
    try:
        data = request.json
        
        # Parse request
        platform = Platform(data.get('platform', 'midjourney'))
        prompt = data.get('prompt', '')
        parameters = data.get('parameters', {})
        character_dna = data.get('character_dna')
        style_guide = data.get('style_guide')
        
        if not prompt:
            return jsonify({'error': 'Prompt required'}), 400
        
        # Create generation request
        gen_request = GenerationRequest(
            platform=platform,
            prompt=prompt,
            parameters=parameters,
            character_dna=character_dna,
            style_guide=style_guide
        )
        
        # Initialize platform if needed
        if not platform_manager.session:
            await platform_manager.initialize()
        
        # Generate content
        result = await platform_manager.generate(gen_request)
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get platform capabilities endpoint"""
    return jsonify(platform_manager.get_platform_capabilities())

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available MCP tools"""
    return jsonify({
        'tools': [
            {
                'name': 'generate_image',
                'description': 'Generate images using AI platforms',
                'parameters': ['prompt', 'platform', 'parameters']
            },
            {
                'name': 'generate_video',
                'description': 'Generate videos using AI platforms',
                'parameters': ['prompt', 'platform', 'parameters', 'duration']
            },
            {
                'name': 'enhance_prompt',
                'description': 'Enhance prompt with character DNA',
                'parameters': ['prompt', 'character_dna', 'style_guide']
            }
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

Deploy MCP Server:

```bash
# Create requirements.txt
cat > requirements.txt << EOF
Flask==3.0.0
aiohttp==3.9.0
asyncio
EOF

# Build and deploy
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/mcp-server:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/mcp-server:latest

gcloud run deploy mcp-server \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/mcp-server:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated
```

✅ **Checkpoint**: MCP Server is deployed and can interface with multiple AI generation platforms.

## Step 7: Building the Director Orchestrator (20 minutes)

### Create Director Orchestrator

```bash
mkdir -p agents/director
cd agents/director
```

Create `orchestrator.py`:

```python
import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp
from flask import Flask, request, jsonify
from google.cloud import spanner
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ProductionTask:
    id: str
    type: str
    status: TaskStatus
    agent: str
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

class DirectorOrchestrator:
    def __init__(self):
        self.client = spanner.Client()
        self.instance = self.client.instance(os.environ['SPANNER_INSTANCE_ID'])
        self.database = self.instance.database(os.environ['SPANNER_DATABASE_ID'])
        
        # Agent endpoints (would be discovered via A2A in production)
        self.agents = {
            'script_analyzer': os.environ.get('SCRIPT_ANALYZER_URL', 'http://script-analyzer:8080'),
            'visual_consistency': os.environ.get('VISUAL_CONSISTENCY_URL', 'http://visual-consistency:8080'),
            'generation_platform': os.environ.get('GENERATION_PLATFORM_URL', 'http://generation-platform:8080'),
            'mcp_server': os.environ.get('MCP_SERVER_URL', 'http://mcp-server:8080')
        }
        
        self.session = None
        self.production_queue = []
        self.production_status = {}
    
    async def initialize(self):
        """Initialize async components"""
        self.session = aiohttp.ClientSession()
        await self.discover_agents()
    
    async def cleanup(self):
        """Cleanup async components"""
        if self.session:
            await self.session.close()
    
    async def discover_agents(self):
        """Discover available agents via A2A protocol"""
        
        for agent_name, url in self.agents.items():
            try:
                async with self.session.get(f"{url}/agent-card") as response:
                    if response.status == 200:
                        card = await response.json()
                        logger.info(f"Discovered agent: {agent_name} - {card.get('description')}")
                    else:
                        logger.warning(f"Agent {agent_name} not responding")
            except Exception as e:
                logger.error(f"Failed to discover {agent_name}: {str(e)}")
    
    async def start_production(self, project_data: Dict[str, Any]) -> str:
        """Start a new production from screenplay"""
        
        production_id = str(uuid.uuid4())
        
        # Initialize production status
        self.production_status[production_id] = {
            'id': production_id,
            'status': 'initializing',
            'project_name': project_data.get('project_name', 'Untitled'),
            'created_at': time.time(),
            'tasks': [],
            'completed_tasks': 0,
            'total_tasks': 0
        }
        
        # Create production pipeline
        pipeline = self.create_production_pipeline(production_id, project_data)
        
        # Queue all tasks
        for task in pipeline:
            self.production_queue.append(task)
            self.production_status[production_id]['tasks'].append(task.id)
        
        self.production_status[production_id]['total_tasks'] = len(pipeline)
        self.production_status[production_id]['status'] = 'in_progress'
        
        # Start processing pipeline
        asyncio.create_task(self.process_pipeline(production_id))
        
        return production_id
    
    def create_production_pipeline(self, production_id: str, project_data: Dict[str, Any]) -> List[ProductionTask]:
        """Create production pipeline tasks"""
        
        pipeline = []
        
        # Task 1: Analyze screenplay
        pipeline.append(ProductionTask(
            id=f"{production_id}_analyze",
            type="screenplay_analysis",
            status=TaskStatus.PENDING,
            agent="script_analyzer",
            payload={
                'script_text': project_data.get('script_text', ''),
                'production_id': production_id
            }
        ))
        
        # Task 2: Create character DNAs
        # This will be populated after script analysis
        pipeline.append(ProductionTask(
            id=f"{production_id}_character_dna",
            type="character_dna_creation",
            status=TaskStatus.PENDING,
            agent="visual_consistency",
            payload={
                'production_id': production_id,
                'depends_on': f"{production_id}_analyze"
            }
        ))
        
        # Task 3: Create style guide
        pipeline.append(ProductionTask(
            id=f"{production_id}_style_guide",
            type="style_guide_creation",
            status=TaskStatus.PENDING,
            agent="visual_consistency",
            payload={
                'project_name': project_data.get('project_name'),
                'style_references': project_data.get('style_references', []),
                'production_id': production_id
            }
        ))
        
        # Task 4: Generate storyboards
        pipeline.append(ProductionTask(
            id=f"{production_id}_storyboards",
            type="storyboard_generation",
            status=TaskStatus.PENDING,
            agent="mcp_server",
            payload={
                'production_id': production_id,
                'depends_on': [f"{production_id}_character_dna", f"{production_id}_style_guide"]
            }
        ))
        
        # Task 5: Generate key frames
        pipeline.append(ProductionTask(
            id=f"{production_id}_keyframes",
            type="keyframe_generation",
            status=TaskStatus.PENDING,
            agent="mcp_server",
            payload={
                'production_id': production_id,
                'depends_on': f"{production_id}_storyboards"
            }
        ))
        
        # Task 6: Generate video sequences
        pipeline.append(ProductionTask(
            id=f"{production_id}_videos",
            type="video_generation",
            status=TaskStatus.PENDING,
            agent="mcp_server",
            payload={
                'production_id': production_id,
                'depends_on': f"{production_id}_keyframes"
            }
        ))
        
        # Task 7: Quality validation
        pipeline.append(ProductionTask(
            id=f"{production_id}_validation",
            type="quality_validation",
            status=TaskStatus.PENDING,
            agent="visual_consistency",
            payload={
                'production_id': production_id,
                'depends_on': f"{production_id}_videos"
            }
        ))
        
        return pipeline
    
    async def process_pipeline(self, production_id: str):
        """Process production pipeline asynchronously"""
        
        tasks = [task for task in self.production_queue 
                if task.id.startswith(production_id)]
        
        while tasks:
            # Process tasks that are ready
            ready_tasks = [task for task in tasks 
                          if task.status == TaskStatus.PENDING 
                          and self.check_dependencies(task)]
            
            # Process ready tasks in parallel
            if ready_tasks:
                await asyncio.gather(*[self.execute_task(task) for task in ready_tasks])
            
            # Update production status
            completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
            self.production_status[production_id]['completed_tasks'] = completed
            
            # Check if all tasks are done
            if all(task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] for task in tasks):
                break
            
            # Wait before checking again
            await asyncio.sleep(1)
        
        # Mark production as complete
        self.production_status[production_id]['status'] = 'completed'
        logger.info(f"Production {production_id} completed")
    
    def check_dependencies(self, task: ProductionTask) -> bool:
        """Check if task dependencies are met"""
        
        if 'depends_on' not in task.payload:
            return True
        
        dependencies = task.payload['depends_on']
        if isinstance(dependencies, str):
            dependencies = [dependencies]
        
        for dep_id in dependencies:
            dep_task = next((t for t in self.production_queue if t.id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def execute_task(self, task: ProductionTask):
        """Execute a single task"""
        
        task.status = TaskStatus.IN_PROGRESS
        logger.info(f"Executing task: {task.id} ({task.type})")
        
        try:
            # Get agent URL
            agent_url = self.agents.get(task.agent)
            if not agent_url:
                raise ValueError(f"Unknown agent: {task.agent}")
            
            # Determine endpoint based on task type
            endpoint = self.get_agent_endpoint(task.type)
            
            # Make request to agent
            async with self.session.post(
                f"{agent_url}{endpoint}",
                json=task.payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    logger.info(f"Task {task.id} completed successfully")
                    
                    # Process task results
                    await self.process_task_result(task)
                else:
                    error_text = await response.text()
                    raise Exception(f"Agent returned {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"Task {task.id} failed: {str(e)}")
            task.error = str(e)
            
            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.RETRYING
                await asyncio.sleep(2 ** task.retries)  # Exponential backoff
                await self.execute_task(task)
            else:
                task.status = TaskStatus.FAILED
    
    def get_agent_endpoint(self, task_type: str) -> str:
        """Get agent endpoint for task type"""
        
        endpoints = {
            'screenplay_analysis': '/analyze',
            'character_dna_creation': '/create-dna',
            'style_guide_creation': '/style-guide',
            'storyboard_generation': '/generate',
            'keyframe_generation': '/generate',
            'video_generation': '/generate',
            'quality_validation': '/validate'
        }
        
        return endpoints.get(task_type, '/process')
    
    async def process_task_result(self, task: ProductionTask):
        """Process task results and update dependent tasks"""
        
        # Handle screenplay analysis results
        if task.type == 'screenplay_analysis':
            analysis = task.result.get('analysis', {})
            characters = analysis.get('characters', [])
            
            # Create character DNA tasks for each character
            for character in characters:
                dna_task = next((t for t in self.production_queue 
                               if t.type == 'character_dna_creation' 
                               and t.id.startswith(task.id.split('_')[0])), None)
                
                if dna_task:
                    dna_task.payload['characters'] = characters
        
        # Store results in database
        await self.store_task_result(task)
    
    async def store_task_result(self, task: ProductionTask):
        """Store task results in database"""
        
        def insert_result(transaction):
            # Store as production artifact
            transaction.insert(
                table='Asset',
                columns=['asset_id', 'asset_type', 'platform', 'prompt', 
                        'url', 'metadata', 'quality_score', 'created_at'],
                values=[[
                    task.id,
                    task.type,
                    task.agent,
                    json.dumps(task.payload),
                    '',  # URL would be populated for actual assets
                    json.dumps(task.result),
                    0.0,  # Quality score would be calculated
                    spanner.COMMIT_TIMESTAMP
                ]]
            )
        
        self.database.run_in_transaction(insert_result)
    
    def get_production_status(self, production_id: str) -> Dict[str, Any]:
        """Get current production status"""
        
        if production_id not in self.production_status:
            return {'error': 'Production not found'}
        
        status = self.production_status[production_id].copy()
        
        # Add task details
        tasks = [task for task in self.production_queue 
                if task.id.startswith(production_id)]
        
        status['tasks_detail'] = [
            {
                'id': task.id,
                'type': task.type,
                'status': task.status.value,
                'agent': task.agent,
                'error': task.error
            }
            for task in tasks
        ]
        
        return status

# Global orchestrator instance
orchestrator = DirectorOrchestrator()

@app.route('/start-production', methods=['POST'])
async def start_production():
    """Start a new production"""
    try:
        data = request.json
        
        if not data.get('script_text'):
            return jsonify({'error': 'Script text required'}), 400
        
        # Initialize if needed
        if not orchestrator.session:
            await orchestrator.initialize()
        
        # Start production
        production_id = await orchestrator.start_production(data)
        
        return jsonify({
            'status': 'success',
            'production_id': production_id,
            'message': 'Production started successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to start production: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/production-status/<production_id>', methods=['GET'])
def get_production_status(production_id):
    """Get production status"""
    
    status = orchestrator.get_production_status(production_id)
    
    if 'error' in status:
        return jsonify(status), 404
    
    return jsonify(status)

@app.route('/agent-card', methods=['GET'])
def agent_card():
    """Return agent card for A2A protocol"""
    return jsonify({
        'name': 'Director Orchestrator',
        'version': '1.0.0',
        'description': 'Orchestrates the entire film production pipeline',
        'capabilities': [
            'production_management',
            'task_delegation',
            'quality_assurance',
            'pipeline_orchestration'
        ],
        'endpoints': {
            'start_production': '/start-production',
            'status': '/production-status'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

Deploy Director Orchestrator:

```bash
# Build and deploy
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/director:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/director:latest

gcloud run deploy director \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/director:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},SPANNER_INSTANCE_ID=${SPANNER_INSTANCE_ID},SPANNER_DATABASE_ID=${SPANNER_DATABASE_ID}"
```

✅ **Checkpoint**: Director Orchestrator is deployed and can manage the production pipeline.

## Step 8: Building the Web Application (15 minutes)

### Create Flask Web Application

```bash
mkdir -p cinevibe/web
cd cinevibe/web
```

Create `app.py`:

```python
import os
import json
import uuid
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from werkzeug.utils import secure_filename
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Director orchestrator URL
DIRECTOR_URL = os.environ.get('DIRECTOR_URL', 'http://director:8080')

class CineVibeApp:
    def __init__(self):
        self.productions = {}
    
    def read_script_file(self, file_path: str) -> str:
        """Read and parse script file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    def start_new_production(self, script_text: str, project_name: str, 
                            style_references: list = None) -> str:
        """Start a new production via Director"""
        
        try:
            response = requests.post(
                f"{DIRECTOR_URL}/start-production",
                json={
                    'script_text': script_text,
                    'project_name': project_name,
                    'style_references': style_references or []
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                production_id = data.get('production_id')
                
                # Store production info
                self.productions[production_id] = {
                    'id': production_id,
                    'name': project_name,
                    'started_at': time.time(),
                    'status': 'in_progress'
                }
                
                return production_id
            else:
                raise Exception(f"Director returned {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to start production: {str(e)}")
            raise
    
    def get_production_status(self, production_id: str) -> dict:
        """Get production status from Director"""
        
        try:
            response = requests.get(
                f"{DIRECTOR_URL}/production-status/{production_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': 'Production not found'}
        
        except Exception as e:
            logger.error(f"Failed to get production status: {str(e)}")
            return {'error': str(e)}

cinevibe = CineVibeApp()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_script():
    """Upload script page"""
    
    if request.method == 'POST':
        # Check if file was uploaded
        if 'script_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['script_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read script content
        script_text = cinevibe.read_script_file(filepath)
        
        # Get project details
        project_name = request.form.get('project_name', 'Untitled Project')
        style_references = request.form.get('style_references', '').split(',')
        
        # Start production
        try:
            production_id = cinevibe.start_new_production(
                script_text, 
                project_name,
                style_references
            )
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return redirect(url_for('production_dashboard', production_id=production_id))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('upload.html')

@app.route('/production/<production_id>')
def production_dashboard(production_id):
    """Production dashboard"""
    
    production_info = cinevibe.productions.get(production_id, {})
    return render_template('dashboard.html', 
                         production_id=production_id,
                         production_info=production_info)

@app.route('/api/production/<production_id>/status')
def api_production_status(production_id):
    """API endpoint for production status"""
    
    status = cinevibe.get_production_status(production_id)
    return jsonify(status)

@app.route('/gallery')
def gallery():
    """Gallery of generated content"""
    return render_template('gallery.html')

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
```

### Create HTML Templates

Create `templates/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CineVibe - AI Film Production</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 90%;
            text-align: center;
        }
        
        h1 {
            font-size: 48px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            font-size: 20px;
            color: #666;
            margin-bottom: 40px;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        
        .feature {
            padding: 20px;
            border-radius: 10px;
            background: #f8f9fa;
        }
        
        .feature-icon {
            font-size: 40px;
            margin-bottom: 10px;
        }
        
        .feature-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .feature-desc {
            font-size: 14px;
            color: #666;
        }
        
        .cta-button {
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 30px;
            font-size: 18px;
            font-weight: 600;
            margin-top: 30px;
            transition: transform 0.3s;
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 CineVibe</h1>
        <p class="subtitle">Transform Screenplays into Professional Videos with AI</p>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">📝</div>
                <div class="feature-title">Script Analysis</div>
                <div class="feature-desc">Automatic extraction of characters, scenes, and dialogue</div>
            </div>
            
            <div class="feature">
                <div class="feature-icon">🎭</div>
                <div class="feature-title">Character DNA</div>
                <div class="feature-desc">Maintain perfect visual consistency across all content</div>
            </div>
            
            <div class="feature">
                <div class="feature-icon">🎨</div>
                <div class="feature-title">Multi-Platform</div>
                <div class="feature-desc">Generate with Runway, Pika, Midjourney, and more</div>
            </div>
            
            <div class="feature">
                <div class="feature-icon">🎬</div>
                <div class="feature-title">Production Pipeline</div>
                <div class="feature-desc">Complete workflow from script to final video</div>
            </div>
        </div>
        
        <a href="/upload" class="cta-button">Start New Production</a>
    </div>
</body>
</html>
```

Create `templates/upload.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Script - CineVibe</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .upload-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 90%;
        }
        
        h2 {
            margin-bottom: 30px;
            color: #333;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        input[type="text"],
        input[type="file"],
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .file-input-wrapper {
            position: relative;
            overflow: hidden;
            display: inline-block;
            width: 100%;
        }
        
        .file-input-wrapper input[type=file] {
            position: absolute;
            left: -9999px;
        }
        
        .file-input-label {
            display: block;
            padding: 20px;
            background: #f8f9fa;
            border: 2px dashed #667eea;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .file-input-label:hover {
            background: #667eea;
            color: white;
        }
        
        .submit-button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s;
        }
        
        .submit-button:hover {
            transform: translateY(-2px);
        }
        
        .info-box {
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="upload-container">
        <h2>📝 Upload Your Screenplay</h2>
        
        <div class="info-box">
            <strong>Supported Formats:</strong> Plain text, PDF, Final Draft (.fdx)
        </div>
        
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label for="project_name">Project Name</label>
                <input type="text" id="project_name" name="project_name" 
                       placeholder="Enter your project name" required>
            </div>
            
            <div class="form-group">
                <label for="script_file">Screenplay File</label>
                <div class="file-input-wrapper">
                    <input type="file" id="script_file" name="script_file" 
                           accept=".txt,.pdf,.fdx" required>
                    <label for="script_file" class="file-input-label">
                        📄 Click to select your screenplay file
                    </label>
                </div>
            </div>
            
            <div class="form-group">
                <label for="style_references">Style References (optional)</label>
                <textarea id="style_references" name="style_references" 
                          rows="3" placeholder="E.g., Blade Runner 2049, Inception, The Matrix"></textarea>
            </div>
            
            <button type="submit" class="submit-button">🚀 Start Production</button>
        </form>
    </div>
    
    <script>
        // Update file input label with selected filename
        document.getElementById('script_file').addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Click to select your screenplay file';
            document.querySelector('.file-input-label').textContent = '📄 ' + fileName;
        });
    </script>
</body>
</html>
```

Create `templates/dashboard.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production Dashboard - CineVibe</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .production-info {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .status-card h3 {
            margin-top: 0;
            color: #333;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }
        
        .task-list {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .task-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .task-item:last-child {
            border-bottom: none;
        }
        
        .task-status {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 15px;
        }
        
        .task-status.pending {
            background: #ffc107;
        }
        
        .task-status.in_progress {
            background: #2196f3;
            animation: pulse 1.5s infinite;
        }
        
        .task-status.completed {
            background: #4caf50;
        }
        
        .task-status.failed {
            background: #f44336;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .refresh-button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🎬 Production Dashboard</h1>
            <p>{{ production_info.name }}</p>
        </div>
    </div>
    
    <div class="container">
        <div class="production-info">
            <h2>Production Status</h2>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%">
                    <span id="progress-text">0%</span>
                </div>
            </div>
            <button class="refresh-button" onclick="refreshStatus()">🔄 Refresh Status</button>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📝 Script Analysis</h3>
                <p id="script-status">Pending...</p>
            </div>
            
            <div class="status-card">
                <h3>🎭 Character DNA</h3>
                <p id="character-status">Pending...</p>
            </div>
            
            <div class="status-card">
                <h3>🎨 Style Guide</h3>
                <p id="style-status">Pending...</p>
            </div>
            
            <div class="status-card">
                <h3>🎬 Generation</h3>
                <p id="generation-status">Pending...</p>
            </div>
        </div>
        
        <div class="task-list">
            <h2>Pipeline Tasks</h2>
            <div id="task-list">
                <!-- Tasks will be populated here -->
            </div>
        </div>
    </div>
    
    <script>
        const productionId = '{{ production_id }}';
        
        function refreshStatus() {
            fetch(`/api/production/${productionId}/status`)
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                });
        }
        
        function updateDashboard(data) {
            // Update progress bar
            const progress = (data.completed_tasks / data.total_tasks) * 100;
            document.getElementById('progress-fill').style.width = progress + '%';
            document.getElementById('progress-text').textContent = Math.round(progress) + '%';
            
            // Update task list
            const taskList = document.getElementById('task-list');
            taskList.innerHTML = '';
            
            if (data.tasks_detail) {
                data.tasks_detail.forEach(task => {
                    const taskItem = document.createElement('div');
                    taskItem.className = 'task-item';
                    
                    const statusDot = document.createElement('div');
                    statusDot.className = `task-status ${task.status}`;
                    
                    const taskInfo = document.createElement('div');
                    taskInfo.innerHTML = `
                        <strong>${task.type.replace(/_/g, ' ').toUpperCase()}</strong>
                        <br>
                        <small>Status: ${task.status} | Agent: ${task.agent}</small>
                        ${task.error ? `<br><small style="color: red">Error: ${task.error}</small>` : ''}
                    `;
                    
                    taskItem.appendChild(statusDot);
                    taskItem.appendChild(taskInfo);
                    taskList.appendChild(taskItem);
                });
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshStatus, 5000);
        
        // Initial load
        refreshStatus();
    </script>
</body>
</html>
```

Deploy Web Application:

```bash
# Build and deploy
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/cinevibe-web:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/cinevibe-web:latest

gcloud run deploy cinevibe-web \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/cinevibe-web:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="DIRECTOR_URL=https://director-xxxxx-uc.a.run.app"
```

✅ **Checkpoint**: Web application is deployed and accessible via Cloud Run URL.

## Step 9: Testing the Complete System (10 minutes)

### Create Test Screenplay

Create `test_screenplay.txt`:

```
FADE IN:

EXT. CITY STREET - DAWN

The sun rises over a bustling metropolis. SARAH (30s, determined) walks purposefully down the street.

INT. COFFEE SHOP - CONTINUOUS

Sarah enters, the bell above the door chiming. The barista, JAMES (20s, friendly), looks up.

JAMES
The usual?

SARAH
(smiling)
You know me too well.

James starts preparing her coffee. Sarah's phone buzzes.

SARAH (CONT'D)
(answering phone)
Yes? ... I'll be right there.

She grabs the coffee and rushes out.

EXT. OFFICE BUILDING - DAY

Sarah enters a gleaming glass tower.

INT. BOARDROOM - CONTINUOUS

Sarah bursts in. The BOARD MEMBERS turn to look at her.

SARAH
I have the solution.

FADE OUT.
```

### Test Production Pipeline

1. **Upload Script**:
   - Navigate to your Cloud Run URL
   - Click "Start New Production"
   - Upload the test screenplay
   - Enter project name: "Test Production"

2. **Monitor Progress**:
   - Watch the dashboard update in real-time
   - Verify each agent processes its tasks
   - Check for any errors in the pipeline

3. **Verify Database**:
   ```bash
   # Query Spanner to verify data
   gcloud spanner databases execute-sql $SPANNER_DATABASE_ID \
     --instance=$SPANNER_INSTANCE_ID \
     --sql="SELECT * FROM Character"
   ```

4. **Check Logs**:
   ```bash
   # View Cloud Run logs
   gcloud run logs read cinevibe-web --region=$REGION
   gcloud run logs read director --region=$REGION
   gcloud run logs read script-analyzer --region=$REGION
   ```

✅ **Checkpoint**: Complete system is working end-to-end.

## Step 10: Advanced Features and Optimization (10 minutes)

### Performance Optimization

1. **Enable Cloud CDN for Static Assets**:
```bash
# Create Cloud Storage bucket for static files
gsutil mb -p $PROJECT_ID gs://cinevibe-static-assets
gsutil iam ch allUsers:objectViewer gs://cinevibe-static-assets
```

2. **Implement Caching**:
```python
# Add Redis caching for Character DNA
from google.cloud import memcache

cache_client = memcache.Client()

def get_character_dna(character_id):
    # Try cache first
    cached = cache_client.get(f"dna_{character_id}")
    if cached:
        return json.loads(cached)
    
    # Query database
    dna = query_database(character_id)
    
    # Cache for 1 hour
    cache_client.set(f"dna_{character_id}", json.dumps(dna), expire=3600)
    return dna
```

3. **Enable Autoscaling**:
```bash
# Configure autoscaling for Cloud Run services
gcloud run services update director \
  --min-instances=1 \
  --max-instances=100 \
  --cpu=2 \
  --memory=4Gi \
  --region=$REGION
```

### Security Hardening

1. **Enable Authentication**:
```bash
# Remove public access
gcloud run services remove-iam-policy-binding director \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=$REGION

# Add service-to-service authentication
gcloud run services add-iam-policy-binding director \
  --member="serviceAccount:cinevibe-web@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=$REGION
```

2. **Store API Keys in Secret Manager**:
```bash
# Create secrets
echo -n "your-runway-api-key" | gcloud secrets create runway-api-key --data-file=-
echo -n "your-midjourney-api-key" | gcloud secrets create midjourney-api-key --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding runway-api-key \
  --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Monitoring and Observability

1. **Enable Cloud Trace**:
```python
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(
    BatchSpanProcessor(cloud_trace_exporter)
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Use in code
with tracer.start_as_current_span("process_screenplay"):
    # Your code here
    pass
```

2. **Create Monitoring Dashboard**:
```bash
# Create custom dashboard
gcloud monitoring dashboards create --config-from-file=dashboard.yaml
```

3. **Set Up Alerts**:
```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=$NOTIFICATION_CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition="rate(compute.googleapis.com/instance/cpu/utilization) > 0.8"
```

## Conclusion

Congratulations! 🎉 You've successfully built CineVibe, a complete AI-powered film production system using:

✅ **Google ADK** for agent development  
✅ **A2A Protocol** for agent communication  
✅ **Spanner Graph Database** for relationship modeling  
✅ **MCP Server** for AI platform integration  
✅ **Cloud Run** for scalable deployment  
✅ **Multi-agent orchestration** for complex workflows  

### What You've Learned

1. **Agent Development**: Building autonomous agents with specific capabilities
2. **Protocol Implementation**: Using A2A for standardized agent communication
3. **Graph Databases**: Modeling complex relationships with Spanner Graph
4. **Tool Integration**: Creating MCP servers for external tool access
5. **Orchestration**: Coordinating multiple agents for complex tasks
6. **Production Deployment**: Deploying scalable multi-agent systems on GCP

### Next Steps

1. **Integrate Real AI Platforms**: Replace placeholders with actual API integrations
2. **Enhance Script Analysis**: Add NLP models for deeper screenplay understanding
3. **Implement Computer Vision**: Add visual consistency validation using ML models
4. **Add Collaboration Features**: Enable multiple users to work on productions
5. **Export Capabilities**: Add export to video editing software formats

## 📚 Based On

This project adapts the **InstaVibe** multi-agent architecture tutorial for film production, demonstrating:
- ADK for agent development
- A2A protocol for agent communication
- MCP for tool integration
- Spanner Graph Database for relationship modeling
- Cloud Run for scalable deployment

### Resources

- [Google ADK Documentation](https://cloud.google.com/adk/docs)
- [A2A Protocol Specification](https://github.com/google/a2a-protocol)
- [Spanner Graph Documentation](https://cloud.google.com/spanner/docs/graph)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)

### Clean Up

To avoid charges, clean up resources when done:

```bash
# Delete Cloud Run services
gcloud run services delete cinevibe-web --region=$REGION
gcloud run services delete director --region=$REGION
gcloud run services delete script-analyzer --region=$REGION
gcloud run services delete visual-consistency --region=$REGION
gcloud run services delete mcp-server --region=$REGION

# Delete Spanner instance
gcloud spanner instances delete $SPANNER_INSTANCE_ID

# Delete Artifact Registry
gcloud artifacts repositories delete $ARTIFACT_REPO --location=$REGION

# Delete the project (if desired)
gcloud projects delete $PROJECT_ID
```

### 🙏 Acknowledgments

- Google ADK Team for the framework
- InstaVibe tutorial for the architecture pattern  
- Open source AI generation communities

---

**Thank you for completing this Codelab!** 

You now have the knowledge to build sophisticated multi-agent AI systems for any domain. The principles and patterns you've learned here can be applied to healthcare, finance, education, and many other fields where complex orchestration of AI capabilities is needed.

Happy building! 🚀