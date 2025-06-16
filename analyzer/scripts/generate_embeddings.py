#!/usr/bin/env python3
"""
Script to generate embeddings for legal rules dataset.
This script reads the dataset from parser/dataset/dataset_gk_rf.csv,
generates embeddings for rule_text using BGE-M3 model,
and saves the results to a CSV file that can be committed to Git.
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

def setup_paths():
    """Setup paths relative to the analyzer directory."""
    # Get the analyzer directory (parent of scripts)
    analyzer_dir = Path(__file__).parent.parent
    project_root = analyzer_dir.parent
    
    # Paths for input and output
    input_csv = project_root / "parser" / "dataset" / "dataset_gk_rf.csv"
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
        suggested_batch_size = 8  # Smaller batch size for MPS
        print("🍎 Apple Silicon MPS detected")
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

def generate_embeddings_batch(model, texts, batch_size=32):
    """Generate embeddings for a batch of texts with memory management."""
    embeddings = []
    failed_batches = 0
    
    # Process in batches for memory efficiency
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
        batch = texts[i:i + batch_size]
        
        try:
            batch_embeddings = model.encode(
                batch, 
                show_progress_bar=False, 
                convert_to_numpy=True,
                batch_size=min(batch_size, len(batch))  # Ensure batch_size doesn't exceed batch length
            )
            embeddings.extend(batch_embeddings)
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif torch.backends.mps.is_available():
                torch.mps.empty_cache()
                
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                failed_batches += 1
                print(f"\n⚠️  Memory error in batch {i//batch_size + 1}, trying smaller sub-batches...")
                
                # Try processing this batch with smaller sub-batches
                sub_batch_size = max(1, batch_size // 4)
                batch_embeddings = []
                
                for j in range(0, len(batch), sub_batch_size):
                    sub_batch = batch[j:j + sub_batch_size]
                    try:
                        sub_embeddings = model.encode(
                            sub_batch, 
                            show_progress_bar=False, 
                            convert_to_numpy=True
                        )
                        batch_embeddings.extend(sub_embeddings)
                        
                        # Clear cache after each sub-batch
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                        elif torch.backends.mps.is_available():
                            torch.mps.empty_cache()
                            
                    except Exception as sub_e:
                        print(f"❌ Failed to process sub-batch: {sub_e}")
                        # Create dummy embeddings to maintain array structure
                        dummy_embedding = np.zeros((len(sub_batch), model.get_sentence_embedding_dimension()))
                        batch_embeddings.extend(dummy_embedding)
                
                embeddings.extend(batch_embeddings)
            else:
                raise
    
    if failed_batches > 0:
        print(f"\n⚠️  {failed_batches} batches had memory issues and were processed with smaller sub-batches")
    
    return embeddings

def save_embeddings_to_csv(df, embeddings, output_path):
    """Save the dataframe with embeddings to CSV."""
    print("Preparing data for CSV export...")
    
    # Create a copy of the dataframe
    df_with_embeddings = df.copy()
    
    # Convert embeddings to JSON strings for CSV storage
    embeddings_json = [json.dumps(embedding.tolist()) for embedding in embeddings]
    df_with_embeddings['embedding'] = embeddings_json
    
    # Save to CSV
    print(f"Saving data with embeddings to: {output_path}")
    df_with_embeddings.to_csv(output_path, index=False, encoding='utf-8')
    
    # Calculate and display file size
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"File saved successfully. Size: {file_size_mb:.2f} MB")
    
    return df_with_embeddings

def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for legal rules dataset")
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
        
        # Load dataset
        print("Loading dataset...")
        df = pd.read_csv(input_csv)
        
        if args.max_rows:
            print(f"Limiting to first {args.max_rows} rows for testing")
            df = df.head(args.max_rows)
        
        print(f"Loaded {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Clean and prepare texts for embedding
        print("Cleaning rule texts...")
        rule_texts = [clean_text(text) for text in df['rule_text']]
        
        # Filter out empty texts
        valid_indices = [i for i, text in enumerate(rule_texts) if text.strip()]
        if len(valid_indices) != len(rule_texts):
            print(f"Warning: {len(rule_texts) - len(valid_indices)} empty rule texts found")
        
        # Detect device and get suggested batch size
        device, suggested_batch_size = detect_device()
        
        # Determine device to use
        if args.force_cpu:
            device = "cpu"
        elif args.device:
            device = args.device
        
        # Determine batch size
        if args.batch_size:
            batch_size = args.batch_size
            print(f"🎯 Using specified batch size: {batch_size}")
        else:
            batch_size = suggested_batch_size
            print(f"🤖 Using auto-detected batch size: {batch_size}")
        
        # Load embedding model
        model = load_embedding_model(args.model, device=device, force_cpu=args.force_cpu)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(rule_texts)} texts...")
        print(f"📦 Processing in batches of {batch_size}")
        embeddings = generate_embeddings_batch(model, rule_texts, batch_size)
        
        # Verify embeddings
        if len(embeddings) != len(df):
            print(f"Error: Number of embeddings ({len(embeddings)}) doesn't match number of rows ({len(df)})")
            return 1
        
        print(f"Generated {len(embeddings)} embeddings")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        # Save to CSV
        df_result = save_embeddings_to_csv(df, embeddings, output_csv)
        
        # Display sample
        print("\nSample of generated data:")
        print(df_result[['rule_number', 'rule_title', 'text_length']].head())
        
        print(f"\nEmbeddings generation completed successfully!")
        print(f"Output file: {output_csv}")
        print(f"You can now commit this file to Git and use the upload script to load it into PostgreSQL.")
        
        return 0
        
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