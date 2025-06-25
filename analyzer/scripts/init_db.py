#!/usr/bin/env python3
"""
Initialize the database with the new schema for rules and rule_chunks tables.
This script drops and recreates the database tables to match the new structure.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_environment():
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    else:
        print("No .env file found, using system environment variables")

def get_database_config():
    """Get database configuration from environment variables."""
    # Try new DB_* format first, then fall back to POSTGRES_* format
    config = {}
    
    # Database host
    config['host'] = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST', 'postgres')
    
    # Database port
    port = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT', '5432')
    config['port'] = int(port)
    
    # Database name
    config['name'] = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB')
    if not config['name']:
        print("❌ Error: Database name not set (DB_NAME or POSTGRES_DB)")
        return None
    
    # Database user
    config['user'] = os.getenv('DB_USER') or os.getenv('POSTGRES_USER')
    if not config['user']:
        print("❌ Error: Database user not set (DB_USER or POSTGRES_USER)")
        return None
    
    # Database password
    config['password'] = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', '')
    
    print(f"Database config: {config['host']}:{config['port']}/{config['name']} as {config['user']}")
    return config

def connect_to_database(config):
    """Establish connection to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['name'],
            user=config['user'],
            password=config['password']
        )
        print("Database connection established successfully")
        return conn
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def initialize_database(conn):
    """Initialize database with new schema."""
    
    # Read the init.sql file
    init_sql_file = project_root / "scripts" / "init.sql"
    
    try:
        with open(init_sql_file, 'r') as f:
            init_sql = f.read()
        
        with conn.cursor() as cur:
            print("Dropping existing tables...")
            # Drop tables in correct order due to foreign key constraints
            cur.execute("DROP TABLE IF EXISTS analysis_results CASCADE;")
            cur.execute("DROP TABLE IF EXISTS rule_chunks CASCADE;")
            cur.execute("DROP TABLE IF EXISTS rules CASCADE;")
            cur.execute("DROP TABLE IF EXISTS legal_rules CASCADE;")  # Old table
            cur.execute("DROP TABLE IF EXISTS document_embeddings CASCADE;")  # Old table
            
            print("Creating new tables with schema...")
            cur.execute(init_sql)
            
            conn.commit()
            print("Database initialized successfully with new schema")
            return True
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        return False

def verify_schema(conn):
    """Verify that the new schema is properly created."""
    try:
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            print(f"\nVerification:")
            print(f"Tables created: {tables}")
            
            # Check indexes
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY indexname;
            """)
            indexes = [row[0] for row in cur.fetchall()]
            
            print(f"Indexes created: {len(indexes)} indexes")
            
            # Check specific expected tables
            expected_tables = ['rules', 'rule_chunks', 'analysis_results']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"WARNING: Missing expected tables: {missing_tables}")
                return False
            else:
                print("✓ All expected tables are present")
                return True
                
    except Exception as e:
        print(f"Error verifying schema: {e}")
        return False

def main():
    try:
        # Load environment
        load_environment()
        
        # Get database configuration
        db_config = get_database_config()
        if not db_config:
            return 1
        
        # Connect to database
        conn = connect_to_database(db_config)
        if not conn:
            return 1
        
        try:
            # Confirm before proceeding
            response = input("\nThis will DROP ALL EXISTING TABLES and recreate them. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                return 0
            
            # Initialize database
            if not initialize_database(conn):
                return 1
            
            # Verify schema
            if not verify_schema(conn):
                return 1
            
            print("\n✓ Database initialization completed successfully!")
            print("\nNext steps:")
            print("1. Run the upload_embeddings.py script to load the chunked dataset")
            print("2. Test the API endpoints to ensure everything works correctly")
            
            return 0
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 