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
    
    def _get_output_codec(self, output_path: str) -> tuple[str, bool]:
        """
        Çıktı formatına göre codec ve WAV olup olmadığını döndürür.
        
        Returns:
            (codec, is_wav) tuple
        """
        is_wav = output_path.endswith('.wav')
        codec = 'pcm_s16le' if is_wav else 'libmp3lame'
        return codec, is_wav
    
    def _build_ffmpeg_cmd_with_bitrate(self, base_cmd: list, is_wav: bool, bitrate: str = '192k') -> list:
        """
        FFmpeg komutuna bitrate parametresini ekler (WAV için eklemez).
        
        Args:
            base_cmd: Temel FFmpeg komutu listesi
            is_wav: WAV formatı mı?
            bitrate: Bitrate değeri
            
        Returns:
            Temizlenmiş komut listesi
        """
        if not is_wav:
            base_cmd.extend(['-b:a', bitrate])
        return [c for c in base_cmd if c is not None]
    
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
            
            # Çıktı formatına göre codec belirle
            codec, is_wav = self._get_output_codec(output_path)
            
            # ffmpeg-normalize parametreleri (EBU R128 standardı)
            cmd = [
                'ffmpeg-normalize',
                input_path,
                '-o', output_path,
                '-c:a', codec,
                '--normalization-type', 'ebu',
                '--target-level', str(self.target_rms),
                '--loudness-range-target', str(self.loudness_range),
                '--true-peak', str(self.target_peak),
                '--sample-rate', '44100',
                '--keep-loudness-range-target',
                '--progress'
            ]
            
            # WAV için bitrate ekleme, MP3 için ekle
            cmd = self._build_ffmpeg_cmd_with_bitrate(cmd, is_wav, '192k')
            
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
        """
        FFmpeg 'loudnorm' filtresi ile normalizasyon (Fallback yerine ana yöntem olarak kullanılabilir).
        Pydub yerine FFmpeg kullanarak bellek sorunlarını (OOM) önler.
        """
        try:
            print(f"🎚️ Normalizing with FFmpeg loudnorm filter...")
            
            # ACX Hedefleri:
            # RMS: -23dB ile -18dB arası (Hedef -20dB)
            # Peak: -3.0dB
            # Noise Floor: -60dB (buna müdahale edemeyiz filter ile, noise gate gerekir)
            
            # loudnorm parametreleri:
            # I (Integrated Loudness) -> -20.0 (ACX RMS hedefi gibi düşünülebilir)
            # TP (True Peak) -> -3.0
            # LRA (Loudness Range) -> 7.0
            
            # Peak limiter ekle: alimiter ile peak'i -3.0 dB altına indir
            # loudnorm + alimiter kombinasyonu
            af_filter = (
                f'loudnorm=I={self.target_rms}:TP={self.target_peak}:LRA={self.loudness_range}:print_format=json,'
                f'alimiter=level_in=1:level_out=1:limit={self.target_peak}:attack=7:release=100:level=disabled'
            )
            
            # Çıktı formatına göre codec belirle
            codec, is_wav = self._get_output_codec(output_path)
            
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-af', af_filter,
                '-c:a', codec,
                '-ar', '44100',
            ]
            
            # WAV için bitrate ekleme, MP3 için ekle
            cmd = self._build_ffmpeg_cmd_with_bitrate(cmd, is_wav, '192k')
            cmd.append(output_path)
            
            # 1 saatlik ses için timeout süresini uzat (10 dakika)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                print(f"✓ FFmpeg loudnorm complete: {output_path}")
                return True
            else:
                print(f"⚠ FFmpeg loudnorm failed: {result.stderr}")
                return False
            
        except subprocess.TimeoutExpired:
            print(f"❌ Normalization timeout (files too large?)")
            return False
        except Exception as e:
            print(f"❌ FFmpeg normalization error: {e}")
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
