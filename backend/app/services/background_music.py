import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from ..core.config import settings

logger = logging.getLogger("ai_audiobook_studio")


async def mix_background_music(
    voice_mp3_path: str,
    bg_music_file: Optional[str],
    volume: float,
) -> Path:
    """
    Voice audio (WAV/MP3) ile arka plan müziğini (looped, sabit volume) karıştırır.
    bg_music_file boşsa veya dosya yoksa voice-only dosya olduğu gibi döner.
    """
    voice_path = Path(voice_mp3_path)
    
    if not bg_music_file:
        return voice_path

    bg_file_path = Path(bg_music_file)
    if not bg_file_path.is_absolute():
        bg_file_path = settings.MUSIC_DIR / bg_file_path.name

    if not bg_file_path.exists() or not bg_file_path.is_file():
        logger.warning("Background music file not found, skipping mix: %s", bg_file_path)
        return voice_path

    bg_volume = max(0.0, min(volume or 0.0, 1.0))

    # Çıktı formatını giriş formatına göre belirle (WAV veya MP3)
    is_wav = voice_path.suffix.lower() == '.wav'
    codec = 'pcm_s16le' if is_wav else 'libmp3lame'
    
    mixed_path = voice_path.with_name(f"{voice_path.stem}_mixed{voice_path.suffix}")
    mix_cmd = [
        'ffmpeg', '-y',
        '-i', str(voice_path),
        '-stream_loop', '-1', '-i', str(bg_file_path),
        '-filter_complex', f"[1:a]volume={bg_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2",
        '-c:a', codec,
        '-ar', '44100',
    ]
    
    # WAV için bitrate ekleme, MP3 için ekle
    if not is_wav:
        mix_cmd.extend(['-b:a', settings.EXPORT_BITRATE])
    mix_cmd.append(str(mixed_path))

    try:
        await asyncio.to_thread(_run_ffmpeg, mix_cmd)
        os.replace(mixed_path, voice_path)
        logger.info("Background music mixed | file=%s volume=%.2f", bg_file_path.name, bg_volume)
    except Exception as mix_err:
        logger.warning("Background music mix failed, keeping voice-only output: %s", mix_err)
        if mixed_path.exists():
            try:
                os.remove(mixed_path)
            except Exception:
                pass

    return voice_path


def _run_ffmpeg(cmd):
    import subprocess
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
