"""Main entry point for running scrapers.

This module demonstrates how to use the ScraperRunner to execute scrapers.
"""
import logging
import sys
from pathlib import Path

from app.scrapers.runner import ScraperRunner
from app.scrapers.youtube_scraper import YouTubeScraper

logger = logging.getLogger(__name__)


def load_channels_from_config(config_path: str) -> list[str]:
    """Load channel URLs from config file.
    
    Args:
        config_path: Path to the channels config file
        
    Returns:
        List of channel URLs (non-comment, non-empty lines)
    """
    config = Path(config_path)
    
    if not config.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    channels = []
    with open(config, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                channels.append(line)
    
    return channels


def resolve_channel_ids(channel_urls: list[str]) -> list[str]:
    """Resolve channel URLs to channel IDs.
    
    Args:
        channel_urls: List of YouTube channel URLs
        
    Returns:
        List of resolved channel IDs
    """
    channel_ids = []
    
    for url in channel_urls:
        try:
            channel_id = YouTubeScraper.get_channel_id_from_url(url)
            if channel_id:
                channel_ids.append(channel_id)
                logger.info(f"Resolved {url} to {channel_id}")
            else:
                logger.warning(f"Could not resolve channel ID from: {url}")
        except Exception as e:
            logger.error(f"Error resolving {url}: {e}")
    
    return channel_ids


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    try:
        # Load channels from config
        config_path = "config/channels.txt"
        logger.info(f"Loading channels from {config_path}")
        channel_urls = load_channels_from_config(config_path)
        
        if not channel_urls:
            logger.error("No channels configured in config/channels.txt")
            return 1
        
        logger.info(f"Found {len(channel_urls)} channel(s) to process")
        
        # Resolve URLs to channel IDs
        channel_ids = resolve_channel_ids(channel_urls)
        
        if not channel_ids:
            logger.error("Could not resolve any channels to IDs")
            return 1
        
        # Create and register scrapers
        runner = ScraperRunner()
        youtube_scraper = YouTubeScraper(
            channel_ids=channel_ids,
            max_results_per_channel=3
        )
        runner.register(youtube_scraper)
        
        # Run the scraper
        logger.info(f"Running registered scrapers: {runner.list_scrapers()}")
        results = runner.run_all()
        
        # Display results
        for scraper_name, data in results.items():
            logger.info(f"\n{scraper_name} scraper results:")
            if isinstance(data, list):
                for video, transcript in data:
                    print(f"\n  Title: {video.title}")
                    print(f"  URL: {video.url}")
                    print(f"  Video ID: {video.video_id}")
                    if video.published_at:
                        print(f"  Published: {video.published_at}")
                    
                    if transcript:
                        preview = transcript.text[:200].replace("\n", " ")
                        print(f"  Transcript: {preview}...")
                    else:
                        print("  Transcript: (not available)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
