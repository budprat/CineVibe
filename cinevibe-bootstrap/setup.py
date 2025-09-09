"""
Database Setup for CineVibe
Creates Spanner instance and graph database schema for film production
Based on InstaVibe's database setup pattern
"""

import os
import sys
from google.cloud import spanner
from google.cloud.spanner_admin_database_v1 import CreateDatabaseRequest
import time

# Get environment variables
PROJECT_ID = os.environ.get("PROJECT_ID")
INSTANCE_ID = os.environ.get("SPANNER_INSTANCE_ID", "cinevibe-graph-instance")
DATABASE_ID = os.environ.get("SPANNER_DATABASE_ID", "graphdb")
REGION = os.environ.get("REGION", "us-central1")

if not PROJECT_ID:
    print("Error: PROJECT_ID environment variable not set")
    print("Please run: source set_env.sh")
    sys.exit(1)

def create_instance():
    """Create Spanner instance if it doesn't exist"""
    spanner_client = spanner.Client(project=PROJECT_ID)
    
    config_name = f"projects/{PROJECT_ID}/instanceConfigs/regional-{REGION}"
    
    try:
        instance = spanner_client.instance(INSTANCE_ID)
        if instance.exists():
            print(f"✅ Instance {INSTANCE_ID} already exists")
            return instance
        
        print(f"Creating Spanner instance {INSTANCE_ID}...")
        
        instance = spanner_client.instance(
            INSTANCE_ID,
            configuration_name=config_name,
            display_name="CineVibe Graph Instance",
            processing_units=100
        )
        
        operation = instance.create()
        
        print("Waiting for instance creation...")
        operation.result(120)  # Wait up to 120 seconds
        
        print(f"✅ Instance {INSTANCE_ID} created successfully")
        return instance
        
    except Exception as e:
        print(f"Error creating instance: {e}")
        sys.exit(1)

