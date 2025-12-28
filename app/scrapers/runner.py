"""Scraper runner for managing and executing multiple scrapers.

This module provides a pipeline for running scrapers in sequence,
with logging and error handling for robustness.
"""
import logging
from typing import Dict, List, Any
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ScraperRunner:
    """Manages and executes registered scrapers."""

    def __init__(self):
        """Initialize the scraper runner."""
        self._scrapers: Dict[str, BaseScraper] = {}

    def register(self, scraper: BaseScraper) -> None:
        """Register a scraper.
        
        Args:
            scraper: Instance of a BaseScraper subclass
        """
        if not isinstance(scraper, BaseScraper):
            raise TypeError(
                f"Scraper must be an instance of BaseScraper, got {type(scraper)}"
            )
        
        self._scrapers[scraper.name] = scraper
        logger.info(f"Registered scraper: {scraper.name}")

    def unregister(self, name: str) -> None:
        """Unregister a scraper by name.
        
        Args:
            name: Name of the scraper to remove
        """
        if name in self._scrapers:
            del self._scrapers[name]
            logger.info(f"Unregistered scraper: {name}")

    def list_scrapers(self) -> List[str]:
        """List all registered scraper names.
        
        Returns:
            List of scraper names
        """
        return list(self._scrapers.keys())

    def run(self, scraper_name: str, *args, **kwargs) -> Any:
        """Run a specific scraper.
        
        Args:
            scraper_name: Name of the scraper to run
            *args: Positional arguments to pass to the scraper
            **kwargs: Keyword arguments to pass to the scraper
            
        Returns:
            Result from the scraper
            
        Raises:
            ValueError: If scraper not found
        """
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
            return result
        except Exception as e:
            logger.error(f"Scraper '{scraper_name}' failed: {e}", exc_info=True)
            raise

    def run_all(self, *args, **kwargs) -> Dict[str, Any]:
        """Run all registered scrapers sequentially.
        
        Args:
            *args: Positional arguments to pass to each scraper
            **kwargs: Keyword arguments to pass to each scraper
            
        Returns:
            Dictionary mapping scraper names to their results.
            Scrapers that fail are excluded from the result.
        """
        results = {}
        
        for scraper_name in self.list_scrapers():
            try:
                results[scraper_name] = self.run(scraper_name, *args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Skipping scraper '{scraper_name}' due to error: {e}"
                )
        
        return results
