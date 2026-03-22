"""SQLAlchemy database models for storing scraped data."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from app.database import Base


class Video(Base):
    """SQLAlchemy model for YouTube video information."""
    
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    transcript = Column(Text, nullable=True)
    has_transcript = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Video(id={self.id}, video_id={self.video_id}, title={self.title})>"
