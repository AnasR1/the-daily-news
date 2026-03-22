"""Base scraper interface for extensibility."""
from abc import ABC, abstractmethod
from typing import Any, List


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the scraper."""
        pass

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the scraper."""
        pass
