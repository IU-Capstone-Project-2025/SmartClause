#!/bin/bash
set -e

# Get the directory of the script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "Copying parser/dataset/dataset_codes_rf.csv to datasets/rules_dataset.csv..."
cp "$SCRIPT_DIR/../parser/dataset/dataset_codes_rf.csv" "$SCRIPT_DIR/rules_dataset.csv"

echo "Running chunking script..."
python "$SCRIPT_DIR/../analyzer/scripts/create_chunks_dataset.py" --force

echo "Generating embeddings for chunks..."
python "$SCRIPT_DIR/../analyzer/scripts/process_and_upload_datasets.py" --generate

echo "Done!" 