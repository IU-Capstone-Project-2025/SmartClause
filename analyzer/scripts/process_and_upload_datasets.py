#!/usr/bin/env python3
"""
Unified script to process and upload legal datasets to PostgreSQL database.

This script handles:
1. Loading rules dataset (dataset_codes_rf.csv) 
2. Loading chunks dataset (dataset_codes_rf_chunking_800chunksize_500overlap.csv)
3. Optionally generating embeddings for chunks
4. Uploading both rules and chunks with embeddings to database

Expected file naming convention in project root datasets/ directory:
- datasets/rules_dataset.csv (or dataset_codes_rf.csv)
- datasets/chunks_dataset.csv (or dataset_codes_rf_chunking_800chunksize_500overlap.csv)
- datasets/chunks_with_embeddings.csv (generated output with embeddings)
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_environment():
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
    else:
        print("⚠ No .env file found, using system environment variables")

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
    
    print(f"✓ Database config: {config['host']}:{config['port']}/{config['name']} as {config['user']}")
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
        print("✓ Database connection established successfully")
        return conn
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def find_dataset_files(script_dir):
    """Find and validate dataset files in the script directory and datasets subdirectory."""
    files = {}
    local_datasets_dir = script_dir / "datasets"
    
    # Also check project root datasets directory (for Docker mounting)
    project_root = script_dir.parent.parent
    root_datasets_dir = project_root / "datasets"
    
    # Look for rules dataset
    rules_candidates = [
        root_datasets_dir / "rules_dataset.csv",
        root_datasets_dir / "dataset_codes_rf.csv",
        local_datasets_dir / "rules_dataset.csv",
        local_datasets_dir / "dataset_codes_rf.csv",
        script_dir / "rules_dataset.csv",
        script_dir / "dataset_codes_rf.csv"
    ]
    
    for candidate in rules_candidates:
        if candidate.exists():
            files['rules'] = candidate
            break
    
    # Look for chunks dataset  
    chunks_candidates = [
        root_datasets_dir / "chunks_dataset.csv",
        root_datasets_dir / "dataset_codes_rf_chunking_800chunksize_500overlap.csv",
        local_datasets_dir / "chunks_dataset.csv",
        local_datasets_dir / "dataset_codes_rf_chunking_800chunksize_500overlap.csv",
        script_dir / "chunks_dataset.csv",
        script_dir / "dataset_codes_rf_chunking_800chunksize_500overlap.csv"
    ]
    
    for candidate in chunks_candidates:
        if candidate.exists():
            files['chunks'] = candidate
            break
    
    # Set output file for embeddings (prefer project root datasets directory)
    if root_datasets_dir.exists():
        files['embeddings_output'] = root_datasets_dir / "chunks_with_embeddings.csv"
    elif local_datasets_dir.exists():
        files['embeddings_output'] = local_datasets_dir / "chunks_with_embeddings.csv"
    else:
        files['embeddings_output'] = script_dir / "chunks_with_embeddings.csv"
    
    return files

def validate_dataset_files(files):
    """Validate that required dataset files exist."""
    missing = []
    
    if 'rules' not in files or not files['rules'].exists():
        missing.append("rules dataset (datasets/rules_dataset.csv or datasets/dataset_codes_rf.csv)")
    
    if 'chunks' not in files or not files['chunks'].exists():
        missing.append("chunks dataset (datasets/chunks_dataset.csv or datasets/dataset_codes_rf_chunking_800chunksize_500overlap.csv)")
    
    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")
        return False
    
    print(f"✓ Found rules dataset: {files['rules']}")
    print(f"✓ Found chunks dataset: {files['chunks']}")
    return True

def load_datasets(files):
    """Load and validate both datasets."""
    print("\n📂 Loading datasets...")
    
    try:
        # Load rules dataset
        print(f"Loading rules from {files['rules']}...")
        rules_df = pd.read_csv(files['rules'])
        print(f"✓ Loaded {len(rules_df)} rules")
        print(f"  Columns: {list(rules_df.columns)}")
        
        # Load chunks dataset
        print(f"Loading chunks from {files['chunks']}...")
        chunks_df = pd.read_csv(files['chunks'])
        print(f"✓ Loaded {len(chunks_df)} chunks")
        print(f"  Columns: {list(chunks_df.columns)}")
        
        # Validate required columns
        required_rules_cols = ['rule_id', 'file', 'rule_number', 'rule_title', 'rule_text', 
                              'section_title', 'chapter_title', 'start_char', 'end_char', 'text_length']
        required_chunks_cols = ['chunk_id', 'rule_id', 'chunk_number', 'chunk_text', 
                               'chunk_char_start', 'chunk_char_end']
        
        missing_rules_cols = [col for col in required_rules_cols if col not in rules_df.columns]
        missing_chunks_cols = [col for col in required_chunks_cols if col not in chunks_df.columns]
        
        if missing_rules_cols:
            print(f"❌ Missing required columns in rules dataset: {missing_rules_cols}")
            return None, None
            
        if missing_chunks_cols:
            print(f"❌ Missing required columns in chunks dataset: {missing_chunks_cols}")
            return None, None
        
        # Check if rule_ids match between datasets
        rules_ids = set(rules_df['rule_id'].unique())
        chunks_rule_ids = set(chunks_df['rule_id'].unique())
        
        if not chunks_rule_ids.issubset(rules_ids):
            missing_rules = chunks_rule_ids - rules_ids
            print(f"⚠ Warning: {len(missing_rules)} rule_ids in chunks don't exist in rules dataset")
        
        print(f"✓ Datasets loaded and validated successfully")
        return rules_df, chunks_df
        
    except Exception as e:
        print(f"❌ Error loading datasets: {e}")
        return None, None

def generate_embeddings(chunks_df, embeddings_file):
    """Generate embeddings for chunks using the embedding service."""
    print(f"\n🤖 Generating embeddings...")
    
    try:
        # Import embedding service
        from app.services.embedding_service import embedding_service
        
        embeddings = []
        failed_count = 0
        
        print(f"Processing {len(chunks_df)} chunks...")
        for idx, row in tqdm(chunks_df.iterrows(), total=len(chunks_df), desc="Generating embeddings"):
            try:
                chunk_text = str(row['chunk_text']) if pd.notna(row['chunk_text']) else ""
                if not chunk_text.strip():
                    embeddings.append(None)
                    failed_count += 1
                    continue
                
                # Generate embedding
                embedding = embedding_service.encode_to_list(chunk_text)
                embeddings.append(json.dumps(embedding))
                
            except Exception as e:
                print(f"Error generating embedding for chunk {idx}: {e}")
                embeddings.append(None)
                failed_count += 1
        
        # Add embeddings to dataframe
        chunks_with_embeddings = chunks_df.copy()
        chunks_with_embeddings['embedding'] = embeddings
        
        # Save to file
        print(f"💾 Saving chunks with embeddings to {embeddings_file}...")
        chunks_with_embeddings.to_csv(embeddings_file, index=False)
        
        print(f"✓ Generated embeddings for {len(embeddings) - failed_count}/{len(chunks_df)} chunks")
        if failed_count > 0:
            print(f"⚠ Failed to generate {failed_count} embeddings")
        
        return chunks_with_embeddings
        
    except ImportError as e:
        print(f"❌ Error importing embedding service: {e}")
        print("Make sure you're running from the analyzer directory")
        return None
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        return None

def load_embeddings(embeddings_file):
    """Load pre-generated embeddings from file."""
    try:
        print(f"📂 Loading embeddings from {embeddings_file}...")
        chunks_with_embeddings = pd.read_csv(embeddings_file)
        
        # Validate embedding column exists
        if 'embedding' not in chunks_with_embeddings.columns:
            print(f"❌ No 'embedding' column found in {embeddings_file}")
            return None
        
        # Count valid embeddings
        valid_embeddings = chunks_with_embeddings['embedding'].notna().sum()
        print(f"✓ Loaded {len(chunks_with_embeddings)} chunks with {valid_embeddings} valid embeddings")
        
        return chunks_with_embeddings
        
    except Exception as e:
        print(f"❌ Error loading embeddings file: {e}")
        return None

def ensure_database_schema(conn):
    """Ensure the database has the correct schema."""
    schema_sql = """
    -- Enable pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Table for storing legal rules (articles) from Russian legal codes
    CREATE TABLE IF NOT EXISTS rules (
        rule_id SERIAL PRIMARY KEY,
        file VARCHAR(255),
        rule_number INTEGER,
        rule_title TEXT,
        rule_text TEXT,
        section_title TEXT,
        chapter_title TEXT,
        start_char INTEGER,
        end_char INTEGER,
        text_length INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Table for storing rule chunks with embeddings
    CREATE TABLE IF NOT EXISTS rule_chunks (
        chunk_id SERIAL PRIMARY KEY,
        rule_id INTEGER REFERENCES rules(rule_id) ON DELETE CASCADE,
        chunk_number INTEGER,
        chunk_text TEXT,
        chunk_char_start INTEGER,
        chunk_char_end INTEGER,
        embedding vector(1024),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS rules_rule_number_idx ON rules (rule_number);
    CREATE INDEX IF NOT EXISTS rules_file_idx ON rules (file);
    CREATE INDEX IF NOT EXISTS rule_chunks_rule_id_idx ON rule_chunks (rule_id);
    CREATE INDEX IF NOT EXISTS rule_chunks_chunk_number_idx ON rule_chunks (rule_id, chunk_number);
    CREATE INDEX IF NOT EXISTS rule_chunks_embedding_idx ON rule_chunks USING ivfflat (embedding vector_cosine_ops);
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
            print("✓ Database schema verified/created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        conn.rollback()
        return False

def clear_database_tables(conn, confirm=True):
    """Clear existing data from database tables."""
    if confirm:
        response = input("\n⚠ This will DELETE ALL existing data in rules and rule_chunks tables. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Upload cancelled")
            return False
    
    try:
        with conn.cursor() as cur:
            print("🗑 Clearing existing data...")
            cur.execute("DELETE FROM rule_chunks;")
            cur.execute("DELETE FROM rules;")
            cur.execute("ALTER SEQUENCE rule_chunks_chunk_id_seq RESTART WITH 1;")
            cur.execute("ALTER SEQUENCE rules_rule_id_seq RESTART WITH 1;")
            conn.commit()
            print("✓ Existing data cleared successfully")
            return True
    except Exception as e:
        print(f"❌ Error clearing existing data: {e}")
        conn.rollback()
        return False

def upload_rules(conn, rules_df, batch_size=100):
    """Upload rules to database."""
    print(f"\n📤 Uploading {len(rules_df)} rules...")
    
    insert_sql = """
    INSERT INTO rules (
        rule_id, file, rule_number, rule_title, rule_text, 
        section_title, chapter_title, start_char, end_char, text_length
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
    """
    
    try:
        # Prepare data
        rules_data = []
        for _, row in rules_df.iterrows():
            rule_data = (
                int(row['rule_id']),
                str(row['file']) if pd.notna(row['file']) else None,
                int(row['rule_number']) if pd.notna(row['rule_number']) else None,
                str(row['rule_title']) if pd.notna(row['rule_title']) else None,
                str(row['rule_text']) if pd.notna(row['rule_text']) else None,
                str(row['section_title']) if pd.notna(row['section_title']) else None,
                str(row['chapter_title']) if pd.notna(row['chapter_title']) else None,
                int(row['start_char']) if pd.notna(row['start_char']) else None,
                int(row['end_char']) if pd.notna(row['end_char']) else None,
                int(row['text_length']) if pd.notna(row['text_length']) else None,
            )
            rules_data.append(rule_data)
        
        # Insert in batches
        with conn.cursor() as cur:
            for i in tqdm(range(0, len(rules_data), batch_size), desc="Uploading rules"):
                batch = rules_data[i:i + batch_size]
                execute_batch(cur, insert_sql, batch, page_size=batch_size)
                conn.commit()
        
        print(f"✓ Successfully uploaded {len(rules_data)} rules")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading rules: {e}")
        conn.rollback()
        return False

def upload_chunks(conn, chunks_df, batch_size=100):
    """Upload chunks with embeddings to database."""
    print(f"\n📤 Uploading {len(chunks_df)} chunks...")
    
    insert_sql = """
    INSERT INTO rule_chunks (
        chunk_id, rule_id, chunk_number, chunk_text, 
        chunk_char_start, chunk_char_end, embedding
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    );
    """
    
    try:
        # Prepare data
        chunks_data = []
        failed_embeddings = 0
        
        for _, row in chunks_df.iterrows():
            # Convert embedding
            embedding = None
            if 'embedding' in row and pd.notna(row['embedding']):
                try:
                    embedding_list = json.loads(row['embedding'])
                    embedding = embedding_list
                except:
                    failed_embeddings += 1
            else:
                failed_embeddings += 1
            
            chunk_data = (
                int(row['chunk_id']),
                int(row['rule_id']),
                int(row['chunk_number']) if pd.notna(row['chunk_number']) else None,
                str(row['chunk_text']) if pd.notna(row['chunk_text']) else None,
                int(row['chunk_char_start']) if pd.notna(row['chunk_char_start']) else None,
                int(row['chunk_char_end']) if pd.notna(row['chunk_char_end']) else None,
                embedding
            )
            chunks_data.append(chunk_data)
        
        # Insert in batches
        with conn.cursor() as cur:
            for i in tqdm(range(0, len(chunks_data), batch_size), desc="Uploading chunks"):
                batch = chunks_data[i:i + batch_size]
                execute_batch(cur, insert_sql, batch, page_size=batch_size)
                conn.commit()
        
        valid_embeddings = len(chunks_data) - failed_embeddings
        print(f"✓ Successfully uploaded {len(chunks_data)} chunks")
        print(f"  - {valid_embeddings} with valid embeddings")
        print(f"  - {failed_embeddings} without embeddings")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading chunks: {e}")
        conn.rollback()
        return False

def upload_chunks_streaming(conn, embeddings_file, batch_size=100, csv_chunk_size=1000):
    """
    Memory-efficient streaming upload of chunks with embeddings.
    Reads and processes CSV file in chunks to minimize memory usage.
    """
    print(f"\n📤 Streaming upload from {embeddings_file}")
    
    insert_sql = """
    INSERT INTO rule_chunks (
        chunk_id, rule_id, chunk_number, chunk_text, 
        chunk_char_start, chunk_char_end, embedding
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    );
    """
    
    try:
        import gc
        
        print(f"🔧 Using CSV chunk size: {csv_chunk_size} rows")
        print(f"🔧 Database batch size: {batch_size} rows")
        
        total_uploaded = 0
        failed_embeddings = 0
        chunk_count = 0
        
        # Stream the CSV file in chunks
        csv_reader = pd.read_csv(embeddings_file, chunksize=csv_chunk_size)
        
        with conn.cursor() as cur:
            for chunk_df in csv_reader:
                chunk_count += 1
                print(f"📦 Processing CSV chunk {chunk_count} ({len(chunk_df)} rows)...")
                
                # Process this chunk
                batch_data = []
                
                for _, row in chunk_df.iterrows():
                    # Convert embedding
                    embedding = None
                    if 'embedding' in row and pd.notna(row['embedding']):
                        try:
                            embedding_list = json.loads(row['embedding'])
                            embedding = embedding_list
                        except:
                            failed_embeddings += 1
                    else:
                        failed_embeddings += 1
                    
                    chunk_data = (
                        int(row['chunk_id']),
                        int(row['rule_id']),
                        int(row['chunk_number']) if pd.notna(row['chunk_number']) else None,
                        str(row['chunk_text']) if pd.notna(row['chunk_text']) else None,
                        int(row['chunk_char_start']) if pd.notna(row['chunk_char_start']) else None,
                        int(row['chunk_char_end']) if pd.notna(row['chunk_char_end']) else None,
                        embedding
                    )
                    batch_data.append(chunk_data)
                    
                    # Upload in smaller batches to avoid memory buildup
                    if len(batch_data) >= batch_size:
                        execute_batch(cur, insert_sql, batch_data, page_size=batch_size)
                        conn.commit()
                        total_uploaded += len(batch_data)
                        batch_data = []
                        
                        # Force garbage collection
                        gc.collect()
                
                # Upload remaining data in this chunk
                if batch_data:
                    execute_batch(cur, insert_sql, batch_data, page_size=len(batch_data))
                    conn.commit()
                    total_uploaded += len(batch_data)
                
                # Clear chunk from memory and force garbage collection
                del chunk_df
                del batch_data
                gc.collect()
                
                print(f"✓ Completed CSV chunk {chunk_count} (total uploaded: {total_uploaded})")
        
        valid_embeddings = total_uploaded - failed_embeddings
        print(f"✓ Successfully uploaded {total_uploaded} chunks via streaming")
        print(f"  - {valid_embeddings} with valid embeddings")
        print(f"  - {failed_embeddings} without embeddings")
        return True
        
    except Exception as e:
        print(f"❌ Error during streaming upload: {e}")
        conn.rollback()
        return False

def verify_upload(conn):
    """Verify the upload was successful."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Count rules
            cur.execute("SELECT COUNT(*) as count FROM rules;")
            rules_count = cur.fetchone()['count']
            
            # Count chunks
            cur.execute("SELECT COUNT(*) as count FROM rule_chunks;")
            chunks_count = cur.fetchone()['count']
            
            # Count chunks with embeddings
            cur.execute("SELECT COUNT(*) as count FROM rule_chunks WHERE embedding IS NOT NULL;")
            chunks_with_embeddings = cur.fetchone()['count']
            
            # Sample data
            cur.execute("""
                SELECT r.rule_number, r.rule_title, COUNT(rc.chunk_id) as chunk_count
                FROM rules r
                LEFT JOIN rule_chunks rc ON r.rule_id = rc.rule_id
                GROUP BY r.rule_id, r.rule_number, r.rule_title
                ORDER BY r.rule_id
                LIMIT 3;
            """)
            sample_rules = cur.fetchall()
            
            print(f"\n📊 Upload Verification:")
            print(f"  - Rules: {rules_count}")
            print(f"  - Chunks: {chunks_count}")
            print(f"  - Chunks with embeddings: {chunks_with_embeddings}")
            print(f"\n📝 Sample Rules:")
            for rule in sample_rules:
                title = rule['rule_title'][:50] + "..." if rule['rule_title'] and len(rule['rule_title']) > 50 else rule['rule_title']
                print(f"  - Rule {rule['rule_number']}: {title} ({rule['chunk_count']} chunks)")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Process and upload legal rules and chunks datasets with optional embedding generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
File naming conventions in project root datasets/ directory:
  datasets/rules_dataset.csv (or dataset_codes_rf.csv) - Rules dataset
  datasets/chunks_dataset.csv (or dataset_codes_rf_chunking_800chunksize_500overlap.csv) - Chunks dataset  
  datasets/chunks_with_embeddings.csv - Output file with embeddings (generated)

Examples:
  # Load existing embeddings and upload (default streaming)
  python process_and_upload_datasets.py --upload
  
  # Upload with smaller memory usage (for 3GB RAM constraint)
  python process_and_upload_datasets.py --upload --clear --csv-chunk-size 500 --batch-size 50
  
  # Generate new embeddings and upload
  python process_and_upload_datasets.py --generate --upload --clear
  
  # Only generate embeddings (no upload)
  python process_and_upload_datasets.py --generate
        """
    )
    
    parser.add_argument("--generate", action="store_true", 
                       help="Generate embeddings for chunks")
    parser.add_argument("--upload", action="store_true", 
                       help="Upload data to database")
    parser.add_argument("--clear", action="store_true", 
                       help="Clear existing database data before upload")
    parser.add_argument("--batch-size", type=int, default=100, 
                       help="Batch size for database operations")
    parser.add_argument("--csv-chunk-size", type=int, default=1000,
                       help="Number of rows to read from CSV at once (default: 1000)")
    parser.add_argument("--stream", action="store_true", default=True,
                       help="Use memory-efficient streaming upload (default: True)")
    parser.add_argument("--no-stream", action="store_true",
                       help="Disable streaming and load all data into memory")
    parser.add_argument("--no-confirm", action="store_true", 
                       help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    if not args.generate and not args.upload:
        print("❌ Please specify --generate and/or --upload")
        return 1
    
    try:
        # Setup
        script_dir = Path(__file__).parent
        load_environment()
        
        # Find and validate dataset files
        print("🔍 Searching for dataset files...")
        files = find_dataset_files(script_dir)
        if not validate_dataset_files(files):
            return 1
        
        # Load datasets
        rules_df, chunks_df = load_datasets(files)
        if rules_df is None or chunks_df is None:
            return 1
        
        # Handle embeddings
        if args.generate:
            # Generate new embeddings
            chunks_with_embeddings = generate_embeddings(chunks_df, files['embeddings_output'])
            if chunks_with_embeddings is None:
                return 1
        elif args.upload:
            # For upload, we don't need to load the embeddings into memory
            # We'll stream directly from the CSV file
            if not files['embeddings_output'].exists():
                print(f"❌ No embeddings file found at {files['embeddings_output']}")
                print("Use --generate flag to create embeddings first")
                return 1
            
            print(f"✓ Found embeddings file: {files['embeddings_output']}")
            # Clear chunks_df from memory since we'll stream from file
            del chunks_df
            import gc
            gc.collect()
        
        # Upload to database if requested
        if args.upload:
            print(f"\n🔗 Connecting to database...")
            db_config = get_database_config()
            if not db_config:
                return 1
            
            conn = connect_to_database(db_config)
            if not conn:
                return 1
            
            try:
                # Setup database schema
                if not ensure_database_schema(conn):
                    return 1
                
                # Clear existing data if requested
                if args.clear:
                    if not clear_database_tables(conn, confirm=not args.no_confirm):
                        return 1
                
                # Upload rules
                if not upload_rules(conn, rules_df, args.batch_size):
                    return 1
                
                # Upload chunks 
                use_streaming = not args.no_stream
                if use_streaming:
                    print(f"🔄 Using memory-efficient streaming upload")
                    if not upload_chunks_streaming(conn, files['embeddings_output'], args.batch_size, args.csv_chunk_size):
                        return 1
                else:
                    print(f"🔄 Using traditional in-memory upload")
                    # Load embeddings for traditional approach
                    chunks_with_embeddings = load_embeddings(files['embeddings_output'])
                    if chunks_with_embeddings is None:
                        return 1
                    if not upload_chunks(conn, chunks_with_embeddings, args.batch_size):
                        return 1
                
                # Verify upload
                if not verify_upload(conn):
                    return 1
                
                print(f"\n🎉 Upload completed successfully!")
                
            finally:
                conn.close()
        
        print(f"\n✅ Process completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 