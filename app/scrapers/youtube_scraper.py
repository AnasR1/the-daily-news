"""YouTube scraper using channel RSS + youtube-transcript-api.

This module fetches the channel uploads RSS feed to get the latest videos
(no YouTube Data API key required) and uses `youtube_transcript_api` to
retrieve transcripts when available.

Functions:
- get_latest_videos(channel_ids, max_results=5)
- get_transcript(video_id, languages=("en",))

Notes:
- Does NOT create or write to a database. Returns plain Python structures.
- Requires `feedparser`, `requests`, and `youtube-transcript-api` installed.
"""
from typing import List, Dict, Optional
import requests
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

RSS_CHANNEL_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _parse_entry_to_video(entry) -> Dict:
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


def fetch_channel_feed(channel_id: str, max_results: int = 5) -> List[Dict]:
    """Fetch the channel uploads RSS and return up to `max_results` videos.

    Args:
        channel_id: YouTube channel ID (not username).
        max_results: maximum number of videos to return.

    Returns:
        List of video dicts with keys: video_id, title, link, published, summary
    """
    url = RSS_CHANNEL_FEED.format(channel_id=channel_id)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    entries = feed.entries or []
    videos = []
    for entry in entries[:max_results]:
        videos.append(_parse_entry_to_video(entry))
    return videos


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
            vids = fetch_channel_feed(cid, max_results=max_results_per_channel)
        except Exception:
            vids = []
        for v in vids:
            v["channel_id"] = cid
            all_videos.append(v)
    return all_videos


def get_transcript(video_id: str, languages=("en",)) -> Optional[str]:
    """Return concatenated transcript text for a video, or None if unavailable."""
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


if __name__ == "__main__":
    channels = [
        # replace with real channel IDs
        #"UCrPseYLGpNygVi34QpGNqpA", #ludwig
        "UCAuUUnT6oDeKwE6v1NGQxug", #TED Ed
    ]
    videos = get_latest_videos(channels, max_results_per_channel=3)
    for v in videos:
        print(v["title"], v["link"])
        t = get_transcript(v["video_id"]) or "(no transcript)"
        print(t[:300].replace('\n', ' '))
        print("---")
