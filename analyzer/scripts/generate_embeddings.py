#!/usr/bin/env python3
"""
Script to generate embeddings for legal rules dataset.
This script reads the dataset from parser/dataset/dataset_codes_rf.csv,
generates embeddings for rule_text using BGE-M3 model,
and saves the results to a CSV file that can be committed to Git.

OPTIMIZED VERSION - Fixes MPS memory leaks with:
- Streaming CSV processing to avoid loading all data in memory
- Aggressive memory cleanup between batches
- Proper garbage collection
- Progressive saving to avoid data loss
"""

import os
import sys
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
from tqdm import tqdm
import argparse
import torch
import gc
import tempfile
import time

def setup_paths():
    """Setup paths relative to the analyzer directory."""
    # Get the analyzer directory (parent of scripts)
    analyzer_dir = Path(__file__).parent.parent
    project_root = analyzer_dir.parent
    
    # Paths for input and output
    input_csv = project_root / "parser" / "dataset" / "dataset_codes_rf.csv"
    output_csv = analyzer_dir / "scripts" / "legal_rules_with_embeddings.csv"
    
    return input_csv, output_csv

def detect_device():
    """Detect the best available device and suggest appropriate batch size."""
    if torch.cuda.is_available():
        device = "cuda"
        suggested_batch_size = 16
        print("🚀 CUDA GPU detected")
    elif torch.backends.mps.is_available():
        device = "mps"
        suggested_batch_size = 2  # Very conservative for MPS to prevent memory issues
        print("🍎 Apple Silicon MPS detected")
        print("⚠️  Using conservative batch size for MPS memory stability")
    else:
        device = "cpu"
        suggested_batch_size = 4  # Even smaller for CPU
        print("💻 Using CPU")
    
    print(f"📊 Suggested batch size for {device.upper()}: {suggested_batch_size}")
    return device, suggested_batch_size

def load_embedding_model(model_name="BAAI/bge-m3", device=None, force_cpu=False):
    """Load the embedding model with appropriate device settings."""
    print(f"Loading embedding model: {model_name}")
    
    if force_cpu:
        device = "cpu"
        print("⚠️  Forcing CPU usage")
    elif device is None:
        device, _ = detect_device()
    
    try:
        # Load model
        model = SentenceTransformer(model_name, device=device)
        
        # Test with a small example to verify it works
        test_text = "This is a test sentence."
        test_embedding = model.encode([test_text], show_progress_bar=False)
        
        print(f"✅ Model loaded successfully on {device.upper()}")
        print(f"📏 Embedding dimension: {model.get_sentence_embedding_dimension()}")
        return model
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "mps" in str(e).lower():
            print(f"⚠️  GPU memory error: {e}")
            print("🔄 Falling back to CPU...")
            try:
                model = SentenceTransformer(model_name, device="cpu")
                test_embedding = model.encode([test_text], show_progress_bar=False)
                print("✅ Model loaded successfully on CPU")
                print(f"📏 Embedding dimension: {model.get_sentence_embedding_dimension()}")
                return model
            except Exception as cpu_e:
                print(f"❌ CPU fallback failed: {cpu_e}")
                raise
        else:
            raise
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise

def clean_text(text):
    """Clean and prepare text for embedding."""
    if pd.isna(text) or text is None:
        return ""
    
    # Convert to string and clean
    text = str(text).strip()
    
    # Remove excessive whitespace and newlines
    text = " ".join(text.split())
    
    return text

def aggressive_memory_cleanup():
    """Perform aggressive memory cleanup for MPS/GPU."""
    # Force garbage collection
    gc.collect()
    
    # Clear GPU caches
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()  # Wait for GPU operations to complete
    elif torch.backends.mps.is_available():
        torch.mps.empty_cache()
        # Add a small delay to ensure MPS cleanup completes
        time.sleep(0.1)

