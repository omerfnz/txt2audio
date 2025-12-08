import os
import torch
import gc
import soundfile as sf
import io
import time
from typing import Optional, Tuple, Generator
from pathlib import Path

# Config import
from ..core.config import settings

# F5-TTS Imports (Lazy import to avoid loading unless needed)
try:
    from f5_tts.api import F5TTS
    from f5_tts.infer.utils_infer import load_model, load_vocoder
except ImportError:
    print("⚠ F5-TTS library not found. Install with 'pip install f5-tts'")
    F5TTS = None

class F5TTSEngine:
    """
    F5-TTS Engine Wrapper for txt2audio project.
    
    Features:
    - Flow Matching based non-autoregressive TTS
    - WebSocket streaming support
    - Memory management (Load/Unload)
    """
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(F5TTSEngine, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        # Check available VRAM and decide device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # If VRAM is too low (< 4GB), force CPU to avoid OOM crashes
        # 2GB VRAM cards (like MX330) crash with OOM on F5-TTS
        if self.device == "cuda":
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"  🔍 Detected VRAM: {vram_gb:.2f} GB")
            if vram_gb < 3.5:
                print(f"  ⚠ Low VRAM detected (< 3.5GB). Forcing CPU mode to prevent OOM crash.")
                print(f"  ℹ Processing will be slower but stable.")
                self.device = "cpu"
                
        self.model = None
        self.is_loaded = False
        
        # Model paths (can be configured in settings)
        self.ckpt_file = settings.F5_MODEL_CKPT if hasattr(settings, "F5_MODEL_CKPT") else "" # HuggingFace repo or local path
        self.vocab_file = settings.F5_VOCAB_FILE if hasattr(settings, "F5_VOCAB_FILE") else ""
        
        self.initialized = True

    def load_model(self):
        """Loads the F5-TTS model into VRAM."""
        if self.is_loaded and self.model is not None:
            return

        if F5TTS is None:
            raise ImportError("F5-TTS library is not installed.")

        print(f"📦 Loading F5-TTS model on {self.device.upper()}...")
        try:
            start_time = time.time()
            
            # Initialize F5TTS API
            # Note: F5TTS class handles model downloading from HF automatically if path is repo ID
            self.model = F5TTS(
                model="F5TTS_Base", # Varsayılan "F5TTS_v1_Base" ama uyumluluk için "F5TTS_Base" kullanabiliriz
                device=self.device,
            )
            
            # Compile only if on CUDA
            if self.device == "cuda" and os.name != "nt":  
                try:
                    print("  ⚡ Compiling model with torch.compile...")
                    self.model.model = torch.compile(self.model.model, mode="reduce-overhead")
                except Exception as e:
                    print(f"  ⚠ torch.compile failed (safe to ignore): {e}")

            self.is_loaded = True
            print(f"✓ F5-TTS Loaded in {time.time() - start_time:.2f}s")
            
            self._log_gpu_memory("After F5 Load")

        except Exception as e:
            print(f"❌ F5-TTS Load Error: {e}")
            self.is_loaded = False
            raise

    def unload_model(self):
        """Unloads the model to free VRAM."""
        if self.model is not None:
            print("🧹 Unloading F5-TTS model...")
            del self.model
            self.model = None
        
        self.is_loaded = False
        if self.device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()
        self._log_gpu_memory("After F5 Unload")

    def generate_stream(
        self, 
        text: str, 
        ref_audio: str, 
        ref_text: str = None,
        speed: float = 0.9
    ) -> Generator[bytes, None, None]:
        """
        Generates audio and yields chunks (bytes) for streaming.
        
        Note: F5-TTS currently generates full sentences. We will stream
        sentence-by-sentence or chunk-by-chunk if supported.
        """
        if not self.is_loaded:
            self.load_model()

        print(f"🎵 F5-TTS Generating: {text[:50]}...")
        
        # Ensure ref_audio is absolute path
        if not os.path.isabs(ref_audio):
            ref_audio = os.path.join(os.getcwd(), ref_audio)

        try:
            # infer returns (wav_np, sr, spectrogram)
            # We can use 'yield' if we modify the infer loop, but standard API returns full audio
            # For "streaming" feeling, we should split text into sentences outside and call this per sentence.
            # Here we assume 'text' is a chunk/sentence.
            
            wav, sr, _ = self.model.infer(
                ref_file=ref_audio,
                ref_text=ref_text if ref_text else "", # If empty, it uses ASR
                gen_text=text,
                remove_silence=True, # Natural pause removal
                speed=speed,
                nfe_step=16  # Reduced from 32 for performance on low VRAM
            )

            # Convert numpy array to WAV bytes
            byte_io = io.BytesIO()
            sf.write(byte_io, wav, sr, format='WAV')
            yield byte_io.getvalue()

        except Exception as e:
            print(f"❌ F5 Generation Error: {e}")
            raise

    def generate_audio_file(
        self,
        text: str,
        ref_audio: str,
        output_path: str,
        ref_text: str = None,
        speed: float = 0.9,
        **kwargs # Ignore extra args like temperature
    ) -> bool:
        """
        Generates audio and saves to file (wav).
        Used for background processing/saving.
        """
        if not self.is_loaded:
            self.load_model()
            
        print(f"🎵 F5-TTS Generating to file: {text[:50]}...")
        
        # Ensure ref_audio is absolute path
        if not os.path.isabs(ref_audio):
            ref_audio = os.path.join(os.getcwd(), ref_audio)
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # infer returns (wav_np, sr, spectrogram)
            wav, sr, _ = self.model.infer(
                ref_file=ref_audio,
                ref_text=ref_text if ref_text else "",
                gen_text=text,
                remove_silence=True,
                speed=speed,
                nfe_step=16 if self.device == "cpu" else 16  # Keep 16 for both to be safe for now, 32 is too heavy
            )
            
            # Save to file
            sf.write(output_path, wav, sr)
            
            # Check if file created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            return False
            
        except Exception as e:
            print(f"❌ F5 File Generation Error: {e}")
            return False

    def _log_gpu_memory(self, context: str = ""):
        if self.device == "cuda":
            allocated = torch.cuda.memory_allocated(0) / 1e9
            reserved = torch.cuda.memory_reserved(0) / 1e9
            print(f"  📊 GPU Memory {context}: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")

