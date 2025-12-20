"""YouTube transcript service.

This module provides functionality to fetch transcripts from YouTube videos
using the YouTube scraper and YouTube Transcript API.

Functions:
- get_video_transcripts(channel_ids, max_results_per_channel=5)
- get_single_transcript(video_id, languages=("en",))
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.scrapers.youtube_scraper import get_latest_videos, get_transcript


def get_video_transcripts(
    channel_ids: List[str], 
    max_results_per_channel: int = 5
) -> List[Dict]:
    """Fetch latest videos from channels and get their transcripts.
    
    Args:
        channel_ids: List of YouTube channel IDs
        max_results_per_channel: Number of videos per channel to process
        
    Returns:
        List of video dicts with an added 'transcript' key containing the 
        transcript text or None if unavailable.
    """
    videos = get_latest_videos(channel_ids, max_results_per_channel)
    
    for video in videos:
        video_id = video.get("video_id")
        video["transcript"] = get_transcript(video_id) if video_id else None
    
    return videos


def get_single_transcript(
    video_id: str, 
    languages: tuple = ("en",)
) -> Optional[str]:
    """Get transcript for a single video.
    
    Args:
        video_id: YouTube video ID
        languages: Tuple of language codes to try in order (e.g., ("en", "es"))
        
    Returns:
        Transcript text as a string, or None if unavailable.
    """
    return get_transcript(video_id, languages=languages)
