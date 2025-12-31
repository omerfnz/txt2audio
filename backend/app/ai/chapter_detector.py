"""
Chapter Detection Module

Detects chapter/section headers in text files.
Supports Roman numerals, numbered chapters, and various prefixes.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChapterInfo:
    """Information about a detected chapter."""
    title: str  # Original title text (e.g., "I", "Chapter One", "Part 2")
    chapter_type: str  # "roman" or "numbered"
    order: int  # Sequential order (1, 2, 3...)
    position: int  # Character position in original text
    prefix: Optional[str] = None  # "Chapter", "Part", "Section", etc.


class ChapterDetector:
    """
    Detects chapter/section headers in text.
    
    Supports:
    - Standalone Roman numerals: I, II, III, IV... (with or without period)
    - Prefixed Roman numerals: Chapter I, Part II, Section III...
    - Prefixed numbers: Chapter 1, Part 2, Section 3...
    """
    
    def __init__(self):
        # Roman numeral pattern (validates I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
        self.roman_pattern = r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'
        
        # Chapter prefixes (case-insensitive)
        self.prefixes = ['Chapter', 'Part', 'Section', 'Book', 'Act', 'Scene']
    
    def roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer."""
        roman = roman.upper().strip()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        res = 0
        for i in range(len(roman)):
            if i > 0 and values[roman[i]] > values[roman[i - 1]]:
                res += values[roman[i]] - 2 * values[roman[i - 1]]
            else:
                res += values[roman[i]]
        return res
    
    def is_valid_roman(self, text: str) -> bool:
        """Check if text is a valid Roman numeral."""
        cleaned = text.strip().rstrip('.')
        return bool(re.match(self.roman_pattern, cleaned, re.IGNORECASE))
    
    def detect_chapters(self, text: str) -> List[ChapterInfo]:
        """
        Detect chapter headers in text.
        
        Args:
            text: Full text content
            
        Returns:
            List of detected chapters with their positions and metadata
        """
        chapters = []
        lines = text.split('\n')
        current_position = 0
        chapter_order = 1
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                current_position += len(line) + 1  # +1 for newline
                continue
            
            # Check for standalone Roman numeral (at start of line or after blank line)
            # Pattern: ^I\.?$ or ^II\.?$ etc. (with optional period)
            standalone_roman_match = re.match(r'^([IVXLCDM]+)\.?$', line_stripped, re.IGNORECASE)
            if standalone_roman_match:
                roman_str = standalone_roman_match.group(1)
                if self.is_valid_roman(roman_str):
                    # Check if previous line was blank (likely a chapter header)
                    is_after_blank = (line_num > 0 and lines[line_num - 1].strip() == '')
                    # Or check if it's at the very beginning
                    if is_after_blank or line_num == 0:
                        order = self.roman_to_int(roman_str)
                        chapters.append(ChapterInfo(
                            title=line_stripped,
                            chapter_type="roman",
                            order=order,
                            position=current_position,
                            prefix=None
                        ))
                        chapter_order = max(chapter_order, order) + 1
            
            # Check for prefixed Roman numerals: "Chapter I", "Part II", etc.
            for prefix in self.prefixes:
                # Pattern: "Chapter I" or "Part II" (case-insensitive)
                prefixed_roman_match = re.match(
                    rf'^({re.escape(prefix)})\s+([IVXLCDM]+)\.?$',
                    line_stripped,
                    re.IGNORECASE
                )
                if prefixed_roman_match:
                    found_prefix = prefixed_roman_match.group(1)
                    roman_str = prefixed_roman_match.group(2)
                    if self.is_valid_roman(roman_str):
                        order = self.roman_to_int(roman_str)
                        chapters.append(ChapterInfo(
                            title=line_stripped,
                            chapter_type="roman",
                            order=order,
                            position=current_position,
                            prefix=found_prefix
                        ))
                        chapter_order = max(chapter_order, order) + 1
                        break
            
            # Check for prefixed numbers: "Chapter 1", "Part 2", etc.
            for prefix in self.prefixes:
                # Pattern: "Chapter 1" or "Part 2" (case-insensitive)
                prefixed_number_match = re.match(
                    rf'^({re.escape(prefix)})\s+(\d+)\.?$',
                    line_stripped,
                    re.IGNORECASE
                )
                if prefixed_number_match:
                    found_prefix = prefixed_number_match.group(1)
                    number_str = prefixed_number_match.group(2)
                    order = int(number_str)
                    chapters.append(ChapterInfo(
                        title=line_stripped,
                        chapter_type="numbered",
                        order=order,
                        position=current_position,
                        prefix=found_prefix
                    ))
                    chapter_order = max(chapter_order, order) + 1
                    break
            
            # Check for prefixed word numbers: "Chapter Two", "Part Three", etc.
            # This handles normalized Roman numerals (e.g., "II." -> "Chapter Two")
            # Also check within the line (not just at start) for cases like "text Chapter One more text"
            for prefix in self.prefixes:
                # Pattern: "Chapter Two", "Part Three", etc. (case-insensitive)
                # Match words like "One", "Two", "Three", "Four", etc.
                # First try at line start
                prefixed_word_match = re.match(
                    rf'^({re.escape(prefix)})\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|Hundred|Thousand)(?:\s|$|\.)',
                    line_stripped,
                    re.IGNORECASE
                )
                # If not at start, search within the line
                if not prefixed_word_match:
                    prefixed_word_match = re.search(
                        rf'\b({re.escape(prefix)})\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|Hundred|Thousand)(?:\s|$|\.)',
                        line_stripped,
                        re.IGNORECASE
                    )
                
                if prefixed_word_match:
                    found_prefix = prefixed_word_match.group(1)
                    word_number = prefixed_word_match.group(2).lower()
                    # Convert word to number
                    word_to_num = {
                        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
                        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
                        'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000
                    }
                    order = word_to_num.get(word_number, 0)
                    if order > 0:
                        # Calculate position: if match is at start, use current_position
                        # Otherwise, find the position of the match within the line
                        if hasattr(prefixed_word_match, 'start') and prefixed_word_match.start() == 0:
                            chapter_pos = current_position
                        elif hasattr(prefixed_word_match, 'start'):
                            chapter_pos = current_position + prefixed_word_match.start()
                        else:
                            chapter_pos = current_position
                        
                        # Extract the chapter title (the matched part)
                        chapter_title = prefixed_word_match.group(0).strip()
                        
                        chapters.append(ChapterInfo(
                            title=chapter_title,
                            chapter_type="numbered",
                            order=order,
                            position=chapter_pos,
                            prefix=found_prefix
                        ))
                        chapter_order = max(chapter_order, order) + 1
                    break
            
            current_position += len(line) + 1  # +1 for newline
        
        # Sort by position to maintain text order
        chapters.sort(key=lambda x: x.position)
        
        # Re-number chapters sequentially if needed (in case of gaps)
        # This ensures chapter_order is always 1, 2, 3, 4...
        if chapters:
            sorted_by_order = sorted(chapters, key=lambda x: x.order)
            order_map = {}
            for idx, chapter in enumerate(sorted_by_order, start=1):
                order_map[(chapter.position, chapter.order)] = idx
            
            # Update order for all chapters
            for chapter in chapters:
                new_order = order_map.get((chapter.position, chapter.order), chapter.order)
                chapter.order = new_order
        
        return chapters
