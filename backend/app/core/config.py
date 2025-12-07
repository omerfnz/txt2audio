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
    DEFAULT_SPEED = 0.9
    DEFAULT_TEMPERATURE = 0.75
    DEFAULT_TOP_K = 50
    DEFAULT_TOP_P = 0.85
    DEFAULT_REPETITION_PENALTY = 2.0
    
    # Audio Processing
    CHUNK_SILENCE_DURATION = 350  # ms
    EXPORT_BITRATE = "192k"
    EXPORT_FORMAT = "mp3"
    
    # GPU Optimization Settings
    # FP16: Coqui TTS ile uyumluluk sorunu var - şimdilik kapalı
    # NOT: XTTS v2 internal olarak FP32 input bekliyor, model.half() uyumsuz
    FP16_MIN_VRAM_GB = 8.0  # Bu değerin üzerindeki GPU'larda FP16 aktif
    USE_FP16_AUTO = False    # KAPATILDI - Coqui TTS uyumsuzluğu
    
    # torch.compile (PyTorch 2.0+)
    # Sadece Linux + GPU ortamında aktif (Windows'ta uyumluluk sorunları var)
    USE_TORCH_COMPILE = True  # GPU + Linux'ta otomatik aktif
    TORCH_COMPILE_MODE = "reduce-overhead"  # "reduce-overhead" veya "max-autotune"
    
    # Model Warm-up
    WARMUP_ON_LOAD = True  # Model yüklendikten sonra warm-up yap
    WARMUP_TEXT = "Hello, this is a warm-up test for the text to speech engine."
    
    # Speaker Embedding Cache
    # Aynı referans ses dosyası için embedding'i tekrar hesaplamamak için cache
    USE_SPEAKER_CACHE = True  # Speaker embedding cache aktif
    SPEAKER_CACHE_MAX_SIZE = 10  # Maximum cache'lenecek speaker sayısı (LRU)
    
    # Concurrent Processing
    # Birden fazla chunk'ı aynı anda işleme (GPU memory'e dikkat!)
    USE_CONCURRENT_PROCESSING = True  # Concurrent processing aktif
    MAX_CONCURRENT_CHUNKS = 2  # T4 GPU (16GB) için güvenli değer
    CONCURRENT_MIN_VRAM_GB = 12.0  # Bu değerin altında concurrent=1'e düş
    
    # GPU Monitoring
    GPU_MONITOR_ENABLED = True  # GPU izleme aktif
    GPU_TEMP_WARNING_C = 80  # Bu sıcaklığın üzerinde uyarı
    GPU_TEMP_CRITICAL_C = 90  # Bu sıcaklığın üzerinde işlemi yavaşlat
    GPU_VRAM_WARNING_PERCENT = 85  # VRAM %85'in üzerinde uyarı

    def __init__(self):
        # Ensure directories exist
        self.STORAGE_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)
        # Reference voices dir might be managed manually or by git, so we just check existence when needed

settings = Settings()
