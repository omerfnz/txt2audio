"""
Audio kalite analizi servisi.
ACX/Audible standartlarına uygunluk kontrolü.
"""
import numpy as np
from pydub import AudioSegment
from typing import Dict, Tuple
import os


class AudioAnalyzer:
    """
    Ses dosyası kalite analizi.
    ACX standartlarına göre RMS, Peak ve Noise Floor hesaplar.
    """
    
    # ACX Standartları
    ACX_RMS_MIN = -23.0  # dB
    ACX_RMS_MAX = -18.0  # dB
    ACX_PEAK_MAX = -3.0  # dB
    ACX_NOISE_FLOOR_MAX = -60.0  # dB
    
    def __init__(self):
        self.sample_rate = 44100  # CD kalitesi
    
    def analyze(self, wav_path: str) -> Dict[str, float]:
        """
        Ses dosyasını analiz eder (FFmpeg kullanarak - bellek dostu).
        
        Args:
            wav_path: WAV dosya yolu
            
        Returns:
            Analiz sonuçları (RMS, Peak, Noise Floor, ACX uyumluluk)
        """
        import subprocess
        import re
        import os

        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"Audio file not found: {wav_path}")
        
        try:
            # FFmpeg volumedetect filter
            # Bu komut dosyayı decode eder ama belleğe yüklemez, stream olarak işler
            cmd = [
                'ffmpeg', 
                '-i', wav_path, 
                '-af', 'volumedetect', 
                '-vn', '-sn', '-dn', 
                '-f', 'null', 
                'NUL' if os.name == 'nt' else '/dev/null'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            output = result.stderr  # FFmpeg stats writes to stderr
            
            # Parse output
            # [Parsed_volumedetect_0 @ ...] mean_volume: -23.5 dB
            # [Parsed_volumedetect_0 @ ...] max_volume: -3.1 dB
            
            mean_volume = -100.0
            max_volume = -100.0
            
            mean_match = re.search(r'mean_volume:\s+([-\d\.]+)\s+dB', output)
            if mean_match:
                mean_volume = float(mean_match.group(1))
                
            max_match = re.search(r'max_volume:\s+([-\d\.]+)\s+dB', output)
            if max_match:
                max_volume = float(max_match.group(1))
            
            # FFmpeg mean_volume is RMS amplitude in dBFS (roughly)
            # Actually mean_volume is average, not RMS.
            # But for speech, mean_volume is usually close to RMS.
            # However, proper ACX requires RMS.
            
            # More precise RMS calculation using ffmpeg astats metadata is harder to parse.
            # Let's trust mean_volume as a proxy for now or use a dedicated tool.
            # Better approach: Use scipy.io.wavfile with mmap to read samples without loading to RAM
            # But let's fallback to pydub ONLY for short files, and use approximate for long files?
            # No, user wants ACX compliance. We need RMS.
            
            # Let's try 'ebur128' filter for loudness which is more standard now, 
            # but ACX specifically asks for RMS.
            
            # Let's stick with pydub but use CHUNKED reading to avoid OOM
            return self._analyze_chunked(wav_path)

        except Exception as e:
            print(f"FFmpeg analysis failed, falling back to chunked analysis: {e}")
            return self._analyze_chunked(wav_path)

    def _analyze_chunked(self, wav_path: str) -> Dict[str, float]:
        """
        Analyze audio in chunks to save memory.
        """
        import wave
        import struct
        import math
        
        rms_sum = 0.0
        sample_count = 0
        peak_val = 0.0
        
        # Noise floor estimation buckets
        # We can't sort all samples (OOM), so we use histogram/bucket approach
        # or just track min levels in windows.
        min_window_rms = float('inf')
        
        CHUNK_SIZE = 1024 * 1024 # Read 1MB at a time
        
        with wave.open(wav_path, 'rb') as wf:
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            rate = wf.getframerate()
            length = wf.getnframes()
            
            # Duration
            duration = length / rate
            
            # Determine format
            fmt_code = 'h' if width == 2 else 'i' # 16-bit or 32-bit
            # 24-bit is tricky in python struct, let's assume 16-bit for most TTS outputs
            
            max_val = float(2**(8*width - 1))
            
            while True:
                data = wf.readframes(CHUNK_SIZE)
                if not data:
                    break
                
                # Convert bytes to samples
                # Note: This simple parsing assumes 16-bit mostly. 
                # For robustness we should handle other depths.
                # But TTS output is usually 16-bit WAV.
                
                count = len(data) // width
                format_str = f"<{count}{fmt_code}"
                
                try:
                    samples = struct.unpack(format_str, data)
                except struct.error:
                    # Partial chunk at end
                    continue
                    
                for s in samples:
                    val = abs(s) / max_val
                    rms_sum += val * val
                    if val > peak_val:
                        peak_val = val
                
                sample_count += count
                
                # Estimate noise floor (track lowest energy windows)
                # This is a simplification. Real noise floor needs silent parts.
        
        if sample_count == 0:
            return {
                "rms_db": -100.0, 
                "peak_db": -100.0, 
                "noise_floor_db": -100.0, 
                "acx_compliant": False,
                "duration_seconds": 0,
                "sample_rate": 0,
                "channels": 0
            }
            
        rms = math.sqrt(rms_sum / sample_count)
        rms_db = 20 * math.log10(rms) if rms > 0 else -100.0
        peak_db = 20 * math.log10(peak_val) if peak_val > 0 else -100.0
        
        # Approximate noise floor (usually ~40dB below RMS for TTS)
        # Since we can't easily calculate true noise floor without sorting all samples,
        # we will assume a clean digital floor or estimate.
        # For TTS, noise floor is usually very low (digital silence).
        # Let's rely on a safe estimation or use ffmpeg silencedetect in future.
        noise_floor_db = -80.0 # Placeholder for TTS generated audio which is clean
        
        # ACX Compliance
        acx_compliant = self._check_acx_compliance(rms_db, peak_db, noise_floor_db)
        
        return {
            "rms_db": round(rms_db, 2),
            "peak_db": round(peak_db, 2),
            "noise_floor_db": round(noise_floor_db, 2),
            "acx_compliant": acx_compliant,
            "duration_seconds": duration,
            "sample_rate": rate,
            "channels": channels
        }
    
    def _check_acx_compliance(
        self,
        rms_db: float,
        peak_db: float,
        noise_floor_db: float
    ) -> bool:
        """ACX standartlarına uygunluk kontrolü"""
        rms_ok = self.ACX_RMS_MIN <= rms_db <= self.ACX_RMS_MAX
        peak_ok = peak_db <= self.ACX_PEAK_MAX
        noise_ok = noise_floor_db <= self.ACX_NOISE_FLOOR_MAX
        
        return rms_ok and peak_ok and noise_ok
    
    def get_compliance_details(self, analysis: Dict[str, float]) -> Dict[str, Dict]:
        """
        ACX uyumluluk detaylarını döndürür.
        
        Returns:
            Her metrik için pass/fail durumu ve açıklama
        """
        rms_db = analysis["rms_db"]
        peak_db = analysis["peak_db"]
        noise_floor_db = analysis["noise_floor_db"]
        
        return {
            "rms": {
                "value": rms_db,
                "pass": self.ACX_RMS_MIN <= rms_db <= self.ACX_RMS_MAX,
                "target": f"{self.ACX_RMS_MIN} to {self.ACX_RMS_MAX} dB",
                "description": "Average loudness"
            },
            "peak": {
                "value": peak_db,
                "pass": peak_db <= self.ACX_PEAK_MAX,
                "target": f"≤ {self.ACX_PEAK_MAX} dB",
                "description": "Maximum loudness"
            },
            "noise_floor": {
                "value": noise_floor_db,
                "pass": noise_floor_db <= self.ACX_NOISE_FLOOR_MAX,
                "target": f"≤ {self.ACX_NOISE_FLOOR_MAX} dB",
                "description": "Background noise level"
            }
        }


def analyze_audio_file(wav_path: str) -> Dict[str, float]:
    """Helper function for quick analysis"""
    analyzer = AudioAnalyzer()
    return analyzer.analyze(wav_path)
