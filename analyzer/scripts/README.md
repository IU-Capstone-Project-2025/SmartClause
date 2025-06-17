# Legal Rules Embeddings Management

This directory contains scripts for generating and managing embeddings for legal rules from the Civil Code dataset.

## Overview

The embedding management system consists of three main scripts:

1. **`generate_embeddings.py`** - Generates embeddings from the source dataset
2. **`upload_embeddings.py`** - Uploads embeddings to PostgreSQL database 
3. **`manage_embeddings.py`** - Convenient wrapper for common operations

## Quick Start

### 1. Environment Setup

Make sure you have the required environment variables set:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_DB=smartclause_analyzer
export POSTGRES_USER=smartclause
export POSTGRES_PASSWORD=smartclause
export POSTGRES_PORT=5432
```

You can also create a `.env` file in the analyzer directory with these variables.

### 2. Test with Small Dataset

```bash
# Test with 10 rows first
python scripts/manage_embeddings.py generate --max-rows 10

# Upload test data to database
python scripts/manage_embeddings.py upload --clear-existing
```

### 3. Full Dataset Processing

```bash
# Generate embeddings for full dataset
python scripts/manage_embeddings.py generate

# Upload to database
python scripts/manage_embeddings.py upload --clear-existing
```

### 4. One-Command Workflow

```bash
# Do everything in one command
python scripts/manage_embeddings.py full --clear-existing
```

## Individual Scripts

### Generate Embeddings

```bash
python scripts/generate_embeddings.py [OPTIONS]
```

**Options:**
- `--model` - Embedding model to use (default: BAAI/bge-m3)
- `--batch-size` - Batch size for processing (default: 32)
- `--max-rows` - Limit rows for testing (optional)

**Example:**
```bash
python scripts/generate_embeddings.py --model BAAI/bge-m3 --batch-size 16 --max-rows 100
```

### Upload Embeddings

```bash
python scripts/upload_embeddings.py [OPTIONS]
```

**Options:**
- `--csv-file` - Path to embeddings CSV (default: auto-detect)
- `--batch-size` - Database insertion batch size (default: 100)
- `--clear-existing` - Clear existing data before upload
- `--no-confirm` - Skip confirmation prompts

**Example:**
```bash
python scripts/upload_embeddings.py --clear-existing --batch-size 50
```

### Management Wrapper

```bash
python scripts/manage_embeddings.py COMMAND [OPTIONS]
```

**Commands:**
- `generate` - Generate embeddings from dataset
- `upload` - Upload embeddings to database
- `full` - Run complete workflow
- `check` - Check file status
- `workflow` - Show recommended workflow
- `setup-db` - Setup database schema

## Files Created

The scripts create the following files:

- `legal_rules_with_embeddings.csv` - Dataset with generated embeddings (can be large!)
- This file can be committed to Git for sharing across team

## Database Schema

The scripts work with the `legal_rules` table:

```sql
CREATE TABLE legal_rules (
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
    embedding vector(1024),  -- BGE-M3 embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Workflow for Team

### First Person (generates embeddings):
1. Run `python scripts/manage_embeddings.py generate`
2. Commit `legal_rules_with_embeddings.csv` to Git
3. Push to repository

### Other Team Members:
1. Pull latest code (includes embeddings CSV)
2. Set up database environment variables
3. Run `python scripts/manage_embeddings.py upload --clear-existing`
4. Ready to use!

## Troubleshooting

### Common Issues

**"Model not found" error:**
```bash
# Download model manually
python scripts/init_model.py
```

**Database connection error:**
- Check environment variables
- Ensure PostgreSQL is running
- Verify database exists

**Out of memory during embedding generation:**
- The script now auto-detects optimal batch sizes for your device
- For Apple Silicon (MPS) memory issues, try:
  ```bash
  python scripts/generate_embeddings.py --force-cpu
  # or
  python scripts/generate_embeddings.py --batch-size 4
  ```
- Use `--max-rows` for testing
- The script will automatically fall back to CPU if GPU runs out of memory

**Large CSV file:**
- The embeddings file can be 50+ MB
- Consider using Git LFS for large files
- Alternatively, store embeddings in cloud storage

### Performance Tips

- Use GPU if available for faster embedding generation
- Adjust batch sizes based on available memory
- Process in chunks for very large datasets

## Development

To add new embedding models:
1. Update model name in `generate_embeddings.py`
2. Ensure dimension matches in database schema
3. Test with small dataset first 