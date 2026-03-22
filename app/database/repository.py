"""Database repository for video operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Video
from app.logging_config import get_logger

logger = get_logger(__name__)


class VideoRepository:
    """Repository for database operations on videos."""
    
    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self.db = db
    
    def create_video(
        self,
        video_id: str,
        title: str,
        url: str,
        description: Optional[str] = None,
        published_at: Optional[object] = None,
        transcript: Optional[str] = None,
        has_transcript: bool = False
    ) -> Video:
        """Create and save a new video to the database."""
        video = Video(
            video_id=video_id,
            title=title,
            url=url,
            description=description,
            published_at=published_at,
            transcript=transcript,
            has_transcript=has_transcript
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        logger.info(f"Created video: {video_id} - {title}")
        return video
    
    def get_video_by_id(self, video_id: str) -> Optional[Video]:
        """Get a video by its YouTube video ID."""
        return self.db.query(Video).filter(Video.video_id == video_id).first()
    
    def get_all_videos(self, limit: Optional[int] = None) -> List[Video]:
        """Get all videos from the database."""
        query = self.db.query(Video).order_by(Video.published_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_videos_with_transcript(self) -> List[Video]:
        """Get all videos that have transcripts."""
        return self.db.query(Video).filter(Video.has_transcript == True).all()
    
    def update_video_transcript(
        self,
        video_id: str,
        transcript: str
    ) -> Optional[Video]:
        """Update a video's transcript."""
        video = self.get_video_by_id(video_id)
        if video:
            video.transcript = transcript
            video.has_transcript = True
            self.db.commit()
            self.db.refresh(video)
            logger.info(f"Updated transcript for video: {video_id}")
        return video
    
    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists in the database."""
        return self.db.query(Video).filter(Video.video_id == video_id).first() is not None
    
    def delete_video(self, video_id: str) -> bool:
        """Delete a video from the database."""
        video = self.get_video_by_id(video_id)
        if video:
            self.db.delete(video)
            self.db.commit()
            logger.info(f"Deleted video: {video_id}")
            return True
        return False
