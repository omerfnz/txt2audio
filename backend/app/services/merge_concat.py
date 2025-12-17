import asyncio
import os
from pathlib import Path
import logging
from typing import List, Dict

from pydub import AudioSegment

from ..core.config import settings
from ..db.models import Chunk, Project
from .websocket import manager

logger = logging.getLogger("ai_audiobook_studio")


async def merge_project_audio(
    project: Project,
    chunks: List[Chunk],
    project_output_dir: Path,
) -> Path:
    """
    Chunk WAV dosyalarını ffmpeg concat ile birleştirir.
    Sessizlikleri ekler, concat list oluşturur, mp3 üretir.
    Dönen değer: oluşturulan mp3 yolu.
    """
    concat_list_path = project_output_dir / "concat_list.txt"
    silence_cache: Dict[int, str] = {}

    valid_chunks = [chunk for chunk in chunks if chunk.chunk_audio_path and os.path.exists(chunk.chunk_audio_path)]
    total_valid = len(valid_chunks)

    if total_valid == 0:
        raise RuntimeError(f"No valid audio chunks to merge for project {project.id}")

    output_filename_wav = f"{project.name}_final.wav"
    output_path_wav = project_output_dir / output_filename_wav

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(valid_chunks):
            chunk_path = chunk.chunk_audio_path
            safe_chunk_path = str(chunk_path).replace("\\", "/")
            f.write(f"file '{safe_chunk_path}'\n")

            silence_duration = settings.CHUNK_SILENCE_DURATION
            if chunk.text_content:
                text = chunk.text_content.strip()
                if text and not any(text.endswith(end) for end in ['.', '!', '?', '"', "'", '”', '’']):
                    if text.endswith((',', ';', ':')):
                        silence_duration = 50
                    else:
                        silence_duration = 10

            if silence_duration > 0:
                if silence_duration not in silence_cache:
                    silence_filename = f"silence_{silence_duration}ms.wav"
                    silence_path = project_output_dir / silence_filename
                    if not silence_path.exists():
                        AudioSegment.silent(duration=silence_duration).export(str(silence_path), format="wav")
                    silence_cache[silence_duration] = str(silence_path).replace("\\", "/")

                f.write(f"file '{silence_cache[silence_duration]}'\n")

            if total_valid > 0 and idx % 10 == 0:
                merge_progress = 99.0 + (idx / total_valid) * 0.5
                await manager.broadcast({
                    "type": "progress_update",
                    "project_id": project.id,
                    "progress": merge_progress
                })

    await manager.broadcast({
        "type": "progress_update",
        "project_id": project.id,
        "progress": 99.5
    })

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_list_path),
        '-ar', '44100',  # Sample rate'i zorla 44.1kHz'e çıkar (audiobook standardı)
        '-c:a', 'pcm_s16le',  # WAV formatında çıktı (MP3 yerine)
        str(output_path_wav)
    ]

    await asyncio.to_thread(
        _run_ffmpeg,
        cmd,
        output_path_wav,
    )

    # Cleanup silence files and concat list
    for silence_file in silence_cache.values():
        try:
            if os.path.exists(silence_file):
                os.remove(silence_file)
        except Exception:
            pass

    if concat_list_path.exists():
        try:
            os.remove(concat_list_path)
        except Exception:
            pass

    # Delete chunk wavs and clear paths
    for chunk in chunks:
        if chunk.chunk_audio_path and os.path.exists(chunk.chunk_audio_path):
            try:
                os.remove(chunk.chunk_audio_path)
            except Exception as e:
                logger.warning("Could not delete chunk file %s: %s", chunk.chunk_audio_path, e)
        chunk.chunk_audio_path = None

    await manager.broadcast({
        "type": "progress_update",
        "project_id": project.id,
        "progress": 99.8
    })

    return output_path_wav


def _run_ffmpeg(cmd: List[str], output_path: Path):
    import subprocess
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logger.info("Merged audio saved: %s", output_path)
