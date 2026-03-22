"""Main entry point for the Daily News scraper."""
import re
import sys
from pathlib import Path

from app.database import SessionLocal, engine, Base
from app.database.models import Video
from app.scrapers.runner import ScraperRunner
from app.scrapers.youtube_scraper import YouTubeScraper
from app.logging_config import get_logger

logger = get_logger(__name__)


def load_channel_ids(config_file: str = "config/channels.txt") -> list[str]:
    """Load YouTube channel IDs from configuration file.
    
    Supports various YouTube URL formats and extracts channel IDs.
    """
    channel_ids = []
    
    config_path = Path(config_file)
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_file}")
        return channel_ids
    
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Extract channel ID from various YouTube URL formats
            channel_id = extract_channel_id(line)
            if channel_id:
                channel_ids.append(channel_id)
                logger.debug(f"Loaded channel ID: {channel_id}")
    
    return channel_ids


def extract_channel_id(url_or_id: str) -> str | None:
    """Extract channel ID from YouTube URL or return ID if already a channel ID."""
    url_or_id = url_or_id.strip()
    
    # Already a channel ID (starts with UC)
    if url_or_id.startswith("UC"):
        return url_or_id
    
    # Extract from standard channel URL: /channel/UCxxx
    match = re.search(r"/channel/([UCuc][a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    
    # For @handle and /c/name formats, we'd need web scraping to get the actual channel ID
    # For now, log that these require special handling
    if "@" in url_or_id or "/c/" in url_or_id or "/user/" in url_or_id:
        logger.warning(
            f"URL format '{url_or_id}' requires web scraping to extract channel ID. "
            f"Please convert to channel ID (UC...) format or use the full URL with channel ID."
        )
    
    return None


def init_database() -> None:
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def main() -> int:
    """Main entry point for the scraper."""
    try:
        logger.info("Starting Daily News Scraper")
        
        # Initialize database
        init_database()
        
        # Load channel IDs from config
        channel_ids = load_channel_ids()
        
        if not channel_ids:
            logger.error("No valid channel IDs found in config/channels.txt")
            return 1
        
        logger.info(f"Loaded {len(channel_ids)} channel(s) to scrape")
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Initialize scraper runner with database session
            runner = ScraperRunner(db=db)
            
            # Register YouTube scraper
            youtube_scraper = YouTubeScraper(
                channel_ids=channel_ids,
                max_results_per_channel=5
            )
            runner.register(youtube_scraper)
            
            # Run all registered scrapers
            logger.info(f"Running {len(runner.list_scrapers())} scraper(s)")
            results = runner.run_all()
            
            logger.info("Scraping completed successfully")
            
            # Print summary
            for scraper_name, result in results.items():
                if isinstance(result, list):
                    logger.info(f"{scraper_name}: {len(result)} items scraped")
            
            return 0
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
