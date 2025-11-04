"""
CineVibe Web Application
Film production interface powered by multi-agent AI system
Based on InstaVibe's Flask application pattern
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from google.cloud import spanner
from google.cloud import aiplatform
import os
import json
import asyncio
import httpx
from datetime import datetime
import hashlib
import logging
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
# Require SECRET_KEY environment variable for security
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable must be set. Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'")

# Enable CORS
CORS(app)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Google Cloud clients
PROJECT_ID = os.environ.get("PROJECT_ID")
SPANNER_INSTANCE_ID = os.environ.get("SPANNER_INSTANCE_ID", "cinevibe-graph-instance")
SPANNER_DATABASE_ID = os.environ.get("SPANNER_DATABASE_ID", "graphdb")
DIRECTOR_AGENT_URL = os.environ.get("DIRECTOR_AGENT_URL", "http://localhost:8003")

# Initialize Spanner client
spanner_client = spanner.Client(project=PROJECT_ID)
instance = spanner_client.instance(SPANNER_INSTANCE_ID)
database = instance.database(SPANNER_DATABASE_ID)

@app.route("/")
def index():
    """Main landing page"""
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    """Production dashboard"""
    # Get active projects
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(
            "SELECT script_id, title, author, genre FROM Script ORDER BY created_at DESC LIMIT 10"
        )
        
        projects = []
        for row in results:
            projects.append({
                "id": row[0],
                "title": row[1],
                "author": row[2],
                "genre": row[3]
            })
    
    return render_template("dashboard.html", projects=projects)

@app.route("/api/upload_script", methods=["POST"])
async def upload_script():
    """Upload and analyze a screenplay"""
    try:
        data = request.json
        script_content = data.get("script")
        title = data.get("title", "Untitled")
        author = data.get("author", "Unknown")
        
        if not script_content:
            return jsonify({"error": "No script content provided"}), 400
        
        # Generate script ID
        script_id = f"script_{hashlib.md5(f'{title}_{datetime.utcnow()}'.encode()).hexdigest()[:12]}"
        
        # Store script in database
        with database.batch() as batch:
            batch.insert(
                table="Script",
                columns=["script_id", "title", "author", "script_content", "created_at"],
                values=[(script_id, title, author, script_content, spanner.COMMIT_TIMESTAMP)]
            )
        
        # Send to Director agent for analysis
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DIRECTOR_AGENT_URL}/analyze",
                json={
                    "script_id": script_id,
                    "script_content": script_content,
                    "title": title
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                analysis = response.json()
                
                # Store analysis results
                session["current_project"] = {
                    "script_id": script_id,
                    "title": title,
                    "analysis": analysis
                }
                
                return jsonify({
                    "success": True,
                    "script_id": script_id,
                    "analysis": analysis
                })
            else:
                return jsonify({"error": "Analysis failed"}), 500
                
    except Exception as e:
        logger.error(f"Error uploading script: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/create_character_dna", methods=["POST"])
async def create_character_dna():
    """Create Character DNA profiles"""
    try:
        data = request.json
        character_info = data.get("character")
        
        # Send to Director for character DNA creation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DIRECTOR_AGENT_URL}/create_character",
                json=character_info,
                timeout=30.0
            )
            
            if response.status_code == 200:
                character_dna = response.json()
                return jsonify({
                    "success": True,
                    "character_dna": character_dna
                })
            else:
                return jsonify({"error": "Character creation failed"}), 500
                
    except Exception as e:
        logger.error(f"Error creating character DNA: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate_storyboard", methods=["POST"])
async def generate_storyboard():
    """Generate storyboard for a scene"""
    try:
        data = request.json
        scene_id = data.get("scene_id")
        
        # Get scene details from database
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                "SELECT * FROM Scene WHERE scene_id = @scene_id",
                params={"scene_id": scene_id},
                param_types={"scene_id": spanner.param_types.STRING}
            )
            
            scene = None
            for row in results:
                scene = {
                    "scene_id": row[0],
                    "scene_number": row[2],
                    "location": row[3],
                    "time_of_day": row[4]
                }
                break
        
        if not scene:
            return jsonify({"error": "Scene not found"}), 404
        
        # Send to Director for storyboard generation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DIRECTOR_AGENT_URL}/generate_storyboard",
                json={"scene": scene},
                timeout=120.0  # Longer timeout for generation
            )
            
            if response.status_code == 200:
                storyboard = response.json()
                return jsonify({
                    "success": True,
                    "storyboard": storyboard
                })
            else:
                return jsonify({"error": "Storyboard generation failed"}), 500
                
    except Exception as e:
        logger.error(f"Error generating storyboard: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate_video", methods=["POST"])
async def generate_video():
    """Generate video for a scene"""
    try:
        data = request.json
        scene_id = data.get("scene_id")
        platform = data.get("platform", "auto")
        duration = data.get("duration", 5)
        
        # Send to Director for video generation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DIRECTOR_AGENT_URL}/generate_video",
                json={
                    "scene_id": scene_id,
                    "platform": platform,
                    "duration": duration
                },
                timeout=300.0  # 5 minute timeout for video generation
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    "success": True,
                    "video": result
                })
            else:
                return jsonify({"error": "Video generation failed"}), 500
                
    except Exception as e:
        logger.error(f"Error generating video: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/project/<project_id>")
def get_project(project_id):
    """Get project details"""
    try:
        project_data = {
            "script": {},
            "characters": [],
            "scenes": [],
            "assets": []
        }
        
        with database.snapshot() as snapshot:
            # Get script
            results = snapshot.execute_sql(
                "SELECT * FROM Script WHERE script_id = @script_id",
                params={"script_id": project_id},
                param_types={"script_id": spanner.param_types.STRING}
            )
            
            for row in results:
                project_data["script"] = {
                    "id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "genre": row[3]
                }
            
            # Get characters
            results = snapshot.execute_sql(
                """
                SELECT DISTINCT c.* 
                FROM Character c
                JOIN CharacterInScene cis ON c.character_id = cis.character_id
                JOIN Scene s ON cis.scene_id = s.scene_id
                WHERE s.script_id = @script_id
                """,
                params={"script_id": project_id},
                param_types={"script_id": spanner.param_types.STRING}
            )
            
            for row in results:
                project_data["characters"].append({
                    "id": row[0],
                    "name": row[1],
                    "age": row[2]
                })
            
            # Get scenes
            results = snapshot.execute_sql(
                "SELECT * FROM Scene WHERE script_id = @script_id ORDER BY scene_number",
                params={"script_id": project_id},
                param_types={"script_id": spanner.param_types.STRING}
            )
            
            for row in results:
                project_data["scenes"].append({
                    "id": row[0],
                    "number": row[2],
                    "location": row[3],
                    "time": row[4]
                })
            
            # Get generated assets
            results = snapshot.execute_sql(
                """
                SELECT ga.* 
                FROM GeneratedAsset ga
                JOIN Scene s ON ga.scene_id = s.scene_id
                WHERE s.script_id = @script_id
                ORDER BY ga.created_at DESC
                """,
                params={"script_id": project_id},
                param_types={"script_id": spanner.param_types.STRING}
            )
            
            for row in results:
                project_data["assets"].append({
                    "id": row[0],
                    "scene_id": row[1],
                    "platform": row[3],
                    "url": row[6],
                    "quality_score": row[7]
                })
        
        return jsonify(project_data)
        
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/production_status")
def production_status():
    """Get production pipeline status"""
    try:
        status = {
            "active_generations": 0,
            "completed_today": 0,
            "quality_average": 0.0,
            "platforms_available": ["runway", "pika", "midjourney", "stable_diffusion"]
        }
        
        with database.snapshot() as snapshot:
            # Get today's completions
            results = snapshot.execute_sql(
                """
                SELECT COUNT(*), AVG(quality_score)
                FROM GeneratedAsset
                WHERE DATE(created_at) = CURRENT_DATE()
                """
            )
            
            for row in results:
                status["completed_today"] = row[0] or 0
                status["quality_average"] = float(row[1] or 0)
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "CineVibe Web Application",
        "timestamp": datetime.utcnow().isoformat()
    })

# SocketIO Event Handlers for Real-time Updates

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to CineVibe real-time updates'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_project')
def handle_join_project(data):
    """Join a project room for real-time updates"""
    project_id = data.get('project_id')
    if project_id:
        join_room(f"project_{project_id}")
        logger.info(f"Client {request.sid} joined project {project_id}")
        emit('joined_project', {'project_id': project_id})

@socketio.on('leave_project')
def handle_leave_project(data):
    """Leave a project room"""
    project_id = data.get('project_id')
    if project_id:
        leave_room(f"project_{project_id}")
        logger.info(f"Client {request.sid} left project {project_id}")
        emit('left_project', {'project_id': project_id})

@socketio.on('request_status')
def handle_status_request(data):
    """Handle status request for a project"""
    project_id = data.get('project_id')
    if project_id:
        # Get status from database or cache
        status = get_project_status(project_id)
        emit('status_update', status)

def broadcast_pipeline_update(project_id, phase, status, progress=None):
    """Broadcast pipeline updates to all clients in a project room"""
    update = {
        'project_id': project_id,
        'phase': phase,
        'status': status,
        'progress': progress,
        'timestamp': datetime.utcnow().isoformat()
    }
    socketio.emit('pipeline_update', update, room=f"project_{project_id}")
    logger.info(f"Broadcast update for project {project_id}: {phase} - {status}")

def broadcast_generation_complete(project_id, asset_type, asset_url):
    """Broadcast when a generation is complete"""
    update = {
        'project_id': project_id,
        'type': 'generation_complete',
        'asset_type': asset_type,
        'asset_url': asset_url,
        'timestamp': datetime.utcnow().isoformat()
    }
    socketio.emit('generation_complete', update, room=f"project_{project_id}")

def monitor_agent_status():
    """Background thread to monitor agent status"""
    agents = {
        'script_analyzer': 'http://localhost:8001/health',
        'visual_consistency': 'http://localhost:8002/health',
        'generation_platform': 'http://localhost:8003/health',
        'director': 'http://localhost:8000/health'
    }
    
    while True:
        try:
            status = {}
            for agent_name, health_url in agents.items():
                try:
                    response = httpx.get(health_url, timeout=2.0)
                    status[agent_name] = 'online' if response.status_code == 200 else 'offline'
                except:
                    status[agent_name] = 'offline'
            
            # Broadcast agent status to all connected clients
            socketio.emit('agent_status', status)
            
        except Exception as e:
            logger.error(f"Error monitoring agents: {e}")
        
        time.sleep(30)  # Check every 30 seconds

def get_project_status(project_id):
    """Get current status of a project"""
    try:
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                """
                SELECT 
                    project_id,
                    status,
                    current_phase,
                    progress,
                    created_at,
                    updated_at
                FROM projects
                WHERE project_id = @project_id
                """,
                params={"project_id": project_id},
                param_types={"project_id": spanner.param_types.STRING}
            )
            
            for row in results:
                return {
                    'project_id': row[0],
                    'status': row[1],
                    'current_phase': row[2],
                    'progress': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'updated_at': row[5].isoformat() if row[5] else None
                }
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        return {'error': str(e)}

# Start background monitoring thread
monitor_thread = Thread(target=monitor_agent_status, daemon=True)
monitor_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)