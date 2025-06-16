#!/usr/bin/env python3
"""
Convenient wrapper script for managing legal rules embeddings.
This script provides easy commands to generate embeddings locally 
and upload them to PostgreSQL database.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent.parent)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running {description}: {e}")
        return False

def generate_embeddings(args):
    """Generate embeddings from the dataset."""
    cmd = [sys.executable, "scripts/generate_embeddings.py"]
    
    if args.model:
        cmd.extend(["--model", args.model])
    if hasattr(args, 'batch_size') and args.batch_size:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if hasattr(args, 'max_rows') and args.max_rows:
        cmd.extend(["--max-rows", str(args.max_rows)])
    if hasattr(args, 'force_cpu') and args.force_cpu:
        cmd.append("--force-cpu")
    if hasattr(args, 'device') and args.device:
        cmd.extend(["--device", args.device])
    
    return run_command(cmd, "Generating embeddings")

def upload_embeddings(args):
    """Upload embeddings to PostgreSQL."""
    cmd = [sys.executable, "scripts/upload_embeddings.py"]
    
    if args.csv_file:
        cmd.extend(["--csv-file", args.csv_file])
    if args.batch_size:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if args.clear_existing:
        cmd.append("--clear-existing")
    if args.no_confirm:
        cmd.append("--no-confirm")
    
    return run_command(cmd, "Uploading embeddings to database")

def setup_database():
    """Setup database schema using init.sql."""
    cmd = ["psql", "-f", "scripts/init.sql"]
    return run_command(cmd, "Setting up database schema")

def check_files():
    """Check if required files exist."""
    analyzer_dir = Path(__file__).parent.parent
    project_root = analyzer_dir.parent
    
    # Check source dataset
    source_csv = project_root / "parser" / "dataset" / "dataset_gk_rf.csv"
    embeddings_csv = analyzer_dir / "scripts" / "legal_rules_with_embeddings.csv"
    
    print("\n📁 File Status Check:")
    print(f"Source dataset: {source_csv}")
    print(f"  {'✅ EXISTS' if source_csv.exists() else '❌ NOT FOUND'}")
    
    print(f"Embeddings file: {embeddings_csv}")
    print(f"  {'✅ EXISTS' if embeddings_csv.exists() else '❌ NOT FOUND'}")
    
    if embeddings_csv.exists():
        size_mb = embeddings_csv.stat().st_size / (1024 * 1024)
        print(f"  Size: {size_mb:.2f} MB")

def show_workflow():
    """Show the recommended workflow."""
    print("""
🚀 Legal Rules Embeddings Management Workflow:

1. FIRST TIME SETUP (RUN ONCE):
   python scripts/manage_embeddings.py generate --max-rows 100  # Test with small dataset
   python scripts/manage_embeddings.py upload --clear-existing   # Upload test data
   
2. FULL DATASET (PRODUCTION):
   python scripts/manage_embeddings.py generate                 # Generate all embeddings
   python scripts/manage_embeddings.py upload --clear-existing  # Upload to database
   
3. UPDATING DATA:
   python scripts/manage_embeddings.py generate                 # Regenerate embeddings
   python scripts/manage_embeddings.py upload --clear-existing  # Replace database data

📋 ENVIRONMENT SETUP:
   Make sure these environment variables are set:
   - POSTGRES_HOST (default: localhost)
   - POSTGRES_DB (default: smartclause)  
   - POSTGRES_USER (default: postgres)
   - POSTGRES_PASSWORD (if needed)
   - POSTGRES_PORT (default: 5432)

💡 TIPS:
   - First run with --max-rows 10 to test everything works
   - Embeddings generation can take 30+ minutes for full dataset
   - Generated embeddings file can be committed to Git
   - Other team members can skip generation and just upload
   - Use --clear-existing to replace existing data
   
🔧 MEMORY ISSUES (Apple Silicon):
   - If you get "MPS backend out of memory" error:
     python scripts/manage_embeddings.py generate --force-cpu
   - Or use smaller batch size:
     python scripts/manage_embeddings.py generate --batch-size 4
   - The script will auto-detect and suggest optimal settings
""")

def main():
    parser = argparse.ArgumentParser(description="Manage legal rules embeddings")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate embeddings from dataset')
    gen_parser.add_argument('--model', default='BAAI/bge-m3', help='Embedding model to use')
    gen_parser.add_argument('--batch-size', type=int, help='Batch size for embedding generation (auto-detected if not specified)')
    gen_parser.add_argument('--max-rows', type=int, help='Maximum rows to process (for testing)')
    gen_parser.add_argument('--force-cpu', action='store_true', help='Force CPU usage even if GPU is available')
    gen_parser.add_argument('--device', choices=['cpu', 'cuda', 'mps'], help='Force specific device')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload embeddings to PostgreSQL')
    upload_parser.add_argument('--csv-file', help='Path to CSV file with embeddings')
    upload_parser.add_argument('--batch-size', type=int, default=100, help='Batch size for database insertion')
    upload_parser.add_argument('--clear-existing', action='store_true', help='Clear existing data before upload')
    upload_parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompts')
    
    # Full workflow command
    full_parser = subparsers.add_parser('full', help='Run full workflow: generate + upload')
    full_parser.add_argument('--model', default='BAAI/bge-m3', help='Embedding model to use')
    full_parser.add_argument('--max-rows', type=int, help='Maximum rows to process (for testing)')
    full_parser.add_argument('--clear-existing', action='store_true', help='Clear existing data before upload')
    full_parser.add_argument('--force-cpu', action='store_true', help='Force CPU usage even if GPU is available')
    full_parser.add_argument('--device', choices=['cpu', 'cuda', 'mps'], help='Force specific device')
    
    # Utility commands
    subparsers.add_parser('check', help='Check file status')
    subparsers.add_parser('workflow', help='Show recommended workflow')
    subparsers.add_parser('setup-db', help='Setup database schema')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        show_workflow()
        return 0
    
    if args.command == 'generate':
        success = generate_embeddings(args)
        if success:
            print("\n🎉 Embeddings generated successfully!")
            print("📤 You can now commit the embeddings file to Git")
            print("⬆️  Run 'upload' command to load into database")
        return 0 if success else 1
        
    elif args.command == 'upload':
        success = upload_embeddings(args)
        if success:
            print("\n🎉 Embeddings uploaded successfully!")
            print("✅ Your PostgreSQL database is ready for RAG queries")
        return 0 if success else 1
        
    elif args.command == 'full':
        print("🚀 Running full workflow: generate embeddings + upload to database")
        
        # Generate embeddings
        gen_args = argparse.Namespace(
            model=args.model,
            batch_size=None,  # Let auto-detection handle it
            max_rows=args.max_rows,
            force_cpu=getattr(args, 'force_cpu', False),
            device=getattr(args, 'device', None)
        )
        if not generate_embeddings(gen_args):
            return 1
        
        # Upload embeddings
        upload_args = argparse.Namespace(
            csv_file=None,
            batch_size=100,
            clear_existing=args.clear_existing,
            no_confirm=True  # Don't ask for confirmation in full workflow
        )
        if not upload_embeddings(upload_args):
            return 1
            
        print("\n🎉 Full workflow completed successfully!")
        print("✅ Your PostgreSQL database is ready for RAG queries")
        return 0
        
    elif args.command == 'check':
        check_files()
        return 0
        
    elif args.command == 'workflow':
        show_workflow()
        return 0
        
    elif args.command == 'setup-db':
        success = setup_database()
        return 0 if success else 1
        
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 