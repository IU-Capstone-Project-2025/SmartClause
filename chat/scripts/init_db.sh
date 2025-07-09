#!/bin/bash

# Database initialization script for SmartClause Chat microservice
# This script creates the chatdb database and required tables

set -e  # Exit on any error

echo "🚀 Initializing Chat microservice database..."

# Check if we're running in Docker or locally
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker container"
    PYTHON_CMD="python"
else
    echo "💻 Running locally"
    PYTHON_CMD="python3"
fi

# Change to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Run the Python initialization script
echo "🔧 Running database initialization..."
$PYTHON_CMD init_db.py

echo "✅ Database initialization completed!"
echo ""
echo "You can now start the chat service with:"
echo "  docker-compose up chat"
echo "or:"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8002" 