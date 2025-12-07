import os
import sys
import torch
import gc
import platform
from typing import Optional, Dict, Any, Tuple
from collections import OrderedDict
import shutil

# Config import
from ..core.config import settings


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.
    
    Used for caching speaker embeddings to avoid recomputing
    them for the same reference audio file.
    """
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache, moving it to end (most recently used)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Add item to cache, removing oldest if at capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                # Remove oldest item (first in OrderedDict)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[key] = value
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }


class TTSEngine:
    """
    XTTS v2 Text-to-Speech Engine with GPU optimizations.
    
    Features:
    - Automatic FP16 (Half Precision) based on GPU VRAM
    - DeepSpeed support on Linux
    - Memory management and cleanup
    """
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.tts: Optional[object] = None
        
        # Speaker embedding cache
        self.use_speaker_cache = settings.USE_SPEAKER_CACHE
        self._speaker_cache: Optional[LRUCache] = None
        if self.use_speaker_cache:
            self._speaker_cache = LRUCache(max_size=settings.SPEAKER_CACHE_MAX_SIZE)
            print(f"✓ Speaker Embedding Cache aktif (max {settings.SPEAKER_CACHE_MAX_SIZE} speaker)")

        # Quality thresholds for individual chunks
        self.min_chunk_duration_ms = 700
        self.min_chunk_rms_db = -50.0
        
        # Model indirme dizini
        self.model_path = os.path.join(os.getcwd(), "storage", "models")
        os.environ["TTS_HOME"] = self.model_path
        os.environ["COQUI_TOS_AGREED"] = "1"
        # Disable DeepSpeed to prevent kernel crashes with XTTS v2
        os.environ["TTS_USE_DEEPSPEED"] = "False"
        
        # espeak-ng pathini bul ve ayarla
        self._setup_espeak()

        # GPU bilgisi
        if self.use_gpu:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✓ GPU Modu: {gpu_name}")
            print(f"  VRAM: {vram_gb:.2f} GB")
            
            if vram_gb < 4:
                print("  ⚠ VRAM düşük! Büyük metinlerde sorun yaşanabilir.")
        else:
            print("✓ CPU Modu")

    def _setup_espeak(self):
        """espeak-ng PATH'ini kontrol et ve ayarla"""
        if sys.platform.startswith("win"):
            # Önce komut satırında var mı kontrol et
            espeak_path = shutil.which("espeak-ng")
            if espeak_path:
                print(f"✓ espeak-ng found: {espeak_path}")
                return
            
            # Windows yollarında ara
            possible_paths = [
                r"C:\Program Files\eSpeak NG",
                r"C:\Program Files (x86)\eSpeak NG",
                os.path.expandvars(r"%PROGRAMFILES%\eSpeak NG"),
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\eSpeak NG"),
            ]
            
            for base_path in possible_paths:
                if os.path.exists(base_path):
                    # bin subdirectory'yi de kontrol et
                    bin_path = os.path.join(base_path, "bin")
                    if os.path.exists(bin_path):
                        os.environ["PATH"] = f"{bin_path};{os.environ.get('PATH', '')}"
                        print(f"✓ espeak-ng found at: {bin_path}")
                        return
                    else:
                        os.environ["PATH"] = f"{base_path};{os.environ.get('PATH', '')}"
                        print(f"✓ espeak-ng found at: {base_path}")
                        return
            
            print("⚠ espeak-ng not in PATH or standard locations")
            print("  If installed, it will still be found by the system")

    def load_model(self):
        """Load XTTS v2 model."""
        if self.tts is None:
            try:
                from TTS.api import TTS
                print(f"📦 Loading XTTS v2 model on {self.device.upper()}...")
                
                # Model yükle
                self.tts = TTS(
                    self.model_name,
                    progress_bar=True
                )
                
                # GPU'ya taşı (eğer istenmişse)
                if self.use_gpu:
                    print(f"🔄 Moving model to {self.device.upper()}...")
                    self.tts = self.tts.to(self.device)
                
                # Force Eval Mode (Performance Optimization)
                if hasattr(self.tts, 'tts_model'):
                    self.tts.tts_model.eval()
                
                print("✓ Model loaded successfully.")
                
                # VRAM temizliği
                if self.use_gpu:
                    torch.cuda.empty_cache()
                    self._log_gpu_memory("After model load")
                
                # Model Warm-up (CUDA kernel'larını önceden yükle)
                if settings.WARMUP_ON_LOAD:
                    self._warmup_model()
                    
            except TypeError as e:
                if "unsupported operand type(s) for |" in str(e):
                    error_msg = (
                        "❌ Python 3.10+ gerekiyor! "
                        f"Mevcut: Python {sys.version.split()[0]}. "
                        "Lütfen Python 3.10+ kullanın."
                    )
                    print(error_msg)
                    raise RuntimeError(error_msg) from e
                raise
            except Exception as e:
                print(f"❌ Model yükleme hatası: {type(e).__name__}")
                print(f"   Detay: {str(e)}")
                raise
    
    def _log_gpu_memory(self, context: str = ""):
        """Log current GPU memory usage."""
        if self.use_gpu:
            allocated = torch.cuda.memory_allocated(0) / 1e9
            reserved = torch.cuda.memory_reserved(0) / 1e9
            print(f"  📊 GPU Memory {context}: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
    
    def _warmup_model(self):
        """
        Perform model warm-up to preload CUDA kernels.
        
        This reduces latency on the first actual inference by
        running a dummy inference during model loading.
        """
        import tempfile
        import time
        
        print("🔄 Model warm-up başlatılıyor...")
        start_time = time.time()
        
        # Varsayılan referans ses dosyası bul
        ref_voice_dir = os.path.join(os.getcwd(), "storage", "reference_voices")
        ref_wav = None
        
        # adult/male klasöründen bir ses dosyası bul
        male_dir = os.path.join(ref_voice_dir, "adult", "male")
        if os.path.exists(male_dir):
            wav_files = [f for f in os.listdir(male_dir) if f.endswith('.wav')]
            if wav_files:
                ref_wav = os.path.join(male_dir, wav_files[0])
        
        # Bulunamadıysa adult/female dene
        if not ref_wav:
            female_dir = os.path.join(ref_voice_dir, "adult", "female")
            if os.path.exists(female_dir):
                wav_files = [f for f in os.listdir(female_dir) if f.endswith('.wav')]
                if wav_files:
                    ref_wav = os.path.join(female_dir, wav_files[0])
        
        if not ref_wav:
            print("  ⚠ Warm-up için referans ses bulunamadı, atlanıyor")
            return
        
        # Geçici dosya ile warm-up inference
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as tmp:
                # FP32 Mode (Safest for XTTS v2 on T4)
                self.tts.tts_to_file(
                    text=settings.WARMUP_TEXT,
                    speaker_wav=ref_wav,
                    language="en",
                    file_path=tmp.name
                )
            
            elapsed = time.time() - start_time
            print(f"  ✓ Model warm-up tamamlandı ({elapsed:.2f}s)")
            
            # Warm-up sonrası bellek temizliği
            if self.use_gpu:
                torch.cuda.empty_cache()
                
        except Exception as e:
            print(f"  ⚠ Warm-up hatası (kritik değil): {e}")
    
    def _get_speaker_embedding(self, speaker_wav: str) -> Optional[Tuple[Any, Any]]:
        """
        Get speaker embedding from cache or compute it.
        
        Args:
            speaker_wav: Path to reference audio file
            
        Returns:
            Tuple of (gpt_cond_latent, speaker_embedding) or None if failed
        """
        if not self.use_speaker_cache or self._speaker_cache is None:
            return None
        
        # Cache key: absolute path of the reference audio
        cache_key = os.path.abspath(speaker_wav)
        
        # Check cache first
        cached = self._speaker_cache.get(cache_key)
        if cached is not None:
            print(f"  📦 Speaker embedding cache HIT")
            return cached
        
        # Compute embedding
        try:
            if hasattr(self.tts, 'synthesizer') and hasattr(self.tts.synthesizer, 'tts_model'):
                tts_model = self.tts.synthesizer.tts_model
                if hasattr(tts_model, 'get_conditioning_latents'):
                    print(f"  🔄 Computing speaker embedding...")
                    
                    # FP32 Mode
                    gpt_cond_latent, speaker_embedding = tts_model.get_conditioning_latents(
                        audio_path=speaker_wav
                    )
                    
                    # Cache the result
                    self._speaker_cache.put(cache_key, (gpt_cond_latent, speaker_embedding))
                    print(f"  ✓ Speaker embedding cached")
                    
                    return (gpt_cond_latent, speaker_embedding)
        except Exception as e:
            print(f"  ⚠ Speaker embedding hesaplanamadı: {e}")
        
        return None
    
    def get_speaker_cache_stats(self) -> Dict[str, Any]:
        """Get speaker cache statistics."""
        if self._speaker_cache:
            return self._speaker_cache.stats()
        return {"enabled": False}
    
    def clear_speaker_cache(self) -> None:
        """Clear the speaker embedding cache."""
        if self._speaker_cache:
            self._speaker_cache.clear()
            print("🧹 Speaker cache cleared")

    def generate_audio(
        self,
        text: str,
        speaker_wav: str,
        output_path: str,
        language: str = "en",
        temperature: float = 0.75,
        top_p: float = 0.85,
        repetition_penalty: float = 2.0,
        speed: float = 1.0,
        **kwargs
    ) -> bool:
        """
        Generate audio file from text using XTTS v2.
        
        Args:
            text: Text to convert to speech
            speaker_wav: Path to reference voice file
            output_path: Output audio file path
            language: Language code (en, tr, etc.)
            temperature: Emotional variance (0.0-1.0). Higher = more expressive
            top_p: Nucleus sampling (0.0-1.0). Higher = more diverse
            repetition_penalty: Prevents word loops (1.0-3.0). Higher = less repetition
            speed: Playback speed multiplier (0.5-2.0)
            **kwargs: Additional TTS parameters
            
        Returns:
            True if successful, False otherwise
        """
        if self.tts is None:
            self.load_model()
        
        try:
            print(f"🎵 Generating audio (Device: {self.device.upper()})")
            print(f"   Text: {text[:50]}...")
            print(f"   Parameters: T={temperature}, TopP={top_p}, "
                  f"RepPen={repetition_penalty}, Speed={speed}")
            
            # Speaker embedding cache check (precompute for future optimization)
            if self.use_speaker_cache:
                _ = self._get_speaker_embedding(speaker_wav)
            
            # Output dizini kontrol et
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # TTS çağrısı - Coqui XTTS v2 parametreleri
            # FP32 Mode (Safest for XTTS v2 on T4)
            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language=language,
                file_path=output_path,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                speed=speed,
                **kwargs
            )
            
            # Dosya oluşturuldu mu kontrol et
            if not os.path.exists(output_path):
                print(f"❌ Output file not created: {output_path}")
                return False
                
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                print(f"❌ Output file is empty: {output_path}")
                return False

            # Task 3.1: Kalite kontrolü (çok kısa / çok sessiz / yarıda kesik chunk'ları yakala)
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_wav(output_path)
                duration_ms = len(audio)
                duration_sec = duration_ms / 1000
                rms_db = audio.dBFS if audio.dBFS != float("-inf") else -100.0

                # Temel kalite kontrolü (çok kısa / sessiz)
                if duration_ms < self.min_chunk_duration_ms or rms_db < self.min_chunk_rms_db:
                    print(
                        "⚠ Chunk below quality thresholds "
                        f"(duration={duration_ms}ms, rms={rms_db:.2f}dB, "
                        f"min_duration={self.min_chunk_duration_ms}ms, "
                        f"min_rms={self.min_chunk_rms_db}dB). Marking as failed."
                    )
                    try:
                        os.remove(output_path)
                    except OSError as remove_error:
                        print(f"⚠ Could not remove low-quality chunk file: {remove_error}")
                    return False

                # Yarıda kesik chunk kontrolü (metin uzunluğuna göre)
                # Ortalama: 1 karakter ≈ 50ms konuşma süresi (150 kelime/dakika, 5 karakter/kelime)
                text_length = len(text)
                expected_duration_ms = text_length * 50  # Tahmini beklenen süre
                min_expected_duration_ms = expected_duration_ms * 0.3  # Minimum %30'u
                
                if duration_ms < min_expected_duration_ms and text_length > 100:
                    # Sadece uzun metinler için kontrol et (kısa metinlerde normal olabilir)
                    truncation_ratio = (duration_ms / expected_duration_ms) * 100
                    print(
                        f"⚠ TRUNCATED AUDIO DETECTED! "
                        f"Text: {text_length} chars, "
                        f"Expected: ~{expected_duration_ms/1000:.1f}s, "
                        f"Got: {duration_sec:.1f}s ({truncation_ratio:.0f}%)"
                    )
                    print(f"   Text preview: {text[:80]}...")
                    # Yarıda kesik ses dosyasını sil ve retry tetikle
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass
                    return False

                # Task 1.3.3: Cümle sonlarına sessizlik ekle (halüsinasyon önleme)
                audio_with_pause = audio + AudioSegment.silent(duration=350)
                audio_with_pause.export(output_path, format="wav")
                print(f"✓ Audio generated: {duration_sec:.1f}s, {file_size:,} bytes")
                
            except Exception as silence_error:
                print(f"⚠ Warning: Could not add silence / run quality check: {silence_error}")
                # Devam et, kritik hata değil
                print(f"✓ Audio generated: {file_size:,} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ Audio generation error: {type(e).__name__}")
            print(f"   Detail: {str(e)}")
            return False

    def release_memory(self):
        """VRAM/RAM temizliği"""
        try:
            if self.use_gpu:
                torch.cuda.empty_cache()
            gc.collect()
        except Exception as e:
            print(f"⚠ Memory cleanup error: {e}")
    
    def print_stats(self):
        """Print engine statistics including cache stats."""
        print("\n📊 TTS Engine Stats:")
        print(f"  Device: {self.device.upper()}")
        if self._speaker_cache:
            stats = self._speaker_cache.stats()
            print(f"  Speaker Cache: {stats['size']}/{stats['max_size']} "
                  f"(hits: {stats['hits']}, misses: {stats['misses']}, rate: {stats['hit_rate']})")
        
        # GPU stats
        if self.use_gpu:
            gpu_stats = self.get_gpu_stats()
            if gpu_stats:
                print(f"  GPU: {gpu_stats.get('name', 'Unknown')}")
                print(f"  VRAM: {gpu_stats.get('vram_used_gb', 0):.2f}/{gpu_stats.get('vram_total_gb', 0):.2f} GB "
                      f"({gpu_stats.get('vram_percent', 0):.1f}%)")
                if 'temperature' in gpu_stats:
                    print(f"  Temperature: {gpu_stats['temperature']}°C")
    
    # ==================== GPU MONITORING ====================
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """
        Get current GPU statistics.
        
        Returns:
            Dictionary with GPU stats (name, vram, temperature, utilization)
        """
        if not self.use_gpu or not torch.cuda.is_available():
            return {}
        
        try:
            device = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device)
            
            # Memory stats
            vram_total = props.total_memory / 1e9
            vram_allocated = torch.cuda.memory_allocated(device) / 1e9
            vram_reserved = torch.cuda.memory_reserved(device) / 1e9
            vram_percent = (vram_allocated / vram_total) * 100 if vram_total > 0 else 0
            
            stats = {
                "name": props.name,
                "vram_total_gb": vram_total,
                "vram_allocated_gb": vram_allocated,
                "vram_reserved_gb": vram_reserved,
                "vram_used_gb": vram_allocated,
                "vram_percent": vram_percent,
                "compute_capability": f"{props.major}.{props.minor}",
            }
            
            # Try to get temperature via nvidia-smi (optional)
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=temperature.gpu,utilization.gpu', 
                     '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split(', ')
                    if len(parts) >= 2:
                        stats['temperature'] = int(parts[0])
                        stats['utilization'] = int(parts[1])
            except Exception:
                pass  # nvidia-smi not available or failed
            
            return stats
            
        except Exception as e:
            print(f"⚠ GPU stats error: {e}")
            return {}
    
    def check_gpu_health(self) -> Tuple[bool, str]:
        """
        Check GPU health status.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        if not self.use_gpu:
            return True, "CPU mode"
        
        stats = self.get_gpu_stats()
        if not stats:
            return True, "Could not get GPU stats"
        
        warnings = []
        
        # Temperature check
        temp = stats.get('temperature')
        if temp:
            if temp >= settings.GPU_TEMP_CRITICAL_C:
                warnings.append(f"🔴 CRITICAL: GPU temperature {temp}°C >= {settings.GPU_TEMP_CRITICAL_C}°C")
            elif temp >= settings.GPU_TEMP_WARNING_C:
                warnings.append(f"🟡 WARNING: GPU temperature {temp}°C >= {settings.GPU_TEMP_WARNING_C}°C")
        
        # VRAM check
        vram_percent = stats.get('vram_percent', 0)
        if vram_percent >= settings.GPU_VRAM_WARNING_PERCENT:
            warnings.append(f"🟡 WARNING: VRAM usage {vram_percent:.1f}% >= {settings.GPU_VRAM_WARNING_PERCENT}%")
        
        if warnings:
            return False, "; ".join(warnings)
        
        return True, f"GPU healthy (Temp: {temp}°C, VRAM: {vram_percent:.1f}%)" if temp else "GPU healthy"
    
    def monitor_and_log(self):
        """Monitor GPU and log stats. Call periodically during processing."""
        if not self.use_gpu or not settings.GPU_MONITOR_ENABLED:
            return
        
        is_healthy, message = self.check_gpu_health()
        if not is_healthy:
            print(f"⚠ GPU Health: {message}")


if __name__ == "__main__":
    try:
        print("=" * 50)
        print("GPU/CPU TEST")
        print("=" * 50)
        print(f"PyTorch Version: {torch.__version__}")
        print(f"CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        print("=" * 50)
        
        engine = TTSEngine(use_gpu=torch.cuda.is_available())
        print("\n✅ Engine created successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import sys
        sys.exit(1)
