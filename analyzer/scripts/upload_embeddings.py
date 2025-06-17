#!/usr/bin/env python3
"""
Script to upload legal rules with embeddings to PostgreSQL.
This script reads the CSV file with pre-generated embeddings
and uploads the data to the PostgreSQL database.
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from pathlib import Path
import argparse
from tqdm import tqdm
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file if it exists."""
    # Look for .env file in analyzer directory
    analyzer_dir = Path(__file__).parent.parent
    env_file = analyzer_dir / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from: {env_file}")
    else:
        print("No .env file found, using system environment variables")

def get_database_config():
    """Get database configuration from environment variables."""
    config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'smartclause_analyzer'),
        'user': os.getenv('POSTGRES_USER', 'smartclause'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
    }
    
    # Check if all required config is present
    if not all([config['host'], config['database'], config['user']]):
        print("Error: Missing required database configuration")
        print("Required environment variables: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER")
        print("Optional: POSTGRES_PORT (default: 5432), POSTGRES_PASSWORD")
        return None
    
    return config

def connect_to_database(config):
    """Connect to PostgreSQL database."""
    try:
        print(f"Connecting to database: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
        
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        print("Database connection successful")
        return conn
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def ensure_table_exists(conn):
    """Ensure the legal_rules table exists with the correct schema."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS legal_rules (
        id SERIAL PRIMARY KEY,
        file_name VARCHAR(255),
        rule_number INTEGER,
        rule_title TEXT,
        rule_text TEXT,
        section_title TEXT,
        chapter_title TEXT,
        start_char INTEGER,
        end_char INTEGER,
        text_length INTEGER,
        embedding vector(1024),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(create_table_sql)
            conn.commit()
            print("Table legal_rules verified/created successfully")
            return True
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        return False

def clear_existing_data(conn, confirm=True):
    """Clear existing data from legal_rules table."""
    if confirm:
        response = input("This will delete all existing data in legal_rules table. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Upload cancelled")
            return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM legal_rules;")
            cur.execute("ALTER SEQUENCE legal_rules_id_seq RESTART WITH 1;")
            conn.commit()
            print("Existing data cleared successfully")
            return True
    except Exception as e:
        print(f"Error clearing existing data: {e}")
        conn.rollback()
        return False

def convert_embedding_from_json(embedding_json):
    """Convert JSON string back to numpy array."""
    try:
        embedding_list = json.loads(embedding_json)
        return np.array(embedding_list, dtype=np.float32)
    except Exception as e:
        print(f"Error converting embedding: {e}")
        return None

def prepare_data_for_insert(df):
    """Prepare data for database insertion."""
    print("Preparing data for database insertion...")
    
    prepared_data = []
    failed_conversions = 0
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Preparing data"):
        try:
            # Convert embedding from JSON
            embedding = convert_embedding_from_json(row['embedding'])
            if embedding is None:
                failed_conversions += 1
                continue
            
            # Prepare row data
            row_data = (
                str(row['file']) if pd.notna(row['file']) else None,
                int(row['rule_number']) if pd.notna(row['rule_number']) else None,
                str(row['rule_title']) if pd.notna(row['rule_title']) else None,
                str(row['rule_text']) if pd.notna(row['rule_text']) else None,
                str(row['section_title']) if pd.notna(row['section_title']) else None,
                str(row['chapter_title']) if pd.notna(row['chapter_title']) else None,
                int(row['start_char']) if pd.notna(row['start_char']) else None,
                int(row['end_char']) if pd.notna(row['end_char']) else None,
                int(row['text_length']) if pd.notna(row['text_length']) else None,
                embedding.tolist()  # Convert to list for psycopg2
            )
            
            prepared_data.append(row_data)
            
        except Exception as e:
            print(f"Error preparing row {idx}: {e}")
            failed_conversions += 1
    
    if failed_conversions > 0:
        print(f"Warning: {failed_conversions} rows failed conversion")
    
    print(f"Prepared {len(prepared_data)} rows for insertion")
    return prepared_data

def insert_data_batch(conn, data, batch_size=100):
    """Insert data into database in batches."""
    insert_sql = """
    INSERT INTO legal_rules (
        file_name, rule_number, rule_title, rule_text, 
        section_title, chapter_title, start_char, end_char, 
        text_length, embedding
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
    """
    
    try:
        with conn.cursor() as cur:
            print(f"Inserting {len(data)} rows in batches of {batch_size}...")
            
            # Insert in batches
            for i in tqdm(range(0, len(data), batch_size), desc="Inserting batches"):
                batch = data[i:i + batch_size]
                execute_batch(cur, insert_sql, batch, page_size=batch_size)
                conn.commit()
            
            print("Data insertion completed successfully")
            return True
            
    except Exception as e:
        print(f"Error inserting data: {e}")
        conn.rollback()
        return False

def verify_insertion(conn):
    """Verify the data was inserted correctly."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Count total rows
            cur.execute("SELECT COUNT(*) as count FROM legal_rules;")
            total_count = cur.fetchone()['count']
            
            # Get sample data
            cur.execute("""
                SELECT rule_number, rule_title, text_length, 
                       array_length(embedding, 1) as embedding_dim
                FROM legal_rules 
                LIMIT 5;
            """)
            sample_data = cur.fetchall()
            
            print(f"\nVerification results:")
            print(f"Total rows inserted: {total_count}")
            print(f"Sample data:")
            for row in sample_data:
                print(f"  Rule {row['rule_number']}: {row['rule_title'][:50]}... (embedding dim: {row['embedding_dim']})")
            
            return True
            
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Upload legal rules with embeddings to PostgreSQL")
    parser.add_argument("--csv-file", help="Path to CSV file with embeddings (default: scripts/legal_rules_with_embeddings.csv)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for database insertion")
    parser.add_argument("--clear-existing", action="store_true", help="Clear existing data before upload")
    parser.add_argument("--no-confirm", action="store_true", help="Don't ask for confirmation before clearing data")
    
    args = parser.parse_args()
    
    try:
        # Load environment
        load_environment()
        
        # Setup paths
        analyzer_dir = Path(__file__).parent.parent
        if args.csv_file:
            csv_file = Path(args.csv_file)
        else:
            csv_file = analyzer_dir / "scripts" / "legal_rules_with_embeddings.csv"
        
        print(f"CSV file: {csv_file}")
        
        # Check if CSV file exists
        if not csv_file.exists():
            print(f"Error: CSV file {csv_file} does not exist!")
            print("Run generate_embeddings.py first to create the embeddings file.")
            return 1
        
        # Get database configuration
        db_config = get_database_config()
        if not db_config:
            return 1
        
        # Connect to database
        conn = connect_to_database(db_config)
        if not conn:
            return 1
        
        try:
            # Ensure table exists
            if not ensure_table_exists(conn):
                return 1
            
            # Clear existing data if requested
            if args.clear_existing:
                if not clear_existing_data(conn, confirm=not args.no_confirm):
                    return 1
            
            # Load CSV data
            print("Loading CSV data...")
            df = pd.read_csv(csv_file)
            print(f"Loaded {len(df)} rows from CSV")
            
            # Verify embeddings column exists
            if 'embedding' not in df.columns:
                print("Error: 'embedding' column not found in CSV file")
                return 1
            
            # Prepare data for insertion
            prepared_data = prepare_data_for_insert(df)
            if not prepared_data:
                print("No data to insert")
                return 1
            
            # Insert data
            if not insert_data_batch(conn, prepared_data, args.batch_size):
                return 1
            
            # Verify insertion
            verify_insertion(conn)
            
            print(f"\nUpload completed successfully!")
            print(f"Uploaded {len(prepared_data)} legal rules with embeddings to PostgreSQL")
            
            return 0
            
        finally:
            conn.close()
            
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 