def process_single_batch(model, texts, device_type="cpu"):
    """Process a single batch with proper error handling and memory management."""
    try:
        # Convert texts to embeddings
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for better similarity search
        )
        
        # Immediately cleanup after processing
        aggressive_memory_cleanup()
        
        return embeddings
        
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"\n⚠️  Memory error, attempting recovery...")
            aggressive_memory_cleanup()
            
            # Try processing one by one
            individual_embeddings = []
            for text in texts:
                try:
                    emb = model.encode([text], show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
                    individual_embeddings.append(emb[0])
                    aggressive_memory_cleanup()
                except Exception as single_e:
                    print(f"❌ Failed to process individual text: {single_e}")
                    # Create dummy embedding to maintain structure
                    dummy_emb = np.zeros(model.get_sentence_embedding_dimension())
                    individual_embeddings.append(dummy_emb)
            
            return np.array(individual_embeddings)
        else:
            raise

def generate_embeddings_streaming(model, input_csv, output_csv, batch_size=2, max_rows=None):
    """
    Generate embeddings using streaming processing to minimize memory usage.
    Processes and saves data in chunks to avoid memory accumulation.
    """
    print(f"🔄 Starting streaming embedding generation with batch size {batch_size}")
    
    # Create a temporary file for progressive saving
    temp_file = output_csv.with_suffix('.tmp')
    
    try:
        # Read CSV in chunks to minimize memory usage
        chunk_size = max(1000, batch_size * 10)  # Process reasonable chunks
        csv_reader = pd.read_csv(input_csv, chunksize=chunk_size)
        
        total_processed = 0
        first_chunk = True
        
        for chunk_idx, df_chunk in enumerate(csv_reader):
            if max_rows and total_processed >= max_rows:
                break
                
            # Limit chunk if needed
            if max_rows:
                remaining = max_rows - total_processed
                if len(df_chunk) > remaining:
                    df_chunk = df_chunk.head(remaining)
            
            print(f"\n📦 Processing chunk {chunk_idx + 1}: {len(df_chunk)} rows")
            
            # Clean texts for this chunk
            rule_texts = [clean_text(text) for text in df_chunk['rule_text']]
            
            # Process this chunk in batches
            chunk_embeddings = []
            for i in tqdm(range(0, len(rule_texts), batch_size), 
                         desc=f"Chunk {chunk_idx + 1} batches", leave=False):
                batch_texts = rule_texts[i:i + batch_size]
                
                if not batch_texts:
                    continue
                
                # Process batch
                batch_embeddings = process_single_batch(model, batch_texts, model.device)
                chunk_embeddings.extend(batch_embeddings)
                
                # Memory cleanup between batches
                aggressive_memory_cleanup()
            
            # Convert embeddings to JSON for this chunk
            embeddings_json = [json.dumps(embedding.tolist()) for embedding in chunk_embeddings]
            df_chunk = df_chunk.copy()
            df_chunk['embedding'] = embeddings_json
            
            # Save this chunk to file (append mode after first chunk)
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            df_chunk.to_csv(temp_file, mode=mode, header=header, index=False, encoding='utf-8')
            
            total_processed += len(df_chunk)
            first_chunk = False
            
            # Cleanup chunk data from memory
            del df_chunk, rule_texts, chunk_embeddings, embeddings_json
            aggressive_memory_cleanup()
            
            print(f"✅ Chunk {chunk_idx + 1} completed. Total processed: {total_processed}")
        
        # Move temp file to final location
        temp_file.rename(output_csv)
        
        # Calculate and display file size
        file_size_mb = os.path.getsize(output_csv) / (1024 * 1024)
        print(f"\n🎉 Embeddings generation completed!")
        print(f"📊 Total rows processed: {total_processed}")
        print(f"📁 Output file: {output_csv}")
        print(f"📏 File size: {file_size_mb:.2f} MB")
        
        return total_processed
        
    except Exception as e:
        # Cleanup temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise e

def verify_output_file(output_csv, expected_rows=None):
    """Verify the output file was created correctly."""
    if not output_csv.exists():
        print("❌ Output file was not created")
        return False
    
    try:
        # Read just the header and first few rows to verify structure
        df_sample = pd.read_csv(output_csv, nrows=5)
        
        required_columns = ['embedding']
        missing_columns = [col for col in required_columns if col not in df_sample.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        # Count total rows
        total_rows = sum(1 for line in open(output_csv)) - 1  # Subtract header
        
        if expected_rows and total_rows != expected_rows:
            print(f"⚠️  Row count mismatch: expected {expected_rows}, got {total_rows}")
        
        print(f"✅ Output file verification passed: {total_rows} rows")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying output file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for legal rules dataset (Memory-Optimized)")
    parser.add_argument("--model", default="BAAI/bge-m3", help="Embedding model to use")
    parser.add_argument("--batch-size", type=int, help="Batch size for embedding generation (auto-detected if not specified)")
    parser.add_argument("--max-rows", type=int, help="Maximum number of rows to process (for testing)")
    parser.add_argument("--force-cpu", action="store_true", help="Force CPU usage even if GPU is available")
    parser.add_argument("--device", choices=["cpu", "cuda", "mps"], help="Force specific device")
    
    args = parser.parse_args()
    
    try:
        # Setup paths
        input_csv, output_csv = setup_paths()
        
        print(f"Input CSV: {input_csv}")
        print(f"Output CSV: {output_csv}")
        
        # Check if input file exists
        if not input_csv.exists():
            print(f"Error: Input file {input_csv} does not exist!")
            return 1
        
        # Check input file size
        input_size_mb = os.path.getsize(input_csv) / (1024 * 1024)
        print(f"📁 Input file size: {input_size_mb:.2f} MB")
        
        # Quick check of input file structure
        try:
            df_sample = pd.read_csv(input_csv, nrows=5)
            total_rows = sum(1 for line in open(input_csv)) - 1  # Subtract header
            print(f"📊 Total rows in dataset: {total_rows}")
            print(f"📋 Columns: {list(df_sample.columns)}")
            
            if 'rule_text' not in df_sample.columns:
                print("❌ Error: 'rule_text' column not found in input file")
                return 1
                
        except Exception as e:
            print(f"❌ Error reading input file: {e}")
            return 1
        
        # Determine processing limit
        if args.max_rows:
            total_to_process = min(args.max_rows, total_rows)
            print(f"🎯 Processing limited to {total_to_process} rows for testing")
        else:
            total_to_process = total_rows
            print(f"🎯 Processing all {total_to_process} rows")
        
        # Detect device and get suggested batch size
        device, suggested_batch_size = detect_device()
        
        # Determine device to use
        if args.force_cpu:
            device = "cpu"
        elif args.device:
            device = args.device
        
        # Determine batch size with extra conservatism for MPS
        if args.batch_size:
            batch_size = args.batch_size
            print(f"🎯 Using specified batch size: {batch_size}")
        else:
            batch_size = suggested_batch_size
            print(f"🤖 Using auto-detected batch size: {batch_size}")
        
        # Extra warning for MPS
        if device == "mps":
            print(f"⚠️  MPS detected: Using conservative settings to prevent memory issues")
            print(f"💡 If you still get memory errors, try: --force-cpu or --batch-size 1")
        
        # Load embedding model
        model = load_embedding_model(args.model, device=device, force_cpu=args.force_cpu)
        
        # Generate embeddings using streaming approach
        print(f"\n🚀 Starting streaming embedding generation...")
        print(f"📦 Batch size: {batch_size}")
        print(f"🔧 Device: {device.upper()}")
        print(f"📊 Estimated memory usage: Much lower than traditional approach")
        
        start_time = time.time()
        processed_rows = generate_embeddings_streaming(
            model, input_csv, output_csv, batch_size, args.max_rows
        )
        elapsed_time = time.time() - start_time
        
        # Verify output
        if verify_output_file(output_csv, processed_rows):
            print(f"\n🎉 Embeddings generation completed successfully!")
            print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
            print(f"⚡ Processing rate: {processed_rows / elapsed_time:.1f} rows/second")
            print(f"📤 You can now commit the embeddings file to Git")
            print(f"⬆️  Run 'upload' command to load into database")
            return 0
        else:
            print(f"\n❌ Output verification failed")
            return 1
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Final cleanup
        aggressive_memory_cleanup()

if __name__ == "__main__":
    sys.exit(main()) 