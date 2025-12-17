import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    
    # Storage Subdirectories
    # Not: Pydantic ile dinamik path oluşturmak için validator kullanılabilir 
    # veya property olarak tanımlanabilir, ancak basitlik için post-init yapıyoruz.
    
    # Database
    DB_NAME: str = "database.db"

    # CORS
    # Not: Wildcard (*) ile allow_credentials=True kullanılamaz
    # CloudSpaces origin'leri için regex kullanılacak
    ALLOW_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://0.0.0.0:5173",
    ]  # Env ile override edilebilir (JSON veya virgülle ayrılmış liste)
    
    # CloudSpaces origin regex pattern (allow_origin_regex ile kullanılacak)
    # Hem frontend (5173-, 4173-) hem backend (8000-) subdomain'lerini kapsar
    CLOUDSPACES_ORIGIN_REGEX: str = r"https://\d+-.*\.cloudspaces\.litng\.ai"
    
    # TTS Defaults (XTTS v2)
    DEFAULT_LANGUAGE: str = "en"
    # Increased speed for better performance (0.9 -> 0.95)
    # 0.95 is still natural but slightly faster
    DEFAULT_SPEED: float = 0.95
    DEFAULT_TEMPERATURE: float = 0.75
    DEFAULT_TOP_K: int = 50
    DEFAULT_TOP_P: float = 0.85
    # Increased from 2.0 to 2.5 to prevent truncation and repetition issues
    DEFAULT_REPETITION_PENALTY: float = 2.5
    
    # Audio Processing
    CHUNK_SILENCE_DURATION: int = 250  # ms (optimized: reduced from 350ms to lower silence percentage)
    EXPORT_BITRATE: str = "192k"
    EXPORT_FORMAT: str = "mp3"

    # Background music defaults
    DEFAULT_BG_MUSIC_ENABLED: bool = False
    DEFAULT_BG_MUSIC_FILE: str = ""  # None/empty means no music
    DEFAULT_BG_MUSIC_VOLUME: float = 0.10  # 0-1 arası, UI 0-100'e maplenecek
    
    # Model Warm-up (AÇIK - güvenli)
    WARMUP_ON_LOAD: bool = True
    WARMUP_TEXT: str = "Hello, this is a warm-up test for the text to speech engine."
    
    # Speaker Embedding Cache (AÇIK - single-chunk modunda güvenli)
    USE_SPEAKER_CACHE: bool = True
    SPEAKER_CACHE_MAX_SIZE: int = 10  # Maximum cache'lenecek speaker sayısı (LRU)
    
    # GPU Monitoring
    GPU_MONITOR_ENABLED: bool = True
    GPU_TEMP_WARNING_C: int = 80
    GPU_TEMP_CRITICAL_C: int = 90
    GPU_VRAM_WARNING_PERCENT: int = 85

    # Debug Mode
    DEBUG_MODE: bool = True

    # RangeHTTPServer Configuration (for large file streaming)
    RANGE_SERVER_ENABLED: bool = True
    RANGE_SERVER_PORT: int = 8080
    RANGE_SERVER_DIR: Optional[Path] = None  # None = OUTPUT_DIR

    # F5-TTS Configuration
    F5_MODEL_CKPT: str = "" # Optional custom checkpoint path
    F5_VOCAB_FILE: str = "" # Optional vocab file

    # Extra configs from .env
    DATABASE_URL: str = "" # Will be ignored/overwritten by DB_URL property logic usually, but needed to avoid validation error
    USE_GPU: bool = True
    TTS_MODEL: str = "xtts"
    LOG_LEVEL: str = "INFO"

    @property
    def UPLOAD_DIR(self) -> Path:
        return self.STORAGE_DIR / "uploads"
    
    @property
    def OUTPUT_DIR(self) -> Path:
        return self.STORAGE_DIR / "outputs"
    
    @property
    def MODELS_DIR(self) -> Path:
        return self.STORAGE_DIR / "models"

    @property
    def MUSIC_DIR(self) -> Path:
        return self.STORAGE_DIR / "music"
    
    @property
    def REFERENCE_VOICES_DIR(self) -> Path:
        return self.STORAGE_DIR / "reference_voices"
    
    @property
    def RANGE_SERVER_ROOT_DIR(self) -> Path:
        """Directory to serve via RangeHTTPServer (defaults to OUTPUT_DIR)"""
        return self.RANGE_SERVER_DIR if self.RANGE_SERVER_DIR else self.OUTPUT_DIR
        
    @property
    def DB_URL(self) -> str:
        return f"sqlite:///{self.BASE_DIR}/{self.DB_NAME}"

    def model_post_init(self, __context):
        # Ensure directories exist
        self.STORAGE_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)
        self.MUSIC_DIR.mkdir(exist_ok=True)
        # Reference voices dir might be managed manually or by git

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignore extra fields in .env file

settings = Settings()
# Trigger directory creation
settings.model_post_init(None)
