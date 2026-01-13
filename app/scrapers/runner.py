"""Scraper runner for managing and executing multiple scrapers."""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.scrapers.base import BaseScraper
from app.database import SessionLocal
from app.database.repository import VideoRepository
from app.logging_config import get_logger

logger = get_logger(__name__)


class ScraperRunner:
    """Manages and executes registered scrapers."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize the scraper runner with optional database session."""
        self._scrapers: Dict[str, BaseScraper] = {}
        self.db = db
        self.video_repo: Optional[VideoRepository] = None
        
        if self.db:
            self.video_repo = VideoRepository(self.db)

    def register(self, scraper: BaseScraper) -> None:
        """Register a scraper instance."""
        if not isinstance(scraper, BaseScraper):
            raise TypeError(
                f"Scraper must be an instance of BaseScraper, got {type(scraper)}"
            )
        
        self._scrapers[scraper.name] = scraper
        logger.info(f"Registered scraper: {scraper.name}")

    def unregister(self, name: str) -> None:
        """Unregister a scraper by name."""
        if name in self._scrapers:
            del self._scrapers[name]
            logger.info(f"Unregistered scraper: {name}")

    def list_scrapers(self) -> List[str]:
        """Return list of all registered scraper names."""
        return list(self._scrapers.keys())

    def run(self, scraper_name: str, *args, **kwargs) -> Any:
        """Run a specific scraper."""
        if scraper_name not in self._scrapers:
            raise ValueError(
                f"Scraper '{scraper_name}' not found. "
                f"Available: {self.list_scrapers()}"
            )
        
        scraper = self._scrapers[scraper_name]
        logger.info(f"Running scraper: {scraper_name}")
        
        try:
            result = scraper.run(*args, **kwargs)
            logger.info(f"Scraper '{scraper_name}' completed successfully")
            
            # Save videos to database if repository is available
            if self.video_repo and isinstance(result, list):
                self._save_videos_to_db(result)
            
            return result
        except Exception as e:
            logger.error(f"Scraper '{scraper_name}' failed: {e}", exc_info=True)
            raise
    
    def _save_videos_to_db(self, videos: List[Any]) -> None:
        """Save videos to the database."""
        saved_count = 0
        skipped_count = 0
        
        for video in videos:
            try:
                if self.video_repo.video_exists(video.video_id):
                    logger.debug(f"Video {video.video_id} already exists, skipping")
                    skipped_count += 1
                    continue
                
                self.video_repo.create_video(
                    video_id=video.video_id,
                    title=video.title,
                    url=video.url,
                    description=video.description,
                    published_at=video.published_at
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save video {video.video_id}: {e}")
        
        logger.info(
            f"Saved {saved_count} videos to database "
            f"({skipped_count} already existed)"
        )

    def run_all(self, *args, **kwargs) -> Dict[str, Any]:
        """Run all registered scrapers sequentially."""
        results = {}
        
        for scraper_name in self.list_scrapers():
            try:
                results[scraper_name] = self.run(scraper_name, *args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Skipping scraper '{scraper_name}' due to error: {e}"
                )
        
        return results