def create_database(instance):
    """Create database with graph schema"""
    
    # DDL statements for CineVibe schema
    ddl_statements = [
        # Character table - stores character profiles
        """CREATE TABLE Character (
            character_id STRING(36) NOT NULL,
            name STRING(100) NOT NULL,
            age INT64,
            physical_description JSON,
            personality_traits ARRAY<STRING(MAX)>,
            visual_dna JSON,
            created_at TIMESTAMP OPTIONS (allow_commit_timestamp=true),
            updated_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
        ) PRIMARY KEY (character_id)""",
        
        # Scene table - stores scene information
        """CREATE TABLE Scene (
            scene_id STRING(36) NOT NULL,
            script_id STRING(36) NOT NULL,
            scene_number INT64 NOT NULL,
            location STRING(200),
            time_of_day STRING(50),
            weather_conditions STRING(100),
            emotional_tone STRING(50),
            description STRING(MAX),
            generated_assets JSON,
            created_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
        ) PRIMARY KEY (scene_id)""",
        
        # Script table - stores screenplay information
        """CREATE TABLE Script (
            script_id STRING(36) NOT NULL,
            title STRING(200),
            author STRING(100),
            genre STRING(50),
            logline STRING(MAX),
            script_content STRING(MAX),
            metadata JSON,
            created_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
        ) PRIMARY KEY (script_id)""",
        
        # GeneratedAsset table - stores AI-generated content
        """CREATE TABLE GeneratedAsset (
            asset_id STRING(36) NOT NULL,
            scene_id STRING(36),
            character_id STRING(36),
            platform STRING(50),
            asset_type STRING(20),
            prompt_used STRING(MAX),
            generation_params JSON,
            file_url STRING(500),
            quality_score FLOAT64,
            consistency_score FLOAT64,
            cost FLOAT64,
            created_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
        ) PRIMARY KEY (asset_id)""",
        
        # Location table - stores unique locations
        """CREATE TABLE Location (
            location_id STRING(36) NOT NULL,
            name STRING(200),
            location_type STRING(50),
            description STRING(MAX),
            visual_references JSON,
            created_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
        ) PRIMARY KEY (location_id)""",
        
        # Prop table - stores prop information
        """CREATE TABLE Prop (
            prop_id STRING(36) NOT NULL,
            name STRING(100),
            description STRING(MAX),
            importance STRING(20),
            scenes_used ARRAY<STRING(36)>,
            created_at TIMESTAMP OPTIONS (allow_commit_timestamp=true)
        ) PRIMARY KEY (prop_id)""",
        
        # Edge Tables for relationships
        
        # CharacterInScene - links characters to scenes
        """CREATE TABLE CharacterInScene (
            character_id STRING(36) NOT NULL,
            scene_id STRING(36) NOT NULL,
            costume_variant STRING(100),
            age_in_scene INT64,
            dialogue_lines INT64,
            screen_time_seconds INT64,
            FOREIGN KEY (character_id) REFERENCES Character (character_id),
            FOREIGN KEY (scene_id) REFERENCES Scene (scene_id)
        ) PRIMARY KEY (character_id, scene_id)""",
        
        # SceneSequence - defines scene order
        """CREATE TABLE SceneSequence (
            from_scene_id STRING(36) NOT NULL,
            to_scene_id STRING(36) NOT NULL,
            transition_type STRING(50),
            continuity_notes STRING(MAX),
            time_gap STRING(100),
            FOREIGN KEY (from_scene_id) REFERENCES Scene (scene_id),
            FOREIGN KEY (to_scene_id) REFERENCES Scene (scene_id)
        ) PRIMARY KEY (from_scene_id, to_scene_id)""",
        
        # CharacterRelationship - relationships between characters
        """CREATE TABLE CharacterRelationship (
            character1_id STRING(36) NOT NULL,
            character2_id STRING(36) NOT NULL,
            relationship_type STRING(50),
            description STRING(MAX),
            FOREIGN KEY (character1_id) REFERENCES Character (character_id),
            FOREIGN KEY (character2_id) REFERENCES Character (character_id)
        ) PRIMARY KEY (character1_id, character2_id)""",
        
        # Note: Property Graph requires ENTERPRISE edition
        # Commented out for STANDARD edition compatibility
        # """CREATE PROPERTY GRAPH CineGraph
        # NODE TABLES (
        #     Character,
        #     Scene,
        #     Location,
        #     Prop,
        #     GeneratedAsset
        # )
        # EDGE TABLES (
        #     CharacterInScene
        #         SOURCE KEY (character_id) REFERENCES Character (character_id)
        #         DESTINATION KEY (scene_id) REFERENCES Scene (scene_id)
        #         LABEL AppearsIn,
        #     SceneSequence
        #         SOURCE KEY (from_scene_id) REFERENCES Scene (scene_id)
        #         DESTINATION KEY (to_scene_id) REFERENCES Scene (scene_id)
        #         LABEL FollowedBy,
        #     CharacterRelationship
        #         SOURCE KEY (character1_id) REFERENCES Character (character_id)
        #         DESTINATION KEY (character2_id) REFERENCES Character (character_id)
        #         LABEL RelatedTo
        # )"""
    ]
    
    try:
        database = instance.database(DATABASE_ID)
        
        if database.exists():
            print(f"✅ Database {DATABASE_ID} already exists")
            return database
        
        print(f"Creating database {DATABASE_ID} with schema...")
        
        # Create database with DDL statements
        operation = instance.database(
            DATABASE_ID,
            ddl_statements=ddl_statements
        ).create()
        
        print("Waiting for database creation...")
        operation.result(120)  # Wait up to 120 seconds
        
        print(f"✅ Database {DATABASE_ID} created successfully")
        return database
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def insert_sample_data(database):
    """Insert sample data for testing"""
    
    print("Inserting sample data...")
    
    with database.batch() as batch:
        # Insert a sample script
        batch.insert(
            table="Script",
            columns=["script_id", "title", "author", "genre", "logline"],
            values=[
                ("script_001", "The Last Coffee", "CineVibe Demo", "Drama",
                 "A woman discovers life's meaning in her last cup of coffee")
            ]
        )
        
        # Insert sample characters
        batch.insert(
            table="Character",
            columns=["character_id", "name", "age", "physical_description"],
            values=[
                ("char_sarah_001", "SARAH", 28, 
                 '{"hair": "brown", "eyes": "green", "height": "5ft 6in"}'),
                ("char_barista_001", "BARISTA", 22,
                 '{"hair": "black", "eyes": "brown", "height": "5ft 10in"}')
            ]
        )
        
        # Insert sample scenes
        batch.insert(
            table="Scene",
            columns=["scene_id", "script_id", "scene_number", "location", "time_of_day"],
            values=[
                ("scene_001", "script_001", 1, "COFFEE SHOP", "DAY"),
                ("scene_002", "script_001", 2, "STREET", "DAY"),
                ("scene_003", "script_001", 3, "COFFEE SHOP", "SUNSET")
            ]
        )
        
        # Link characters to scenes
        batch.insert(
            table="CharacterInScene",
            columns=["character_id", "scene_id", "dialogue_lines"],
            values=[
                ("char_sarah_001", "scene_001", 5),
                ("char_barista_001", "scene_001", 3),
                ("char_sarah_001", "scene_002", 2),
                ("char_sarah_001", "scene_003", 8),
                ("char_barista_001", "scene_003", 4)
            ]
        )
        
        # Create scene sequence
        batch.insert(
            table="SceneSequence",
            columns=["from_scene_id", "to_scene_id", "transition_type"],
            values=[
                ("scene_001", "scene_002", "CUT TO"),
                ("scene_002", "scene_003", "DISSOLVE TO")
            ]
        )
    
    print("✅ Sample data inserted")

