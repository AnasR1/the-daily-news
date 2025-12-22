"""YouTube scraper using channel RSS + youtube-transcript-api.

This module provides a unified, object-oriented interface for fetching videos
and transcripts from YouTube channels using RSS feeds and the YouTube Transcript API.

Classes:
- YouTubeScraper: Main class for YouTube operations

Notes:
- Does NOT create or write to a database. Returns plain Python structures.
- Requires `feedparser`, `requests`, and `youtube-transcript-api` installed.
"""
from typing import List, Dict, Optional
import re
import requests
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable


class YouTubeScraper:
    """Unified interface for fetching YouTube videos and transcripts."""
    
    RSS_CHANNEL_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
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
        # Remove trailing slashes
        url = url.rstrip("/")
        
        # Direct channel ID URL
        channel_match = re.search(r'(?:youtube\.com|youtu\.be)/channel/([a-zA-Z0-9_-]+)', url)
        if channel_match:
            return channel_match.group(1)
        
        # @username format (requires additional lookup)
        username_match = re.search(r'(?:youtube\.com|youtu\.be)/@([a-zA-Z0-9_-]+)', url)
        if username_match:
            username = username_match.group(1)
            return YouTubeScraper._resolve_username_to_channel_id(username)
        
        # /c/CustomName format (requires additional lookup)
        custom_name_match = re.search(r'(?:youtube\.com|youtu\.be)/c/([a-zA-Z0-9_-]+)', url)
        if custom_name_match:
            custom_name = custom_name_match.group(1)
            return YouTubeScraper._resolve_custom_url_to_channel_id(custom_name)
        
        # /user/username format (requires additional lookup)
        user_match = re.search(r'(?:youtube\.com|youtu\.be)/user/([a-zA-Z0-9_-]+)', url)
        if user_match:
            username = user_match.group(1)
            return YouTubeScraper._resolve_username_to_channel_id(username)
        
        return None
    
    @staticmethod
    def _resolve_username_to_channel_id(username: str) -> Optional[str]:
        """Resolve @username to channel ID by fetching the channel page.
        
        Args:
            username: YouTube username without @ symbol
            
        Returns:
            Channel ID if found, None otherwise
        """
        try:
            url = f"https://www.youtube.com/@{username}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            # Search for channel ID in the page content
            match = re.search(r'"browseId":"(UC[a-zA-Z0-9_-]+)"', resp.text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None
    
    @staticmethod
    def _resolve_custom_url_to_channel_id(custom_url: str) -> Optional[str]:
        """Resolve /c/CustomName to channel ID by fetching the channel page.
        
        Args:
            custom_url: Custom channel URL name
            
        Returns:
            Channel ID if found, None otherwise
        """
        try:
            url = f"https://www.youtube.com/c/{custom_url}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            # Search for channel ID in the page content
            match = re.search(r'"browseId":"(UC[a-zA-Z0-9_-]+)"', resp.text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None
    
    @staticmethod
    def _parse_entry_to_video(entry) -> Dict:
        """Parse RSS entry to video dict.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Dict with keys: video_id, title, link, published, summary
        """
        # feedparser maps <yt:videoId> to entry.get('yt_videoid') in many cases
        video_id = entry.get("yt_videoid")
        link = entry.get("link") or ""
        if not video_id:
            # try extract from link: watch?v=<id>
            if "v=" in link:
                video_id = link.split("v=")[-1].split("&")[0]
            else:
                # last path segment
                video_id = link.rstrip("/").split("/")[-1]

        return {
            "video_id": video_id,
            "title": entry.get("title"),
            "link": link,
            "published": entry.get("published"),
            "summary": entry.get("summary"),
        }
    
    @staticmethod
    def fetch_channel_feed(channel_id: str, max_results: int = 5) -> List[Dict]:
        """Fetch the channel uploads RSS and return up to `max_results` videos.

        Args:
            channel_id: YouTube channel ID (not username).
            max_results: maximum number of videos to return.

        Returns:
            List of video dicts with keys: video_id, title, link, published, summary
        """
        url = YouTubeScraper.RSS_CHANNEL_FEED.format(channel_id=channel_id)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        entries = feed.entries or []
        videos = []
        for entry in entries[:max_results]:
            videos.append(YouTubeScraper._parse_entry_to_video(entry))
        return videos
    
    @staticmethod
    def get_latest_videos(channel_ids: List[str], max_results_per_channel: int = 5) -> List[Dict]:
        """Get latest videos across multiple channels.

        Args:
            channel_ids: list of YouTube channel IDs
            max_results_per_channel: how many videos per channel to fetch

        Returns:
            List of video dicts with an added `channel_id` key.
        """
        all_videos = []
        for cid in channel_ids:
            try:
                vids = YouTubeScraper.fetch_channel_feed(cid, max_results=max_results_per_channel)
            except Exception:
                vids = []
            for v in vids:
                v["channel_id"] = cid
                all_videos.append(v)
        return all_videos
    
    @staticmethod
    def get_transcript(video_id: str, languages=("en",)) -> Optional[str]:
        """Return concatenated transcript text for a video, or None if unavailable.
        
        Args:
            video_id: YouTube video ID
            languages: Tuple of language codes to try in order (e.g., ("en", "es"))
            
        Returns:
            Transcript text as a string, or None if unavailable
        """
        try:
            parts = YouTubeTranscriptApi.list_transcripts(video_id)
            # prefer the first matching language
            transcript = None
            for lang in languages:
                if parts.find_transcript([lang]):
                    transcript_list = parts.find_transcript([lang]).fetch()
                    transcript = "\n".join([p.get("text", "") for p in transcript_list])
                    break
            if transcript is None:
                # fallback: pick first available transcript
                first = parts.find_transcript([parts._translations[0].language_code]) if parts._translations else None
                if first:
                    transcript_list = first.fetch()
                    transcript = "\n".join([p.get("text", "") for p in transcript_list])
            return transcript
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_videos_with_transcripts(
        channel_ids: List[str], 
        max_results_per_channel: int = 3
    ) -> List[Dict]:
        """Fetch latest videos from channels and get their transcripts.
        
        Args:
            channel_ids: List of YouTube channel IDs
            max_results_per_channel: Number of videos per channel to process
            
        Returns:
            List of video dicts with an added 'transcript' key containing the 
            transcript text or None if unavailable.
        """
        videos = YouTubeScraper.get_latest_videos(channel_ids, max_results_per_channel)
        
        for video in videos:
            video_id = video.get("video_id")
            video["transcript"] = YouTubeScraper.get_transcript(video_id) if video_id else None
        
        return videos


if __name__ == "__main__":
    # Example: using direct channel IDs
    channels = [
        "UCAuUUnT6oDeKwE6v1NGQxug",  # TED Ed
    ]
    
    # Example 1: Get videos with transcripts
    videos = YouTubeScraper.get_videos_with_transcripts(channels, max_results_per_channel=3)
    for v in videos:
        print(v["title"], v["link"])
        t = v.get("transcript") or "(no transcript)"
        print(t[:300].replace('\n', ' '))
        print("---")
    
    # Example 2: Resolve channel ID from URL
    print("\n\nResolving channel IDs from URLs:")
    test_urls = [
        "https://www.youtube.com/channel/UCAuUUnT6oDeKwE6v1NGQxug",
        "https://www.youtube.com/@TED",
    ]
    for url in test_urls:
        channel_id = YouTubeScraper.get_channel_id_from_url(url)
        print(f"{url} -> {channel_id}")

