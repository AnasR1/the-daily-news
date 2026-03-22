"""Script to create all database tables."""
import logging
from app.database import engine, Base
from app.database.models import Video

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables defined in models."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create database tables: {e}")
        raise


if __name__ == "__main__":
    create_tables()
