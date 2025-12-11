"""
Database Models for AI Audiobook Studio

This module defines SQLAlchemy ORM models for project management,
including support for TTS presets.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .session import Base


class Project(Base):
    """
    Audiobook project model.
    
    Represents a single audiobook generation project, including
    source file information, TTS configuration, and processing status.
    """
    __tablename__ = "projects"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Processing status: processing, completed, failed
    status = Column(String, default="processing")
    
    # File paths
    text_path = Column(String)
    audio_path = Column(String, nullable=True)
    voice_ref_path = Column(String)
    
    # Source file metadata
    source_type = Column(
        String,
        default="txt",
        comment="Source file type: txt"
    )
    content_type = Column(
        String,
        default="fiction",
        comment="Content category: fiction, nonfiction, custom"
    )
    
    # TTS Preset Configuration
    preset_id = Column(
        String,
        default="en_fiction",
        comment="TTS preset identifier (e.g., en_fiction, tr_nonfiction)"
    )

    # TTS Model Engine (xtts only)
    tts_model = Column(
        String,
        default="xtts",
        comment="TTS engine to use: 'xtts'"
    )
    
    # XTTS v2 Parameters
    # These can override preset values if custom preset is used
    language = Column(String, default="en")
    speed = Column(Float, default=1.0)
    temperature = Column(Float, default=0.75)
    top_k = Column(Integer, default=50)
    top_p = Column(Float, default=0.85)
    repetition_penalty = Column(Float, default=2.0)

    # Cancellation / control
    # When True, background processing should stop as soon as possible.
    is_cancelled = Column(Boolean, default=False)
    
    # Resume tracking
    resume_count = Column(
        Integer,
        default=0,
        comment="Number of times the project has been resumed"
    )
    last_error = Column(
        String,
        nullable=True,
        comment="Last error message encountered during processing"
    )
    failed_chunks = Column(
        String,
        nullable=True,
        comment="JSON array of chunk indices that failed after max retries (e.g., '[1, 5, 23]')"
    )
    
    # Relationships
    chunks = relationship(
        "Chunk",
        back_populates="project",
        cascade="all, delete-orphan"
    )


class Chunk(Base):
    """
    Text chunk model for audio generation.
    
    Represents a segment of text to be converted to audio.
    Represents a segment of text to be converted to audio.
    """
    __tablename__ = "chunks"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Chunk ordering and identification
    index = Column(
        Integer,
        comment="Sequential order of chunk within project"
    )
    
    # EPUB chapter support
    chapter_title = Column(
        String,
        nullable=True,
        comment="Chapter title extracted from EPUB (if applicable)"
    )
    chapter_order = Column(
        Integer,
        nullable=True,
        comment="Original chapter number from EPUB structure"
    )
    
    # Content and processing
    text_content = Column(String)
    is_processed = Column(Boolean, default=False)
    chunk_audio_path = Column(String, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="chunks")
