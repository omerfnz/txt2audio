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
    # FP16: KAPATILDI - Coqui TTS uyumsuzluk (Input FP32 vs Model FP16)
    # Hata: "Input type (FloatTensor) and weight type (HalfTensor) should be the same"
    FP16_MIN_VRAM_GB = 8.0  # Bu değerin üzerindeki GPU'larda FP16 aktif
    USE_FP16_AUTO = False    # ❌ KAPALI - Coqui TTS uyumsuz
    
    # torch.compile (PyTorch 2.0+)
    # KAPATILDI - XTTS v2 ile uyumluluk sorunları var
    USE_TORCH_COMPILE = False  # KAPATILDI - CUDA errors
    TORCH_COMPILE_MODE = "reduce-overhead"  # "reduce-overhead" veya "max-autotune"
    
    # Model Warm-up
    WARMUP_ON_LOAD = True  # ✅ AÇIK - CUDA kernel preload (güvenli)
    WARMUP_TEXT = "Hello, this is a warm-up test for the text to speech engine."
    
    # Speaker Embedding Cache
    # Single-chunk modunda GÜVENLİ - Aynı ses projelerinde %10-15 hızlanma
    USE_SPEAKER_CACHE = True  # ✅ AÇ - Concurrent=1'de güvenli
    SPEAKER_CACHE_MAX_SIZE = 10  # Maximum cache'lenecek speaker sayısı (LRU)
    
    # Concurrent Processing
    # KRİTİK: KAPALI KALMALI - XTTS v2 thread-safe değil, GPU çakışması oluyor
    # CUDA assertion hatası: srcIndex < srcSelectDimSize
    USE_CONCURRENT_PROCESSING = False  # ❌ KRİTİK: KAPALI TUTUN
    MAX_CONCURRENT_CHUNKS = 1  # ❌ KRİTİK: 1'de TUTUN (concurrent çalışmıyor)
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
