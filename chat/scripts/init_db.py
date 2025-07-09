#!/usr/bin/env python3
"""
Database initialization script for SmartClause Chat microservice.
Creates the chatdb database and required tables.
"""

import asyncio
import sys
import logging
import os
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import MetaData, Table, Column, String, Text, DateTime, Integer, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment variables"""
    # Try to get from environment
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Fallback to default values
    return "postgresql+asyncpg://smartclause:sm4rtcl4us3@postgres:5432/chatdb"


async def create_database():
    """Create the chatdb database if it doesn't exist"""
    try:
        # Get database URL and construct postgres URL
        db_url = get_database_url()
        postgres_url = db_url.replace('/chatdb', '/postgres')
        
        # Extract connection details
        import re
        match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/.*', postgres_url)
        if not match:
            raise ValueError("Invalid database URL format")
        
        user, password, host, port = match.groups()
        
        # Connect using asyncpg directly to postgres database
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database='postgres'
        )
        
        # Check if chatdb exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'chatdb'"
        )
        
        if not result:
            logger.info("Creating chatdb database...")
            await conn.execute("CREATE DATABASE chatdb")
            logger.info("✅ chatdb database created successfully")
        else:
            logger.info("✅ chatdb database already exists")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        raise


async def create_tables():
    """Create the required tables in chatdb"""
    try:
        logger.info("Creating database tables...")
        
        db_url = get_database_url()
        engine = create_async_engine(db_url, echo=True)
        
        # Define metadata
        metadata = MetaData()
        
        # Define chat_messages table
        chat_messages = Table(
            'chat_messages',
            metadata,
            Column('id', UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
            Column('space_id', UUID(as_uuid=True), nullable=False, index=True),
            Column('user_id', String(255), nullable=False, index=True),
            Column('content', Text, nullable=False),
            Column('type', String(20), nullable=False),
            Column('timestamp', DateTime(timezone=True), server_default=func.now(), nullable=False),
            Column('message_metadata', JSONB, server_default='{}'),
            Column('sequence_number', Integer, nullable=False),
            Column('is_deleted', Boolean, server_default='false')
        )
        
        # Define chat_sessions table
        chat_sessions = Table(
            'chat_sessions',
            metadata,
            Column('id', UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
            Column('space_id', UUID(as_uuid=True), nullable=False, unique=True, index=True),
            Column('user_id', String(255), nullable=False, index=True),
            Column('memory_length', Integer, server_default='10'),
            Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
            Column('updated_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
            Column('is_active', Boolean, server_default='true')
        )
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)  # Drop existing tables
            await conn.run_sync(metadata.create_all)  # Create fresh tables
            
            # Execute each SQL statement separately
            sql_statements = [
                "CREATE INDEX IF NOT EXISTS chat_messages_space_user_idx ON chat_messages (space_id, user_id)",
                "CREATE INDEX IF NOT EXISTS chat_messages_sequence_idx ON chat_messages (space_id, user_id, sequence_number DESC)",
                "CREATE INDEX IF NOT EXISTS chat_messages_timestamp_idx ON chat_messages (timestamp DESC)",
                "ALTER TABLE chat_messages ADD CONSTRAINT chat_messages_space_user_seq UNIQUE (space_id, user_id, sequence_number)",
                # Removed the type check constraint since SQLAlchemy Enum already handles it
                "ALTER TABLE chat_sessions ADD CONSTRAINT chat_sessions_memory_check CHECK (memory_length >= 1 AND memory_length <= 50)",
                """CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'""",
                "DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions",
                "CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
            ]
            
            for sql_stmt in sql_statements:
                try:
                    await conn.execute(text(sql_stmt))
                    logger.debug(f"Executed: {sql_stmt[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to execute SQL statement: {e}")
                    # Continue with other statements
        
        await engine.dispose()
        
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


async def verify_setup():
    """Verify the database setup by checking tables"""
    try:
        logger.info("Verifying database setup...")
        
        db_url = get_database_url()
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in result.fetchall()]
            
        await engine.dispose()
        
        expected_tables = ['chat_messages', 'chat_sessions']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        logger.info(f"✅ All required tables exist: {tables}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying setup: {e}")
        return False


async def main():
    """Main initialization function"""
    logger.info("🚀 Starting Chat microservice database initialization...")
    
    db_url = get_database_url()
    logger.info(f"Database URL: {db_url}")
    
    try:
        # Step 1: Create database
        await create_database()
        
        # Step 2: Create tables
        await create_tables()
        
        # Step 3: Verify setup
        success = await verify_setup()
        
        if success:
            logger.info("🎉 Chat microservice database initialization completed successfully!")
        else:
            logger.error("💥 Database initialization failed verification")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 