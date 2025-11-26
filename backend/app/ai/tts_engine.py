import os
import sys
import torch
import gc
from typing import Optional
import shutil

class TTSEngine:
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.tts: Optional[object] = None
        
        # Model indirme dizini
        self.model_path = os.path.join(os.getcwd(), "storage", "models")
        os.environ["TTS_HOME"] = self.model_path
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # espeak-ng pathini bul ve ayarla
        self._setup_espeak()
        
        # GPU Info
        if self.use_gpu:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✓ GPU Modu: {gpu_name}")
            print(f"  VRAM: {vram_gb:.2f} GB")
            # Düşük VRAM uyarısı
            if vram_gb < 4:
                print(f"  ⚠ VRAM düşük! Büyük metinlerde sorun yaşanabilir.")
        else:
            print(f"✓ CPU Modu")

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

    def generate_audio(self, text: str, speaker_wav: str, output_path: str, language: str = "en") -> bool:
        if self.tts is None:
            self.load_model()
        
        try:
            print(f"🎵 Generating audio (Device: {self.device.upper()})")
            print(f"   Text: {text[:50]}...")
            
            # Output dizini kontrol et
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # TTS çağrısı
            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language=language,
                file_path=output_path
            )
            
            # Dosya oluşturuldu mu kontrol et
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                print(f"❌ Output file empty or not created: {output_path}")
                return False
            
            file_size = os.path.getsize(output_path)
            print(f"✓ Audio generated: {file_size} bytes")
            return True
            
        except Exception as e:
            print(f"❌ Audio generation error: {type(e).__name__}")
            print(f"   Detay: {str(e)}")
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
