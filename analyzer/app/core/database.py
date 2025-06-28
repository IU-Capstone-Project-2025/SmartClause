from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        # Configure HNSW search parameters once per session for optimal performance
        # Based on benchmarking results: ef_search = 32 provides the best accuracy/speed tradeoff
        try:
            db.execute(text(f"SET hnsw.ef_search = {settings.hnsw_ef_search}"))
            logger.debug(f"HNSW ef_search parameter set to {settings.hnsw_ef_search}")
        except Exception as e:
            logger.warning(f"Failed to set HNSW parameters: {e}")
            # This is not critical, continue without custom parameters
        
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """Initialize database with required extensions and tables"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise 