"""
Timelapse Exporter Module

Exports chapter timestamps in YouTube description format.
"""

from typing import List
from .chapter_service import ChapterTimestamp


class TimelapseExporter:
    """
    Exports chapter timestamps in various formats.
    """
    
    def export_youtube_format(
        self,
        chapters: List[ChapterTimestamp]
    ) -> str:
        """
        Export chapters in YouTube description format.
        
        Format:
        0:00 Chapter One
        15:32 Chapter Two
        28:45 Chapter Three
        
        Args:
            chapters: List of chapters with timestamps
            
        Returns:
            Formatted string ready for YouTube description
        """
        if not chapters:
            return ""
        
        lines = []
        for chapter in chapters:
            # YouTube format: timestamp followed by chapter title
            # Format: M:SS or H:MM:SS
            lines.append(f"{chapter.timestamp_formatted} {chapter.title}")
        
        return "\n".join(lines)
    
    def export_simple_format(
        self,
        chapters: List[ChapterTimestamp]
    ) -> str:
        """
        Export chapters in simple text format.
        
        Format:
        Chapter One - 0:00
        Chapter Two - 15:32
        Chapter Three - 28:45
        
        Args:
            chapters: List of chapters with timestamps
            
        Returns:
            Formatted string
        """
        if not chapters:
            return ""
        
        lines = []
        for chapter in chapters:
            lines.append(f"{chapter.title} - {chapter.timestamp_formatted}")
        
        return "\n".join(lines)