def test_graph_queries(database):
    """Test relational queries (Graph queries require ENTERPRISE edition)"""
    
    print("\nTesting relational queries...")
    
    # Query 1: Find all characters in a scene using JOIN
    query1 = """
    SELECT c.name AS character_name, s.location AS scene_location
    FROM Character c
    JOIN CharacterInScene cis ON c.character_id = cis.character_id
    JOIN Scene s ON cis.scene_id = s.scene_id
    WHERE s.scene_id = @scene_id
    """
    
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(
            query1,
            params={"scene_id": "scene_001"},
            param_types={"scene_id": spanner.param_types.STRING}
        )
        
        print("\nCharacters in Scene 1:")
        for row in results:
            print(f"  - {row[0]} appears in {row[1]}")
    
    # Query 2: Find scene sequence using JOIN
    query2 = """
    SELECT s1.scene_number AS from_scene, s2.scene_number AS to_scene
    FROM Scene s1
    JOIN SceneSequence ss ON s1.scene_id = ss.from_scene_id
    JOIN Scene s2 ON ss.to_scene_id = s2.scene_id
    """
    
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(query2)
        
        print("\nScene Sequence:")
        for row in results:
            print(f"  - Scene {row[0]} → Scene {row[1]}")
    
    print("\n✅ Relational queries successful")

def main():
    """Main setup function"""
    print("=" * 50)
    print("CineVibe Database Setup")
    print("=" * 50)
    print()
    
    print(f"Project ID: {PROJECT_ID}")
    print(f"Instance ID: {INSTANCE_ID}")
    print(f"Database ID: {DATABASE_ID}")
    print(f"Region: {REGION}")
    print()
    
    # Create Spanner instance
    instance = create_instance()
    
    # Create database with schema
    database = create_database(instance)
    
    # Insert sample data
    insert_sample_data(database)
    
    # Test graph queries
    test_graph_queries(database)
    
    print("\n" + "=" * 50)
    print("✅ CineVibe database setup complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()