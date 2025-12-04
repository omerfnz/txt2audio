import os
import sys
import torch
import gc
import platform
from typing import Optional
import shutil

class TTSEngine:
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.tts: Optional[object] = None
        self.use_deepspeed = False

        # Quality thresholds for individual chunks (to detect silent/invalid outputs)
        # Duration in milliseconds and RMS level in dBFS
        self.min_chunk_duration_ms = 700   # ~0.7s minimum duration
        self.min_chunk_rms_db = -50.0      # below this treated as "too quiet / likely silence"
        
        # Model indirme dizini
        self.model_path = os.path.join(os.getcwd(), "storage", "models")
        os.environ["TTS_HOME"] = self.model_path
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # espeak-ng pathini bul ve ayarla
        self._setup_espeak()

        # GPU / DeepSpeed bilgisi
        if self.use_gpu:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✓ GPU Modu: {gpu_name}")
            print(f"  VRAM: {vram_gb:.2f} GB")
            # Düşük VRAM uyarısı
            if vram_gb < 4:
                print("  ⚠ VRAM düşük! Büyük metinlerde sorun yaşanabilir.")

            # DeepSpeed sadece Linux/WSL + GPU için denenir
            if platform.system() != "Windows":
                try:
                    import deepspeed  # type: ignore  # noqa: F401
                    self.use_deepspeed = True
                    print("✓ DeepSpeed kurulu ve GPU ortamında kullanılabilir.")
                except Exception:
                    print("ℹ DeepSpeed bulunamadı veya yüklenemedi. Standart PyTorch ile devam edilecek.")
            else:
                print("ℹ DeepSpeed Windows ortamında otomatik olarak devre dışı bırakıldı.")
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
        if self.tts is None:
            try:
                from TTS.api import TTS
                print(f"📦 Loading XTTS v2 model on {self.device.upper()}...")
                
                # Model yükle - FIX: deprecated gpu parametresi kaldırıldı
                self.tts = TTS(
                    self.model_name,
                    progress_bar=True  # Progress göster
                )
                
                # GPU'ya taşı (eğer istenmişse)
                if self.use_gpu:
                    print(f"🔄 Moving model to {self.device.upper()}...")
                    self.tts = self.tts.to(self.device)
                
                print("✓ Model loaded successfully.")
                
                # Düşük VRAM için optimize et
                if self.use_gpu:
                    torch.cuda.empty_cache()
                    
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
            
            # Output dizini kontrol et
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # TTS çağrısı - Coqui XTTS v2 parametreleri
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

            # Task 3.1: Basit kalite kontrolü (çok kısa / çok sessiz chunk'ları yakala)
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_wav(output_path)
                duration_ms = len(audio)
                rms_db = audio.dBFS if audio.dBFS != float("-inf") else -100.0

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

                # Task 1.3.3: Cümle sonlarına sessizlik ekle (halüsinasyon önleme)
                audio_with_pause = audio + AudioSegment.silent(duration=350)
                audio_with_pause.export(output_path, format="wav")
                print("✓ Added 350ms silence to chunk")
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
                print("🧹 GPU memory cleared")
            gc.collect()
        except Exception as e:
            print(f"⚠ Memory cleanup error: {e}")

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
