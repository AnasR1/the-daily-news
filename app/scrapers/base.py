"""Base scraper interface for extensibility.

This module provides the abstract base class for all scrapers,
ensuring consistent interface and enabling easy addition of new scraper types.
"""
from abc import ABC, abstractmethod
from typing import Any, List


class BaseScraper(ABC):
    """Abstract base class for all scrapers.
    
    Subclasses must implement the run() method to define their scraping behavior.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the scraper."""
        pass

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the scraper.
        
        Returns:
            Scraper-specific results
        """
        pass
