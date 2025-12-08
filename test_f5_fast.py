import os
import torch
import time
from f5_tts.api import F5TTS
from pathlib import Path

def test_generation():
    print("Initializing F5TTS...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    try:
        f5 = F5TTS(
            model="F5TTS_Base",
            device=device
        )
        print("Model loaded.")
        
        # Create a dummy reference audio if not exists
        ref_audio = "test_ref.wav"
        if not os.path.exists(ref_audio):
            import soundfile as sf
            import numpy as np
            # 5 seconds of silence/noise
            sr = 24000
            data = np.random.uniform(-0.1, 0.1, sr * 5)
            sf.write(ref_audio, data, sr)
            print(f"Created dummy reference audio: {ref_audio}")
            
        ref_text = "This is a reference text for the audio."
        gen_text = "This is a test generation with reduced steps."
        
        print("Starting inference (steps=16)...")
        start = time.time()
        wav, sr, spec = f5.infer(
            ref_file=ref_audio,
            ref_text=ref_text,
            gen_text=gen_text,
            remove_silence=True,
            speed=1.0,
            nfe_step=16 # Reduced from default 32
        )
        print(f"Inference completed in {time.time() - start:.2f}s")
        print(f"Output shape: {wav.shape}, SR: {sr}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()

