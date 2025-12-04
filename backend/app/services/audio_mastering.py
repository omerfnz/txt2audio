"""
Audio mastering servisi.
ACX/Audible standartlarına uygun ses normalleştirme.
"""
import subprocess
import os
from pathlib import Path
from typing import Optional
from pydub import AudioSegment


class AudioMastering:
    """
    Profesyonel ses mastering servisi.
    ACX standartlarına göre normalizasyon.
    """
    
    def __init__(self):
        self.target_rms = -20.0  # ACX hedef RMS (dB)
        self.target_peak = -3.0  # ACX hedef peak (dB)
        self.loudness_range = 7.0  # EBU R128 loudness range
    
    def normalize_for_acx(
        self,
        input_path: str,
        output_path: str,
        use_ffmpeg_normalize: bool = True
    ) -> bool:
        """
        Ses dosyasını ACX standartlarına göre normalize eder.
        
        Args:
            input_path: Giriş ses dosyası (WAV/MP3)
            output_path: Çıkış ses dosyası (MP3)
            use_ffmpeg_normalize: ffmpeg-normalize kullan (daha profesyonel)
            
        Returns:
            Başarılı ise True
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Çıkış dizinini oluştur
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if use_ffmpeg_normalize and self._check_ffmpeg_normalize():
            return self._normalize_with_ffmpeg(input_path, output_path)
        else:
            return self._normalize_with_pydub(input_path, output_path)
    
    def _check_ffmpeg_normalize(self) -> bool:
        """ffmpeg-normalize kurulu mu kontrol et"""
        try:
            subprocess.run(
                ['ffmpeg-normalize', '--version'],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _normalize_with_ffmpeg(self, input_path: str, output_path: str) -> bool:
        """ffmpeg-normalize ile profesyonel normalizasyon"""
        try:
            print(f"🎚️ Normalizing with ffmpeg-normalize...")
            
            # ffmpeg-normalize parametreleri (EBU R128 standardı)
            cmd = [
                'ffmpeg-normalize',
                input_path,
                '-o', output_path,
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '--normalization-type', 'ebu',
                '--target-level', str(self.target_rms),
                '--loudness-range-target', str(self.loudness_range),
                '--true-peak', str(self.target_peak),
                '--sample-rate', '44100',
                '--keep-loudness-range-target',
                '--progress'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 dakika max
            )
            
            if result.returncode == 0:
                print(f"✓ Normalization complete: {output_path}")
                return True
            else:
                print(f"⚠ ffmpeg-normalize failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Normalization timeout")
            return False
        except Exception as e:
            print(f"❌ Normalization error: {e}")
            return False
    
    def _normalize_with_pydub(self, input_path: str, output_path: str) -> bool:
        """pydub ile basit normalizasyon (fallback)"""
        try:
            print(f"🎚️ Normalizing with pydub (basic)...")
            
            # Dosyayı yükle
            if input_path.endswith('.mp3'):
                audio = AudioSegment.from_mp3(input_path)
            else:
                audio = AudioSegment.from_wav(input_path)
            
            # Peak normalization (basit)
            target_dBFS = -3.0  # ACX peak hedefi
            change_in_dBFS = target_dBFS - audio.max_dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            # MP3 olarak export
            normalized_audio.export(
                output_path,
                format='mp3',
                bitrate='192k',
                parameters=["-ar", "44100"]
            )
            
            print(f"✓ Basic normalization complete: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ pydub normalization error: {e}")
            return False
    
    def apply_compression(
        self,
        audio: AudioSegment,
        threshold: float = -20.0,
        ratio: float = 4.0
    ) -> AudioSegment:
        """
        Basit compression uygula.
        
        Args:
            audio: Ses segment
            threshold: Threshold (dB)
            ratio: Compression ratio
            
        Returns:
            Compressed audio
        """
        # pydub ile basit compression
        # Not: Gerçek compression için ffmpeg kullanılmalı
        compressed = audio.compress_dynamic_range(
            threshold=threshold,
            ratio=ratio
        )
        return compressed
