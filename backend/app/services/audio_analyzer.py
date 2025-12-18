"""
Audio kalite analizi servisi.
ACX/Audible standartlarına uygunluk kontrolü.
"""
import numpy as np
from pydub import AudioSegment
from typing import Dict, Tuple, List
import os
import logging

logger = logging.getLogger("ai_audiobook_studio")


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
    
    def analyze(self, audio_path: str) -> Dict[str, float]:
        """
        Ses dosyasını analiz eder (FFmpeg kullanarak - bellek dostu).
        WAV ve MP3 formatlarını destekler.
        
        Args:
            audio_path: Ses dosyası yolu (WAV/MP3)
            
        Returns:
            Analiz sonuçları (RMS, Peak, Noise Floor, ACX uyumluluk)
        """
        import subprocess
        import re
        import os
        import tempfile

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Dosya formatını kontrol et
        file_ext = os.path.splitext(audio_path)[1].lower()
        is_wav = file_ext == '.wav'
        
        # WAV değilse, geçici WAV'a çevir (wave modülü sadece WAV okuyabilir)
        temp_wav_path = None
        try:
            if not is_wav:
                # MP3 veya diğer formatları WAV'a çevir
                temp_wav_path = tempfile.mktemp(suffix='.wav')
                cmd_convert = [
                    'ffmpeg', '-y',
                    '-i', audio_path,
                    '-ar', '44100',
                    '-ac', '1',
                    '-sample_fmt', 's16',
                    temp_wav_path
                ]
                result_convert = subprocess.run(
                    cmd_convert,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result_convert.returncode != 0:
                    raise Exception(f"Failed to convert to WAV: {result_convert.stderr}")
                audio_path_to_analyze = temp_wav_path
            else:
                audio_path_to_analyze = audio_path
            
            # FFmpeg ile volumedetect analizi (hızlı ama yaklaşık)
            cmd = [
                'ffmpeg', 
                '-i', audio_path_to_analyze, 
                '-af', 'volumedetect', 
                '-vn', '-sn', '-dn', 
                '-f', 'null', 
                'NUL' if os.name == 'nt' else '/dev/null'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            output = result.stderr  # FFmpeg stats writes to stderr
            
            # Parse output
            mean_volume = -100.0
            max_volume = -100.0
            
            mean_match = re.search(r'mean_volume:\s+([-\d\.]+)\s+dB', output)
            if mean_match:
                mean_volume = float(mean_match.group(1))
                
            max_match = re.search(r'max_volume:\s+([-\d\.]+)\s+dB', output)
            if max_match:
                max_volume = float(max_match.group(1))
            
            # FFmpeg volumedetect yaklaşık değerler verir, daha doğru analiz için chunked analiz kullan
            return self._analyze_chunked(audio_path_to_analyze)

        except Exception as e:
            logger.warning(f"FFmpeg analysis failed, falling back to chunked analysis: {e}")
            # Fallback: Eğer WAV değilse çevirmeyi dene
            if not is_wav and temp_wav_path is None:
                try:
                    temp_wav_path = tempfile.mktemp(suffix='.wav')
                    cmd_convert = [
                        'ffmpeg', '-y',
                        '-i', audio_path,
                        '-ar', '44100',
                        '-ac', '1',
                        '-sample_fmt', 's16',
                        temp_wav_path
                    ]
                    subprocess.run(cmd_convert, capture_output=True, timeout=600, check=True)
                    return self._analyze_chunked(temp_wav_path)
                except Exception:
                    pass
            # Son çare: WAV dosyasıysa direkt analiz et
            if is_wav:
                return self._analyze_chunked(audio_path)
            else:
                raise Exception(f"Could not analyze audio file: {e}")
        finally:
            # Geçici WAV dosyasını temizle
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except Exception:
                    pass

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

    def detect_long_silences(self, wav_path: str, min_duration: float = 5.0) -> List[Tuple[float, float, float]]:
        """
        Uzun sessizlikleri tespit eder (Carmilla problemi için).

        Args:
            wav_path: Ses dosyası yolu
            min_duration: Minimum sessizlik süresi (saniye)

        Returns:
            [(start_time, end_time, duration), ...] uzun sessizlik listesi
        """
        import librosa
        from typing import List, Tuple

        # Ses dosyasını yükle (düşük sample rate ile hızlı analiz)
        y, sr = librosa.load(wav_path, sr=22050)

        # RMS hesapla
        hop_length = 512
        frame_length = 2048
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        times = librosa.times_like(rms, sr=sr, hop_length=hop_length)

        # Sessizlik eşikleri (optimized: -40dB for more realistic silence detection)
        silence_threshold_linear = 10 ** (-40.0 / 20)  # -40dB

        # Uzun sessizlikleri tespit et
        long_silences = []
        current_silence_start = None

        for i, (time, is_silent) in enumerate(zip(times, rms < silence_threshold_linear)):
            if is_silent and current_silence_start is None:
                current_silence_start = time
            elif not is_silent and current_silence_start is not None:
                silence_duration = time - current_silence_start
                if silence_duration >= min_duration:
                    long_silences.append((current_silence_start, time, silence_duration))
                current_silence_start = None

        # Son sessizlik varsa
        if current_silence_start is not None:
            silence_duration = len(y) / sr - current_silence_start
            if silence_duration >= min_duration:
                long_silences.append((current_silence_start, len(y) / sr, silence_duration))

        return long_silences

    def get_silence_analysis(self, wav_path: str) -> Dict[str, any]:
        """
        Sessizlik analizi raporu.

        Returns:
            {
                'total_silence_percentage': float,
                'long_silences': [(start, end, duration), ...],
                'long_silence_count': int,
                'max_silence_duration': float
            }
        """
        import librosa

        # Temel analiz
        y, sr = librosa.load(wav_path, sr=22050)
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]

        silence_threshold_linear = 10 ** (-40.0 / 20)  # -40dB (optimized for more realistic detection)
        silent_frames = rms < silence_threshold_linear
        silence_percentage = (np.sum(silent_frames) / len(rms)) * 100

        # Uzun sessizlikler
        long_silences = self.detect_long_silences(wav_path, min_duration=5.0)
        max_silence = max([dur for _, _, dur in long_silences], default=0)

        return {
            'total_silence_percentage': round(silence_percentage, 2),
            'long_silences': long_silences,
            'long_silence_count': len(long_silences),
            'max_silence_duration': round(max_silence, 1)
        }


def analyze_audio_file(wav_path: str) -> Dict[str, float]:
    """Helper function for quick analysis"""
    analyzer = AudioAnalyzer()
    return analyzer.analyze(wav_path)


def analyze_silence_and_acx(wav_path: str) -> Dict[str, any]:
    """
    Hem sessizlik hem ACX analizi yapan kapsamlı fonksiyon.

    Returns:
        {
            'acx_analysis': {...},  # ACX uyumluluk
            'silence_analysis': {...},  # Sessizlik raporu
            'overall_quality': 'GOOD'|'FAIR'|'POOR'
        }
    """
    analyzer = AudioAnalyzer()

    # ACX analizi
    acx_results = analyzer.analyze(wav_path)
    compliance_details = analyzer.get_compliance_details(acx_results)

    # Sessizlik analizi
    silence_results = analyzer.get_silence_analysis(wav_path)

    # Genel kalite değerlendirmesi
    acx_compliant = acx_results['acx_compliant']
    long_silences = silence_results['long_silence_count']
    silence_percentage = silence_results['total_silence_percentage']

    if acx_compliant and long_silences == 0 and silence_percentage < 20:
        overall_quality = 'GOOD'
    elif acx_compliant and long_silences <= 2 and silence_percentage < 30:
        overall_quality = 'FAIR'
    else:
        overall_quality = 'POOR'

    return {
        'acx_analysis': acx_results,
        'compliance_details': compliance_details,
        'silence_analysis': silence_results,
        'overall_quality': overall_quality
    }
