from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .session import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing") # processing, completed, failed
    text_path = Column(String)
    audio_path = Column(String, nullable=True)
    voice_ref_path = Column(String)
    
    chunks = relationship("Chunk", back_populates="project")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    index = Column(Integer)
    text_content = Column(String)
    is_processed = Column(Boolean, default=False)
    chunk_audio_path = Column(String, nullable=True)

    project = relationship("Project", back_populates="chunks")
