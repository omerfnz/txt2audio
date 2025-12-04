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
        Ses dosyasını analiz eder.
        
        Args:
            wav_path: WAV dosya yolu
            
        Returns:
            Analiz sonuçları (RMS, Peak, Noise Floor, ACX uyumluluk)
        """
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"Audio file not found: {wav_path}")
        
        # Ses dosyasını yükle
        audio = AudioSegment.from_wav(wav_path)
        
        # NumPy array'e çevir
        samples = np.array(audio.get_array_of_samples())
        
        # Normalize to float (-1.0 to 1.0)
        if audio.sample_width == 2:  # 16-bit
            samples = samples / 32768.0
        elif audio.sample_width == 3:  # 24-bit
            samples = samples / 8388608.0
        elif audio.sample_width == 4:  # 32-bit
            samples = samples / 2147483648.0
        
        # Stereo ise mono'ya çevir
        if audio.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)
        
        # RMS (Root Mean Square) hesapla
        rms = np.sqrt(np.mean(samples**2))
        rms_db = 20 * np.log10(rms) if rms > 0 else -100.0
        
        # Peak hesapla
        peak = np.max(np.abs(samples))
        peak_db = 20 * np.log10(peak) if peak > 0 else -100.0
        
        # Noise Floor hesapla (en düşük %10'luk kısım)
        sorted_samples = np.sort(np.abs(samples))
        noise_samples = sorted_samples[:int(len(sorted_samples) * 0.1)]
        noise_floor = np.mean(noise_samples)
        noise_floor_db = 20 * np.log10(noise_floor) if noise_floor > 0 else -100.0
        
        # ACX uyumluluk kontrolü
        acx_compliant = self._check_acx_compliance(rms_db, peak_db, noise_floor_db)
        
        return {
            "rms_db": round(rms_db, 2),
            "peak_db": round(peak_db, 2),
            "noise_floor_db": round(noise_floor_db, 2),
            "acx_compliant": acx_compliant,
            "duration_seconds": len(audio) / 1000.0,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels
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
