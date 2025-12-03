import os
from pathlib import Path

class Settings:
    # Base Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR = BASE_DIR / "storage"
    
    # Storage Subdirectories
    UPLOAD_DIR = STORAGE_DIR / "uploads"
    OUTPUT_DIR = STORAGE_DIR / "outputs"
    MODELS_DIR = STORAGE_DIR / "models"
    REFERENCE_VOICES_DIR = STORAGE_DIR / "reference_voices"
    
    # Database
    DB_NAME = "database.db"
    DB_URL = f"sqlite:///{BASE_DIR}/{DB_NAME}"
    
    # TTS Defaults (XTTS v2)
    DEFAULT_LANGUAGE = "en"
    DEFAULT_SPEED = 1.0
    DEFAULT_TEMPERATURE = 0.75
    DEFAULT_TOP_K = 50
    DEFAULT_TOP_P = 0.85
    DEFAULT_REPETITION_PENALTY = 2.0
    
    # Audio Processing
    CHUNK_SILENCE_DURATION = 350  # ms
    EXPORT_BITRATE = "192k"
    EXPORT_FORMAT = "mp3"

    def __init__(self):
        # Ensure directories exist
        self.STORAGE_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)
        # Reference voices dir might be managed manually or by git, so we just check existence when needed

settings = Settings()
