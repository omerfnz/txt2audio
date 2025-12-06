"""
Utilities for cleaning Project Gutenberg text files.
"""
import re
from typing import Tuple, Optional, List

class GutenbergCleaner:
    """Cleans text files downloaded from Project Gutenberg."""
    
    # Markers that indicate the start of the book content
    START_MARKERS = [
        r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*",
        r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK",
        r"\*\*\* START OF THIS PROJECT GUTENBERG EBOOK",
    ]
    
    # Markers that indicate the end of the book content
    END_MARKERS = [
        r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*",
        r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK",
        r"\*\*\* END OF THIS PROJECT GUTENBERG EBOOK",
    ]

    def __init__(self):
        self.start_patterns = [re.compile(p, re.IGNORECASE) for p in self.START_MARKERS]
        self.end_patterns = [re.compile(p, re.IGNORECASE) for p in self.END_MARKERS]

    def extract_metadata(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts Title and Author from the header section of the Gutenbeg text.
        """
        title = None
        author = None
        
        # Look for Title: and Author: lines in the first 200 lines (header usually)
        lines = text.split('\n')[:200]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for Title
            if not title and (line.startswith("Title:") or line.startswith("TITLE:")):
                title = line.split(":", 1)[1].strip()
            
            # Check for Author
            if not author and (line.startswith("Author:") or line.startswith("AUTHOR:")):
                author = line.split(":", 1)[1].strip()
                
            if title and author:
                break
                
        return title, author

    def clean_text(self, text: str, title: Optional[str] = None) -> str:
        """
        Removes Gutenberg headers and footers, returning only the book content.
        Uses title detection and keyword heuristics to remove introductory meta-text.
        """
        lines = text.split('\n')
        start_index = 0
        end_index = len(lines)
        
        # Find start marker
        for i, line in enumerate(lines):
            line_check = line.strip()
            if any(p.search(line_check) for p in self.start_patterns):
                start_index = i + 1
                break
        
        # Find end marker
        for i in range(len(lines) - 1, start_index, -1):
            line_check = lines[i].strip()
            if any(p.search(line_check) for p in self.end_patterns):
                end_index = i
                break
                
        # Extract content lines
        content_lines = lines[start_index:end_index]
        
        # Remove empty lines from the beginning
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)

        # Strategy 1: Title-based skip
        # If we know the title, look for it in the first 50 lines. 
        # Gutenberg texts often repeat the title right before the actual story begins.
        if title:
            # Clean title for comparison (remove special chars, lower case)
            clean_title = re.sub(r'[^\w\s]', '', title).lower().strip()
            
            # Look for the title line
            found_title_idx = -1
            for i in range(min(50, len(content_lines))):
                line = content_lines[i].strip()
                if not line:
                    continue
                    
                # Check for exact match or "Title by Author" pattern
                clean_line = re.sub(r'[^\w\s]', '', line).lower().strip()
                
                # If line starts with title (ignoring case/punctuation)
                if clean_line.startswith(clean_title) and len(clean_line) >= len(clean_title):
                    found_title_idx = i
                    break
            
            # If found, discard everything before it (keep the title line as it often starts the text)
            if found_title_idx != -1:
                content_lines = content_lines[found_title_idx:]
                return self._finalize_text(content_lines)

        # Strategy 2: Paragraph/Keyword cleaning (Fallback)
        # We process text as blocks/paragraphs to remove multi-line meta text
        cleaned_groups = []
        current_group = []
        
        for line in content_lines:
            if not line.strip():
                if current_group:
                    cleaned_groups.append(current_group)
                    current_group = []
            else:
                current_group.append(line)
        if current_group:
            cleaned_groups.append(current_group)

        # Filter initial groups that look like meta-text
        final_groups = []
        is_content_started = False
        
        meta_keywords = [
            "Project Gutenberg", "Etext", "transcription", "official release", 
            "re-released", "rerelease", "officially", "dated", "copyright", 
            "distribute", "proofreading"
        ]
        
        for group in cleaned_groups:
            if is_content_started:
                final_groups.append(group)
                continue
                
            # Convert group to single string for checking
            group_text = " ".join([l.strip() for l in group])
            
            # Check for meta keywords
            if any(k.lower() in group_text.lower() for k in meta_keywords):
                continue # Skip this group
                
            # If we reached here, this group is likely content
            is_content_started = True
            final_groups.append(group)
            
        # Reconstruct lines
        result_lines = []
        for group in final_groups:
            result_lines.extend(group)
            result_lines.append("") # Restore paragraph break
            
        return self._finalize_text(result_lines)

    def _finalize_text(self, lines: List[str]) -> str:
        """Helper to join lines and fix common formatting issues."""
        text = '\n'.join(lines)
        # Fix spaced ellipsis (. . .) -> (...)
        text = text.replace(". . .", "...")
        return text.strip()

    def prepare_chunks(self, text: str) -> List[str]:
        """
        Prepares specific chunks for the Project Gutenberg textbook:
        1. Intro chunk: "From the library of The Archive Key."
        2. Title chunk: "{Title} by {Author}"
        3. Content chunk: The rest of the book content.
        """
        chunks = []
        
        # 1. Intro Chunk
        chunks.append("From the library of The Archive Key.")
        
        # 2. Extract Title and Author for the second chunk
        title, author = self.extract_metadata(text)
        
        if title and author:
            chunks.append(f"{title} by {author}")
        elif title:
            chunks.append(title)
        
        # 3. Clean Content
        cleaned_content = self.clean_text(text, title=title)
        
        return chunks, cleaned_content
