#!/usr/bin/env python3
"""
Dataset Download Script for SmartClause Legal Analysis Platform

This script downloads the required datasets from Hugging Face Hub:
- rules_dataset.csv (33MB): Legal rules metadata  
- chunks_dataset.csv (65MB): Text chunks for embedding
- chunks_with_embeddings.csv (1.1GB): Pre-generated embeddings

Usage:
    python download_datasets.py [--force] [--verify]
    
Options:
    --force: Force re-download even if files exist
    --verify: Verify file integrity after download
"""

import os
import sys
import argparse
from pathlib import Path
from urllib.request import urlretrieve, urlopen
from urllib.error import URLError, HTTPError

# Hugging Face dataset configuration
HF_DATASET_REPO = "narly/russian-codexes-bge-m3"
HF_BASE_URL = f"https://huggingface.co/datasets/{HF_DATASET_REPO}/resolve/main"

# Dataset files configuration
DATASETS = {
    "rules_dataset.csv": {
        "url": f"{HF_BASE_URL}/rules_dataset.csv",
        "description": "Legal rules metadata (190,846 rules)"
    },
    "chunks_dataset.csv": {
        "url": f"{HF_BASE_URL}/chunks_dataset.csv", 
        "description": "Text chunks for embedding (413,453 chunks)"
    },
    "chunks_with_embeddings.csv": {
        "url": f"{HF_BASE_URL}/chunks_with_embeddings.csv",
        "description": "Pre-generated embeddings (BGE-M3 model)"
    }
}

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def download_progress_hook(block_num, block_size, total_size):
    """Progress callback for urlretrieve"""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, (downloaded * 100) // total_size)
        size_downloaded = format_size(downloaded)
        size_total = format_size(total_size)
        print(f"\r  Progress: {percent:3d}% [{size_downloaded}/{size_total}]", end="", flush=True)
    else:
        size_downloaded = format_size(downloaded)
        print(f"\r  Downloaded: {size_downloaded}", end="", flush=True)

def get_remote_file_size(url):
    """Get file size from HTTP headers"""
    try:
        with urlopen(url) as response:
            content_length = response.headers.get('Content-Length')
            if content_length:
                return int(content_length)
    except Exception:
        pass
    return None

def verify_file_size(filepath, expected_size_bytes=None, tolerance=0.05):
    """Verify downloaded file size against expected size"""
    if not filepath.exists():
        return False
    
    # If no expected size provided, just check file exists and isn't empty
    if expected_size_bytes is None:
        return filepath.stat().st_size > 0
    
    actual_size = filepath.stat().st_size
    size_diff = abs(actual_size - expected_size_bytes) / expected_size_bytes
    return size_diff <= tolerance

def download_file(filename, config, target_dir, force=False):
    """Download a single dataset file"""
    filepath = target_dir / filename
    
    # Get remote file size first
    print(f"📥 Preparing to download {filename}")
    print(f"   Description: {config['description']}")
    print(f"   URL: {config['url']}")
    
    remote_size = get_remote_file_size(config["url"])
    if remote_size:
        print(f"   Remote size: {format_size(remote_size)}")
    else:
        print("   Remote size: Unknown")
    
    # Check if file already exists
    if filepath.exists() and not force:
        if verify_file_size(filepath, remote_size):
            actual_size = format_size(filepath.stat().st_size)
            print(f"✅ {filename} already exists and appears valid ({actual_size})")
            return True
        else:
            print(f"⚠️  {filename} exists but size mismatch, re-downloading...")
    
    try:
        # Download with progress indicator
        print(f"🔄 Starting download...")
        urlretrieve(config["url"], filepath, reporthook=download_progress_hook)
        print()  # New line after progress
        
        # Verify download
        if verify_file_size(filepath, remote_size):
            actual_size = format_size(filepath.stat().st_size)
            print(f"✅ Downloaded successfully: {actual_size}")
            return True
        else:
            actual_size = format_size(filepath.stat().st_size) if filepath.exists() else "0 B"
            expected_size = format_size(remote_size) if remote_size else "Unknown"
            print(f"❌ Size verification failed for {filename}")
            print(f"   Expected: {expected_size}, Got: {actual_size}")
            return False
            
    except HTTPError as e:
        print(f"\n❌ HTTP Error downloading {filename}: {e.code} {e.reason}")
        return False
    except URLError as e:
        print(f"\n❌ URL Error downloading {filename}: {e.reason}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error downloading {filename}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download SmartClause datasets from Hugging Face")
    parser.add_argument("--force", action="store_true", 
                       help="Force re-download even if files exist")
    parser.add_argument("--verify", action="store_true",
                       help="Verify file integrity after download")
    
    args = parser.parse_args()
    
    # Setup target directory
    script_dir = Path(__file__).parent
    
    # Prefer project root datasets directory (for Docker mounting)
    project_root = script_dir.parent.parent
    preferred_datasets_dir = project_root / "datasets"
    local_datasets_dir = script_dir / "datasets"
    
    # Use project root datasets directory if we're likely in Docker context
    # or if it already exists, otherwise use local directory
    if preferred_datasets_dir.exists() or not local_datasets_dir.exists():
        datasets_dir = preferred_datasets_dir
        print(f"📁 Using project root datasets directory")
    else:
        datasets_dir = local_datasets_dir
        print(f"📁 Using local datasets directory")
    
    datasets_dir.mkdir(exist_ok=True)
    
    print("🚀 SmartClause Dataset Downloader")
    print("=" * 50)
    print(f"📁 Target directory: {datasets_dir}")
    print(f"🌐 Source: https://huggingface.co/datasets/{HF_DATASET_REPO}")
    print()
    
    # Calculate total download size from remote
    print("📊 Checking remote file sizes...")
    total_size = 0
    for filename, config in DATASETS.items():
        remote_size = get_remote_file_size(config["url"])
        if remote_size:
            total_size += remote_size
            print(f"   {filename}: {format_size(remote_size)}")
        else:
            print(f"   {filename}: Size unknown")
    
    if total_size > 0:
        print(f"\n📊 Total download size: {format_size(total_size)}")
    print()
    
    # Download each dataset
    success_count = 0
    for filename, config in DATASETS.items():
        print(f"📦 Processing {filename}...")
        if download_file(filename, config, datasets_dir, args.force):
            success_count += 1
        print()
    
    # Summary
    print("=" * 50)
    if success_count == len(DATASETS):
        print("🎉 All datasets downloaded successfully!")
        print()
        print("Next steps:")
        print("1. Start the application: docker-compose up -d")
        print("2. Load datasets: docker-compose exec analyzer python scripts/process_and_upload_datasets.py --upload --clear")
        print("3. Access the application at http://localhost:3000")
    else:
        failed_count = len(DATASETS) - success_count
        print(f"⚠️  {failed_count} dataset(s) failed to download")
        print("Please check your internet connection and try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 