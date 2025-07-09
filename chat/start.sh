#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting Chat microservice..."

echo "⏳ Waiting for PostgreSQL to be ready..."
while ! python -c "
import asyncpg
import asyncio
async def check_db():
    try:
        conn = await asyncpg.connect('postgresql://smartclause:sm4rtcl4us3@postgres:5432/postgres')
        await conn.close()
        return True
    except:
        return False
result = asyncio.run(check_db())
exit(0 if result else 1)
" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

echo "🔧 Initializing database..."
python scripts/init_db.py

echo "🎉 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload 