"""YouTube scraper using channel RSS + youtube-transcript-api.

This module provides a unified, object-oriented interface for fetching videos
and transcripts from YouTube channels using RSS feeds and the YouTube Transcript API.

Classes:
- YouTubeScraper: Main scraper class for YouTube operations
- ChannelVideo: Pydantic model for channel videos
- Transcript: Pydantic model for transcripts

Notes:
- Does NOT create or write to a database. Returns plain Python structures.
- Requires `feedparser`, `requests`, `pydantic`, and `youtube-transcript-api` installed.
"""
import logging
import re
from typing import List, Optional
from datetime import datetime

import requests
import feedparser
from pydantic import BaseModel
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ChannelVideo(BaseModel):
    """Pydantic model for a YouTube channel video."""

    title: str
    url: str
    video_id: str
    published_at: Optional[datetime] = None
    description: Optional[str] = None


class Transcript(BaseModel):
    """Pydantic model for a YouTube video transcript."""

    text: str


class YouTubeScraper(BaseScraper):
    """Scraper for fetching YouTube videos and transcripts."""

    RSS_CHANNEL_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    YOUTUBE_BASE_URL = "https://www.youtube.com"
    CHANNEL_ID_PATTERN = r"(?:youtube\.com|youtu\.be)/channel/([a-zA-Z0-9_-]+)"
    BROWSE_ID_PATTERN = r'"browseId":"(UC[a-zA-Z0-9_-]+)"'
    REQUEST_TIMEOUT = 10

    def __init__(self, channel_ids: List[str], max_results_per_channel: int = 5):
        """Initialize YouTubeScraper.
        
        Args:
            channel_ids: List of YouTube channel IDs to scrape
            max_results_per_channel: Maximum videos to fetch per channel
        """
        self.channel_ids = channel_ids
        self.max_results_per_channel = max_results_per_channel

    @property
    def name(self) -> str:
        """Return the scraper name."""
        return "youtube"

    def run(self) -> List[tuple[ChannelVideo, Optional[Transcript]]]:
        """Execute the scraper.
        
        Returns:
            List of tuples containing ChannelVideo and optional Transcript
        """
        return self.get_videos_with_transcripts(
            self.channel_ids, self.max_results_per_channel
        )

    @staticmethod
    def get_channel_id_from_url(url: str) -> Optional[str]:
        """Extract real channel ID from various YouTube URL formats.

        Handles:
        - https://youtube.com/@username
        - https://youtube.com/c/CustomName
        - https://youtube.com/channel/UCxxxxxxxxxx
        - https://youtube.com/user/username
        - https://www.youtube.com/... (with www)

        Args:
            url: YouTube channel URL

        Returns:
            Channel ID if found, None otherwise
        """
        url = url.rstrip("/")

        # Direct channel ID URL
        if channel_id := YouTubeScraper._extract_from_pattern(
            url, YouTubeScraper.CHANNEL_ID_PATTERN
        ):
            return channel_id

        # @username format
        username_match = re.search(
            r"(?:youtube\.com|youtu\.be)/@([a-zA-Z0-9_-]+)", url
        )
        if username_match:
            return YouTubeScraper._resolve_username_to_channel_id(
                username_match.group(1)
            )

        # /c/CustomName format
        custom_match = re.search(r"(?:youtube\.com|youtu\.be)/c/([a-zA-Z0-9_-]+)", url)
        if custom_match:
            return YouTubeScraper._resolve_custom_url_to_channel_id(
                custom_match.group(1)
            )

        # /user/username format
        user_match = re.search(r"(?:youtube\.com|youtu\.be)/user/([a-zA-Z0-9_-]+)", url)
        if user_match:
            return YouTubeScraper._resolve_username_to_channel_id(
                user_match.group(1)
            )

        return None

    @staticmethod
    def _extract_from_pattern(text: str, pattern: str) -> Optional[str]:
        """Extract first group from regex pattern match.

        Args:
            text: Text to search in
            pattern: Regex pattern with one capture group

        Returns:
            First captured group or None
        """
        match = re.search(pattern, text)
        return match.group(1) if match else None

    @staticmethod
    def _fetch_channel_page(url: str) -> Optional[str]:
        """Fetch channel page content.

        Args:
            url: Full URL to fetch

        Returns:
            Page content or None if request fails
        """
        try:
            response = requests.get(url, timeout=YouTubeScraper.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return None

    @staticmethod
    def _resolve_username_to_channel_id(username: str) -> Optional[str]:
        """Resolve @username to channel ID by fetching the channel page.

        Args:
            username: YouTube username without @ symbol

        Returns:
            Channel ID if found, None otherwise
        """
        url = f"{YouTubeScraper.YOUTUBE_BASE_URL}/@{username}"
        if content := YouTubeScraper._fetch_channel_page(url):
            return YouTubeScraper._extract_from_pattern(
                content, YouTubeScraper.BROWSE_ID_PATTERN
            )
        return None

    @staticmethod
    def _resolve_custom_url_to_channel_id(custom_url: str) -> Optional[str]:
        """Resolve /c/CustomName to channel ID by fetching the channel page.

        Args:
            custom_url: Custom channel URL name

        Returns:
            Channel ID if found, None otherwise
        """
        url = f"{YouTubeScraper.YOUTUBE_BASE_URL}/c/{custom_url}"
        if content := YouTubeScraper._fetch_channel_page(url):
            return YouTubeScraper._extract_from_pattern(
                content, YouTubeScraper.BROWSE_ID_PATTERN
            )
        return None

    @staticmethod
    def _extract_video_id_from_link(link: str) -> Optional[str]:
        """Extract video ID from a YouTube link.

        Args:
            link: YouTube URL

        Returns:
            Video ID or None
        """
        if "v=" in link:
            return link.split("v=")[-1].split("&")[0]
        return link.rstrip("/").split("/")[-1] if link else None

    @staticmethod
    def _parse_entry_to_video(entry) -> ChannelVideo:
        """Parse RSS entry to ChannelVideo model.

        Args:
            entry: feedparser entry object

        Returns:
            ChannelVideo instance
        """
        # feedparser maps <yt:videoId> to entry.get('yt_videoid')
        video_id = entry.get("yt_videoid")
        link = entry.get("link") or ""

        if not video_id:
            video_id = YouTubeScraper._extract_video_id_from_link(link)

        return ChannelVideo(
            video_id=video_id,
            title=entry.get("title"),
            url=link,
            published_at=entry.get("published"),
            description=entry.get("summary"),
        )

    @staticmethod
    def fetch_channel_feed(
        channel_id: str, max_results: int = 5
    ) -> List[ChannelVideo]:
        """Fetch the channel uploads RSS and return up to `max_results` videos.

        Args:
            channel_id: YouTube channel ID (not username).
            max_results: maximum number of videos to return.

        Returns:
            List of ChannelVideo instances

        Raises:
            requests.RequestException: If RSS feed fetch fails
        """
        url = YouTubeScraper.RSS_CHANNEL_FEED.format(channel_id=channel_id)
        response = requests.get(url, timeout=YouTubeScraper.REQUEST_TIMEOUT)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        entries = feed.entries or []

        return [
            YouTubeScraper._parse_entry_to_video(entry)
            for entry in entries[:max_results]
        ]

    @staticmethod
    def get_latest_videos(
        channel_ids: List[str], max_results_per_channel: int = 5
    ) -> List[ChannelVideo]:
        """Get latest videos across multiple channels.

        Args:
            channel_ids: list of YouTube channel IDs
            max_results_per_channel: how many videos per channel to fetch

        Returns:
            List of ChannelVideo instances
        """
        all_videos = []

        for channel_id in channel_ids:
            try:
                videos = YouTubeScraper.fetch_channel_feed(
                    channel_id, max_results=max_results_per_channel
                )
                all_videos.extend(videos)
            except requests.RequestException as e:
                logger.warning(
                    f"Failed to fetch videos from channel {channel_id}: {e}"
                )
            except Exception as e:
                logger.error(f"Unexpected error fetching channel {channel_id}: {e}")

        return all_videos

    @staticmethod
    def get_transcript(video_id: str) -> Optional[Transcript]:
        """Fetch transcript for a video.

        By default, fetches the English transcript only.

        Args:
            video_id: YouTube video ID (not the full URL)

        Returns:
            Transcript instance, or None if unavailable
        """
        try:
            api = YouTubeTranscriptApi()
            fetched_transcript = api.fetch(video_id)
            text = "\n".join(snippet.text for snippet in fetched_transcript)
            return Transcript(text=text)
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            logger.debug(f"No transcript available for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            return None

    @staticmethod
    def get_videos_with_transcripts(
        channel_ids: List[str], max_results_per_channel: int = 3
    ) -> List[tuple[ChannelVideo, Optional[Transcript]]]:
        """Fetch latest videos from channels and get their transcripts.

        Args:
            channel_ids: List of YouTube channel IDs
            max_results_per_channel: Number of videos per channel to process

        Returns:
            List of tuples containing ChannelVideo and optional Transcript.
        """
        videos = YouTubeScraper.get_latest_videos(
            channel_ids, max_results_per_channel
        )
        return [
            (video, YouTubeScraper.get_transcript(video.video_id)) for video in videos
        ]
