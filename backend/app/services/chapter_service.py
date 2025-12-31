"""
Chapter Service Module

Manages chapter metadata and calculates timestamps.
"""

import logging
from typing import List, Dict
from dataclasses import dataclass
from sqlalchemy.orm import Session
from pydub import AudioSegment

from ..db.models import Chunk
from ..ai.chapter_detector import ChapterInfo

logger = logging.getLogger("ai_audiobook_studio")


@dataclass
class ChapterTimestamp:
    """Chapter with timestamp information."""
    title: str
    order: int
    timestamp_seconds: float
    timestamp_formatted: str  # HH:MM:SS format
    chunk_index: int  # Starting chunk index


class ChapterService:
    """
    Service for managing chapter metadata and timestamps.
    """
    
    def save_chapters(
        self,
        project_id: int,
        chapters: List[ChapterInfo],
        chunks: List[Chunk],
        db: Session
    ) -> None:
        """
        Save chapter information to chunks.
        
        Finds which chunk each chapter starts in and sets chapter_title
        and chapter_order on the Chunk model.
        
        Args:
            project_id: Project ID
            chapters: List of detected chapters
            chunks: List of chunks (ordered by index)
            db: Database session
        """
        if not chapters:
            logger.debug(f"No chapters detected for project {project_id}")
            return
        
        # Create a map of character position to chunk index
        # We need to find which chunk each chapter position falls into
        position_to_chunk = {}
        current_pos = 0
        
        for chunk in chunks:
            chunk_text = chunk.text_content or ""
            chunk_length = len(chunk_text)
            
            # Map all positions in this chunk to this chunk's index
            for pos in range(current_pos, current_pos + chunk_length):
                position_to_chunk[pos] = chunk.index
            
            current_pos += chunk_length + 1  # +1 for space/newline between chunks
        
        # Assign chapters to chunks
        chapters_assigned = 0
        for chapter in chapters:
            # Find the chunk that contains this chapter's position
            chunk_index = position_to_chunk.get(chapter.position)
            
            if chunk_index is not None:
                # Find the chunk object
                chunk = next((c for c in chunks if c.index == chunk_index), None)
                if chunk:
                    # Format chapter title for display
                    if chapter.prefix:
                        display_title = f"{chapter.prefix} {chapter.order}"
                    else:
                        # For standalone Roman numerals, use "Chapter" prefix
                        display_title = f"Chapter {chapter.order}"
                    
                    chunk.chapter_title = display_title
                    chunk.chapter_order = chapter.order
                    chapters_assigned += 1
                    logger.debug(
                        f"Assigned chapter '{display_title}' (order={chapter.order}) "
                        f"to chunk {chunk_index} at position {chapter.position}"
                    )
            else:
                logger.warning(
                    f"Could not find chunk for chapter '{chapter.title}' "
                    f"at position {chapter.position}"
                )
        
        db.commit()
        logger.info(
            f"Saved {chapters_assigned}/{len(chapters)} chapters to chunks "
            f"for project {project_id}"
        )
    
    def calculate_chapter_timestamps(
        self,
        project_id: int,
        db: Session
    ) -> List[ChapterTimestamp]:
        """
        Calculate start timestamps for each chapter.
        
        Reads audio durations of chunks and sums them up to find
        where each chapter starts in the final audio.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            List of chapters with timestamps
        """
        # Get all chunks ordered by index
        chunks = db.query(Chunk).filter(
            Chunk.project_id == project_id
        ).order_by(Chunk.index).all()
        
        if not chunks:
            logger.warning(f"No chunks found for project {project_id}")
            return []
        
        # Get chapters (chunks with chapter_title set)
        chapter_chunks = [
            (c.index, c.chapter_title, c.chapter_order)
            for c in chunks
            if c.chapter_title and c.chapter_order is not None
        ]
        
        if not chapter_chunks:
            logger.debug(f"No chapters found for project {project_id}")
            return []
        
        # Sort by order
        chapter_chunks.sort(key=lambda x: x[2])  # Sort by chapter_order
        
        # Calculate cumulative durations
        timestamps = []
        cumulative_duration_ms = 0
        last_chapter_chunk_index = 0
        
        for chunk_index, chapter_title, chapter_order in chapter_chunks:
            # Sum durations of all chunks from the last chapter to this chapter
            # (from last_chapter_chunk_index to chunk_index-1)
            for i in range(last_chapter_chunk_index, chunk_index):
                chunk = next((c for c in chunks if c.index == i), None)
                if chunk and chunk.chunk_audio_path:
                    try:
                        audio = AudioSegment.from_file(chunk.chunk_audio_path)
                        cumulative_duration_ms += len(audio)
                    except Exception as e:
                        logger.warning(
                            f"Could not read audio duration for chunk {i}: {e}"
                        )
            
            # Convert to seconds
            timestamp_seconds = cumulative_duration_ms / 1000.0
            
            # Format as HH:MM:SS
            hours = int(timestamp_seconds // 3600)
            minutes = int((timestamp_seconds % 3600) // 60)
            seconds = int(timestamp_seconds % 60)
            
            if hours > 0:
                timestamp_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                timestamp_formatted = f"{minutes}:{seconds:02d}"
            
            timestamps.append(ChapterTimestamp(
                title=chapter_title,
                order=chapter_order,
                timestamp_seconds=timestamp_seconds,
                timestamp_formatted=timestamp_formatted,
                chunk_index=chunk_index
            ))
            
            logger.debug(
                f"Chapter '{chapter_title}' starts at {timestamp_formatted} "
                f"(chunk {chunk_index})"
            )
            
            # Update last chapter chunk index for next iteration
            last_chapter_chunk_index = chunk_index
        
        logger.info(
            f"Calculated timestamps for {len(timestamps)} chapters "
            f"in project {project_id}"
        )
        
        return timestamps
    
    def get_chapters(
        self,
        project_id: int,
        db: Session
    ) -> List[Dict]:
        """
        Get chapter list for a project.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            List of chapter dictionaries with title, order, and optional timestamp
        """
        chunks = db.query(Chunk).filter(
            Chunk.project_id == project_id,
            Chunk.chapter_title.isnot(None),
            Chunk.chapter_order.isnot(None)
        ).order_by(Chunk.chapter_order, Chunk.index).all()
        
        chapters = []
        for chunk in chunks:
            chapters.append({
                "title": chunk.chapter_title,
                "order": chunk.chapter_order,
                "chunk_index": chunk.index
            })
        
        return chapters
