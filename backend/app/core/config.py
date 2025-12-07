import os
from pathlib import Path
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
    
    # TTS Defaults (XTTS v2)
    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_SPEED: float = 0.9
    DEFAULT_TEMPERATURE: float = 0.75
    DEFAULT_TOP_K: int = 50
    DEFAULT_TOP_P: float = 0.85
    DEFAULT_REPETITION_PENALTY: float = 2.0
    
    # Audio Processing
    CHUNK_SILENCE_DURATION: int = 350  # ms
    EXPORT_BITRATE: str = "192k"
    EXPORT_FORMAT: str = "mp3"
    
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

    # System Optimization
    TTS_USE_DEEPSPEED: bool = False  # DeepSpeed devre dışı bırakıldı (XTTS uyumsuzluğu)

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
    def REFERENCE_VOICES_DIR(self) -> Path:
        return self.STORAGE_DIR / "reference_voices"
        
    @property
    def DB_URL(self) -> str:
        return f"sqlite:///{self.BASE_DIR}/{self.DB_NAME}"

    def model_post_init(self, __context):
        # Ensure directories exist
        self.STORAGE_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)
        # Reference voices dir might be managed manually or by git

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
# Trigger directory creation
settings.model_post_init(None)
