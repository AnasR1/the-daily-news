# Scraper Pipeline Quick Start

## Add YouTube Channels

Edit `config/channels.txt` and add your channel URLs:

```
# YouTube channels to scrape
https://www.youtube.com/@your_channel
https://www.youtube.com/@another_channel
https://www.youtube.com/c/CustomName
https://www.youtube.com/channel/UCxxxxxxxxxx
```

**Format Support:**
- `@username` format
- `/c/CustomName` format  
- `/channel/UCXXXXX` format
- `/user/username` format

## Run the Pipeline

```bash
python -m app.scrapers
```

This will:
1. Read channels from `config/channels.txt`
2. Resolve URLs to YouTube channel IDs
3. Fetch latest videos and transcripts
4. Display results in console

## Add a New Scraper Type

### Step 1: Create Your Scraper

Create `app/scrapers/my_scraper.py`:

```python
from app.scrapers.base import BaseScraper
from typing import Any

class MyScraper(BaseScraper):
    def __init__(self, config):
        self.config = config
    
    @property
    def name(self) -> str:
        return "my_scraper"
    
    def run(self) -> Any:
        # Your scraping logic here
        return results
```

### Step 2: Register in Pipeline

In `app/scrapers/__main__.py`, add to the `main()` function:

```python
from app.scrapers.my_scraper import MyScraper

# After creating runner:
my_scraper = MyScraper(config=...)
runner.register(my_scraper)
```

### Step 3: Run

```bash
python -m app.scrapers
```

Your scraper runs alongside YouTube scraper automatically!

## Project Files

| File | Purpose |
|------|---------|
| `config/channels.txt` | Channel configuration |
| `app/scrapers/base.py` | Abstract scraper base class |
| `app/scrapers/runner.py` | Pipeline orchestrator |
| `app/scrapers/__main__.py` | CLI entry point |
| `app/scrapers/youtube_scraper.py` | YouTube implementation |
| `SCRAPER_PIPELINE.md` | Full documentation |

## Architecture

```
ScraperRunner
├── YouTubeScraper (inherits BaseScraper)
├── RSSFeedScraper (inherits BaseScraper)  ← Add your scrapers here
└── MyCustomScraper (inherits BaseScraper)
```

All scrapers run through the same pipeline automatically!

## Key Principles

✅ **Extensible** - Add scrapers without modifying existing code  
✅ **Configurable** - Channels in config file, not hardcoded  
✅ **Robust** - One scraper failing doesn't crash the pipeline  
✅ **Logged** - All operations tracked for debugging  

See `SCRAPER_PIPELINE.md` for detailed documentation.
