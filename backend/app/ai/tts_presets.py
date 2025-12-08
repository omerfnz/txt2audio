"""
TTS Preset Management Module

This module provides predefined TTS parameter configurations
optimized for different languages and content types to achieve
professional audiobook narration quality.

Based on Coqui XTTS v2 research and ACX audiobook standards.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TTSPreset:
    """
    TTS parameter preset configuration.
    
    Attributes:
        name: Human-readable preset name
        description: Detailed description of use case
        language: Target language code (en, tr, etc.)
        content_type: Content category (fiction, nonfiction)
        temperature: Controls emotional variance (0.0-1.0)
        top_p: Nucleus sampling threshold (0.0-1.0)
        repetition_penalty: Prevents word repetition (1.0-3.0)
        speed: Playback speed multiplier (0.5-2.0)
        enable_text_splitting: Auto-split long sentences
    """
    name: str
    description: str
    language: str
    content_type: str
    temperature: float
    top_p: float
    repetition_penalty: float
    speed: float
    enable_text_splitting: bool


# Predefined presets optimized for XTTS v2
PRESETS: Dict[str, TTSPreset] = {
    "en_fiction": TTSPreset(
        name="English Fiction",
        description=(
            "Optimized for English novels and story narration. "
            "Balanced temperature for rich emotional expression "
            "while maintaining stability. Higher repetition penalty "
            "prevents truncation in dramatic passages."
        ),
        language="en",
        content_type="fiction",
        temperature=0.75,  # Reduced from 0.80 for better stability
        top_p=0.85,
        repetition_penalty=2.3,  # Increased from 2.0 for stability
        speed=0.95,
        enable_text_splitting=True
    ),
    
    "en_nonfiction": TTSPreset(
        name="English Non-Fiction",
        description=(
            "Optimized for English educational and informational content. "
            "Lower temperature for clear, consistent articulation "
            "and professional tone. Enhanced stability with higher repetition "
            "penalty to prevent truncation issues."
        ),
        language="en",
        content_type="nonfiction",
        temperature=0.32,  # Slightly lower for maximum stability
        top_p=0.88,  # Reduced for more consistent output
        repetition_penalty=2.5,  # Increased from 2.0 to prevent loops/truncation
        speed=0.95,
        enable_text_splitting=True
    ),
    
    "tr_fiction": TTSPreset(
        name="Turkish Fiction",
        description=(
            "Optimized for Turkish novels and story narration. "
            "Balanced temperature for natural Turkish prosody "
            "while maintaining emotional depth."
        ),
        language="tr",
        content_type="fiction",
        temperature=0.85,
        top_p=0.80,
        repetition_penalty=1.8,
        speed=0.9,
        enable_text_splitting=True
    ),
    
    "tr_nonfiction": TTSPreset(
        name="Turkish Non-Fiction",
        description=(
            "Optimized for Turkish educational and informational content. "
            "Moderate temperature for clear pronunciation "
            "of technical terms and proper nouns."
        ),
        language="tr",
        content_type="nonfiction",
        temperature=0.40,
        top_p=0.88,
        repetition_penalty=1.8,
        speed=0.9,
        enable_text_splitting=True
    ),
    
    "custom": TTSPreset(
        name="Custom",
        description=(
            "User-defined custom parameters. "
            "Use this preset for manual fine-tuning."
        ),
        language="en",
        content_type="custom",
        temperature=0.75,
        top_p=0.85,
        repetition_penalty=2.0,
        speed=0.9,
        enable_text_splitting=True
    )
}


def get_preset(preset_id: str) -> Optional[TTSPreset]:
    """
    Retrieve a preset by its identifier.
    
    Args:
        preset_id: Preset identifier key
        
    Returns:
        TTSPreset object if found, None otherwise
    """
    return PRESETS.get(preset_id)


def get_all_presets() -> Dict[str, TTSPreset]:
    """
    Get all available presets.
    
    Returns:
        Dictionary of all preset configurations
    """
    return PRESETS.copy()


def get_presets_by_language(language: str) -> Dict[str, TTSPreset]:
    """
    Filter presets by language.
    
    Args:
        language: Language code (e.g., 'en', 'tr')
        
    Returns:
        Dictionary of presets matching the language
    """
    return {
        key: preset
        for key, preset in PRESETS.items()
        if preset.language == language
    }


def validate_preset_params(
    temperature: float,
    top_p: float,
    repetition_penalty: float,
    speed: float
) -> tuple[bool, Optional[str]]:
    """
    Validate TTS parameters are within acceptable ranges.
    
    Args:
        temperature: Temperature value to validate
        top_p: Top-p value to validate
        repetition_penalty: Repetition penalty to validate
        speed: Speed value to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not 0.0 <= temperature <= 1.0:
        return False, "Temperature must be between 0.0 and 1.0"
    
    if not 0.0 <= top_p <= 1.0:
        return False, "Top-p must be between 0.0 and 1.0"
    
    if not 1.0 <= repetition_penalty <= 3.0:
        return False, "Repetition penalty must be between 1.0 and 3.0"
    
    if not 0.5 <= speed <= 2.0:
        return False, "Speed must be between 0.5 and 2.0"
    
    return True, None
