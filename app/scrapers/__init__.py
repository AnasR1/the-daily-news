"""Scrapers package for the AI News Aggregator.

This package contains per-source scrapers (YouTube, RSS, etc.) and the runner
for executing them. All scrapers inherit from BaseScraper and are executed
via the ScraperRunner.
"""

from app.scrapers.base import BaseScraper
from app.scrapers.runner import ScraperRunner
from app.scrapers.youtube_scraper import YouTubeScraper, ChannelVideo, Transcript

__all__ = [
    "BaseScraper",
    "ScraperRunner",
    "YouTubeScraper",
    "ChannelVideo",
    "Transcript",
]
