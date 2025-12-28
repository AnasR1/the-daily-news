# Scraper Pipeline Documentation

## Overview

The scraper pipeline provides an extensible framework for running multiple data-gathering scrapers. It's designed to be easy to add new scrapers without modifying existing code.

## Architecture

### Core Components

1. **`BaseScraper`** (`app/scrapers/base.py`)
   - Abstract base class for all scrapers
   - Requires implementing `name` property and `run()` method
   - Ensures consistent interface across all scrapers

2. **`ScraperRunner`** (`app/scrapers/runner.py`)
   - Manages registration and execution of scrapers
   - Supports running individual or all scrapers
   - Provides logging and error handling

3. **`YouTubeScraper`** (`app/scrapers/youtube_scraper.py`)
   - First implementation inheriting from `BaseScraper`
   - Fetches videos and transcripts from YouTube channels
   - Reads channels from `config/channels.txt`

## Configuration

### Channel Configuration (`config/channels.txt`)

Store YouTube channels to scrape, one per line. Supports multiple URL formats:

```
# YouTube channels to scrape
# Comments are lines starting with #
https://www.youtube.com/@channelname
https://www.youtube.com/c/CustomName
https://www.youtube.com/channel/UCxxxxxxxxxx
https://www.youtube.com/user/username
```

- Empty lines are ignored
- Lines starting with `#` are comments
- URLs are automatically resolved to channel IDs

## Usage

### Running the Pipeline

```bash
# Run all registered scrapers from project root
python -m app.scrapers
```

This will:
1. Load channels from `config/channels.txt`
2. Resolve URLs to channel IDs
3. Create a YouTubeScraper instance
4. Execute the scraper and display results

### Programmatic Usage

```python
from app.scrapers import ScraperRunner, YouTubeScraper

# Create runner
runner = ScraperRunner()

# Register a scraper
youtube = YouTubeScraper(
    channel_ids=["UCxxxxxxxxxx"],
    max_results_per_channel=5
)
runner.register(youtube)

# Run specific scraper
results = runner.run("youtube")

# Or run all registered scrapers
all_results = runner.run_all()
```

## Creating a New Scraper

To add a new scraper (e.g., RSS feeds):

### 1. Create the Scraper Class

```python
# app/scrapers/rss_scraper.py
from app.scrapers.base import BaseScraper
from typing import List, Any

class RSSFeedScraper(BaseScraper):
    """Scraper for RSS feeds."""
    
    def __init__(self, feed_urls: List[str]):
        self.feed_urls = feed_urls
    
    @property
    def name(self) -> str:
        return "rss_feeds"
    
    def run(self) -> Any:
        """Fetch and parse RSS feeds."""
        # Implementation here
        results = []
        for url in self.feed_urls:
            # Parse feed
            pass
        return results
```

### 2. Register in Your Pipeline

```python
from app.scrapers import ScraperRunner
from app.scrapers.rss_scraper import RSSFeedScraper

runner = ScraperRunner()

# Register YouTube scraper
youtube = YouTubeScraper(channel_ids=[...])
runner.register(youtube)

# Register RSS scraper
rss = RSSFeedScraper(feed_urls=[...])
runner.register(rss)

# Run both
results = runner.run_all()
```

### 3. Update `app/scrapers/__init__.py`

```python
from app.scrapers.rss_scraper import RSSFeedScraper

__all__ = [
    "BaseScraper",
    "ScraperRunner",
    "YouTubeScraper",
    "RSSFeedScraper",  # Add here
    "ChannelVideo",
    "Transcript",
]
```

## Project Structure

```
the-daily-news/
├── config/
│   └── channels.txt          # Channel configuration
├── app/
│   └── scrapers/
│       ├── __init__.py       # Package exports
│       ├── __main__.py       # Entry point for pipeline
│       ├── base.py           # Base scraper class
│       ├── runner.py         # Pipeline runner
│       ├── youtube_scraper.py # YouTube scraper implementation
│       └── youtube.py        # Deprecated (legacy compatibility)
└── ...
```

## Key Design Principles

1. **Extensibility**: New scrapers inherit from `BaseScraper` with minimal overhead
2. **Loose Coupling**: Scrapers don't depend on each other
3. **Configuration-Driven**: Channel lists are external, not hardcoded
4. **Error Handling**: `ScraperRunner` gracefully handles individual scraper failures
5. **Logging**: All operations are logged for debugging and monitoring

## Error Handling

- Individual scraper failures don't stop the pipeline
- Errors are logged with full traceback for debugging
- Failed scrapers are excluded from results but don't crash the application

## Future Enhancements

- Config file validation
- Scheduling (run scrapers on a timer)
- Data persistence (save results to database)
- Multiple config profiles for different environments
- Scraper metrics and monitoring
