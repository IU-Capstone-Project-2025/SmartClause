#!/usr/bin/env python3
"""
Create Chunks Dataset Script for SmartClause Legal Analysis Platform

This script converts the original legal rules dataset into optimally-sized chunks
using parameters determined from chunking experiments. The optimal parameters are:
- chunk_size: 800 characters
- overlap: 500 characters

Usage:
    python create_chunks_dataset.py [--input INPUT_FILE] [--output OUTPUT_FILE] 
                                   [--chunk-size CHUNK_SIZE] [--overlap OVERLAP]
                                   [--force] [--verify]
    
Options:
    --input: Input CSV file path (default: datasets/rules_dataset.csv)
    --output: Output CSV file path (default: auto-generated in datasets/)
    --chunk-size: Size of each chunk in characters (default: 800)
    --overlap: Number of overlapping characters between chunks (default: 500)
    --force: Force overwrite existing output file
    --verify: Verify chunking results after processing
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from typing import List, Tuple, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

# Ensure NLTK resources are downloaded
try:
    stopwords.words('russian')
    word_tokenize('тест', language='russian')
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt')


def preprocess_text(text: str) -> str:
    # Remove unnecessary punctuation (keep . , : ; - ( ))
    # Remove: ! ? " ' / \ [ ] { } * # $ % & < = > @ ^ _ ` | ~
    text = re.sub(r"[!\?\"'\[\]{}*/#\$%&<>@^_`|~\\]", "", text)
    stop_words = stopwords.words('russian')
    keywords = ["статья", "глава", "часть", "пункта", "№", "закона", "от", "законов"]
    text = text.lower()
    tokens = word_tokenize(text, language='russian')
    processed_tokens = []
    for i, token in enumerate(tokens):
        if token not in stop_words:
            if (token.isnumeric() or not token.isalnum()) and len(token) != 1:
                if i > 0 and tokens[i-1] in keywords:
                    processed_tokens.append(token)
            else:
                processed_tokens.append(token)
    return " ".join(processed_tokens)

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[Tuple[str, int, int]]:
    chunks = []
    n = len(text)
    if n <= chunk_size:
        return [(text, 0, n)]
    step = chunk_size - overlap
    if step <= 0:
        raise ValueError(f"Overlap ({overlap}) must be less than chunk_size ({chunk_size})")
    start = 0
    while start < n:
        # Move start forward to next word boundary (if not at 0)
        if start != 0:
            while start < n and text[start].isalnum():
                start += 1
            # Move past the boundary character (if not at end)
            if start < n and not text[start].isalnum():
                start += 1
        end = min(start + chunk_size, n)
        # If not at the end, move end back to the last word boundary
        if end < n:
            while end > start and text[end-1].isalnum():
                end -= 1
            if end == start:
                end = min(start + chunk_size, n)
        chunk_content = text[start:end]
        chunks.append((chunk_content, start, end))
        if end == n:
            break
        # Next chunk starts at (end - overlap), but ensure it's not negative
        start = max(end - overlap, 0)
    return chunks

def validate_input_file(file_path: Path) -> bool:
    try:
        df = pd.read_csv(file_path, nrows=1)
        required_columns = [
            'rule_id', 'file', 'rule_number', 'rule_title', 'rule_text',
            'section_title', 'chapter_title', 'start_char', 'end_char', 'text_length'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        return False

def load_dataset(file_path: Path) -> Optional[pd.DataFrame]:
    try:
        print(f"📂 Loading dataset from {file_path}")
        df = pd.read_csv(file_path)
        print(f"✓ Loaded {len(df)} rules")
        print(f"  Columns: {list(df.columns)}")
        if df['rule_text'].isna().any():
            print("⚠️  Warning: Some rules have missing text")
        return df
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None

def create_chunks_dataset(rules_df: pd.DataFrame, chunk_size: int = 800, overlap: int = 500) -> pd.DataFrame:
    print(f"\n🔄 Creating chunks with size={chunk_size}, overlap={overlap}")
    chunk_rows = []
    chunk_id_counter = 0
    for _, row in tqdm(rules_df.iterrows(), total=len(rules_df), desc="Processing rules"):
        rule_id = row['rule_id']
        rule_text = str(row['rule_text']) if pd.notna(row['rule_text']) else ""
        if not rule_text.strip():
            continue
        chunks = chunk_text(rule_text, chunk_size, overlap)
        for chunk_number, (chunk_content, start_pos, end_pos) in enumerate(chunks):
            preprocessed_chunk = preprocess_text(chunk_content)
            chunk_rows.append({
                'chunk_id': chunk_id_counter,
                'rule_id': rule_id,
                'chunk_number': chunk_number,
                'chunk_text': preprocessed_chunk,
                'chunk_char_start': start_pos,
                'chunk_char_end': end_pos,
                'chunk_length': len(chunk_content)
            })
            chunk_id_counter += 1
    chunks_df = pd.DataFrame(chunk_rows)
    print(f"✓ Created {len(chunks_df)} chunks from {len(rules_df)} rules")
    return chunks_df

def verify_chunking(chunks_df: pd.DataFrame, rules_df: pd.DataFrame) -> bool:
    print(f"\n🔍 Verifying chunking results...")
    try:
        total_chunks = len(chunks_df)
        total_rules = len(rules_df)
        avg_chunks_per_rule = total_chunks / total_rules
        print(f"  - Total chunks: {total_chunks:,}")
        print(f"  - Total rules: {total_rules:,}")
        print(f"  - Average chunks per rule: {avg_chunks_per_rule:.2f}")
        missing_chunk_text = chunks_df['chunk_text'].isna().sum()
        if missing_chunk_text > 0:
            print(f"⚠️  Warning: {missing_chunk_text} chunks have missing text")
        chunk_lengths = chunks_df['chunk_text'].str.len()
        print(f"  - Chunk length stats:")
        print(f"    • Min: {chunk_lengths.min()}")
        print(f"    • Max: {chunk_lengths.max()}")
        print(f"    • Mean: {chunk_lengths.mean():.1f}")
        print(f"    • Median: {chunk_lengths.median():.1f}")
        duplicate_chunk_ids = chunks_df['chunk_id'].duplicated().sum()
        if duplicate_chunk_ids > 0:
            print(f"❌ Found {duplicate_chunk_ids} duplicate chunk_ids")
            return False
        missing_rule_ids = set(chunks_df['rule_id']) - set(rules_df['rule_id'])
        if missing_rule_ids:
            print(f"❌ Found chunks with missing rule_ids: {len(missing_rule_ids)}")
            return False
        sample_size = min(5, len(chunks_df))
        sample_chunks = chunks_df.sample(sample_size)
        print(f"  - Sample chunks verification:")
        for _, chunk in sample_chunks.iterrows():
            rule_id = chunk['rule_id']
            original_rule = rules_df[rules_df['rule_id'] == rule_id].iloc[0]
            original_text = str(original_rule['rule_text'])
            start_pos = chunk['chunk_char_start']
            end_pos = chunk['chunk_char_end']
            expected_chunk = original_text[start_pos:end_pos]
            if chunk['chunk_text'] != expected_chunk:
                print(f"    ❌ Chunk {chunk['chunk_id']} doesn't match original text")
                return False
        print("✓ All verification checks passed")
        return True
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def save_chunks_dataset(chunks_df: pd.DataFrame, output_path: Path, force: bool = False) -> bool:
    try:
        if output_path.exists() and not force:
            response = input(f"Output file {output_path} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"💾 Saving chunks dataset to {output_path}")
        chunks_df.to_csv(output_path, index=False)
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"✓ Saved successfully ({file_size:,} bytes)")
            return True
        else:
            print("❌ Failed to save file")
            return False
    except Exception as e:
        print(f"❌ Error saving dataset: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Create chunks dataset from legal rules using optimal parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Use default settings (chunk_size=800, overlap=500)
    python create_chunks_dataset.py
    
    # Specify custom input and output files
    python create_chunks_dataset.py --input datasets/rules_dataset.csv --output datasets/chunks.csv
    
    # Use custom chunking parameters
    python create_chunks_dataset.py --chunk-size 1000 --overlap 300
    
    # Force overwrite and verify results
    python create_chunks_dataset.py --force --verify
        """
    )
    parser.add_argument("--input", "-i", type=str, default="datasets/rules_dataset.csv",
                       help="Input CSV file path (default: datasets/rules_dataset.csv)")
    parser.add_argument("--output", "-o", type=str,
                       help="Output CSV file path (default: datasets/chunks_dataset.csv)")
    parser.add_argument("--chunk-size", type=int, default=800,
                       help="Size of each chunk in characters (default: 800)")
    parser.add_argument("--overlap", type=int, default=500,
                       help="Number of overlapping characters between chunks (default: 500)")
    parser.add_argument("--force", action="store_true",
                       help="Force overwrite existing output file")
    parser.add_argument("--verify", action="store_true",
                       help="Verify chunking results after processing")
    args = parser.parse_args()
    try:
        input_file = Path(args.input)
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return 1
        if not validate_input_file(input_file):
            return 1
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = Path("datasets/chunks_dataset.csv")
        if args.chunk_size <= 0:
            print(f"❌ Invalid chunk_size: {args.chunk_size}")
            return 1
        if args.overlap < 0:
            print(f"❌ Invalid overlap: {args.overlap}")
            return 1
        if args.overlap >= args.chunk_size:
            print(f"❌ Overlap ({args.overlap}) must be less than chunk_size ({args.chunk_size})")
            return 1
        print("🚀 SmartClause Chunks Dataset Creator")
        print("=" * 50)
        print(f"📁 Input file: {input_file}")
        print(f"📁 Output file: {output_file}")
        print(f"🔧 Chunk size: {args.chunk_size} characters")
        print(f"🔧 Overlap: {args.overlap} characters")
        print(f"🔧 Force overwrite: {args.force}")
        print(f"🔧 Verify results: {args.verify}")
        print()
        rules_df = load_dataset(input_file)
        if rules_df is None:
            return 1
        chunks_df = create_chunks_dataset(rules_df, args.chunk_size, args.overlap)
        if args.verify:
            if not verify_chunking(chunks_df, rules_df):
                print("❌ Chunking verification failed")
                return 1
        if not save_chunks_dataset(chunks_df, output_file, args.force):
            return 1
        print("\n🎉 Chunks dataset created successfully!")
        print(f"📊 Summary:")
        print(f"  - Input rules: {len(rules_df):,}")
        print(f"  - Output chunks: {len(chunks_df):,}")
        print(f"  - Average chunks per rule: {len(chunks_df) / len(rules_df):.2f}")
        print(f"  - Output file: {output_file}")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 