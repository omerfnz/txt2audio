import asyncio
import gc
import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import torch
from pydub import AudioSegment

from ..ai.text_processor import TextProcessor
from ..core.config import settings
from ..db.models import Chunk, Project
from .websocket import manager

logger = logging.getLogger("ai_audiobook_studio")

# XTTS model erişimini seri hale getirmek için global lock
gpu_lock = asyncio.Lock()


@dataclass
class ChunkRunResult:
    processed_count: int
    total_chunks: int
    failed_chunks: List[int]
    last_error: Optional[str]
    cancelled: bool


def _handle_oom_error():
    """OOM sonrası bellek temizliği."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


async def _process_single_chunk(
    chunk: Chunk,
    project: Project,
    output_path: str,
    use_gpu: bool,
    engine_provider,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Tek chunk üretimi + retry."""
    engine = engine_provider(use_gpu=use_gpu)

    async with gpu_lock:
        attempt = 0
        success = False
        chunk_error = ""

        while attempt < 5 and not success:
            try:
                base_temp = project.temperature or settings.DEFAULT_TEMPERATURE
                base_speed = project.speed or settings.DEFAULT_SPEED
                base_rep_penalty = project.repetition_penalty or settings.DEFAULT_REPETITION_PENALTY

                if attempt == 0:
                    temperature_adj = base_temp
                    speed_adj = base_speed
                    repetition_penalty_adj = base_rep_penalty
                elif attempt == 1:
                    temperature_adj = max(0.35, base_temp * 0.7)
                    speed_adj = base_speed * 0.85
                    repetition_penalty_adj = min(3.0, base_rep_penalty * 1.2)
                    logger.info(
                        "Retry 1/5 with adjusted params | chunk=%s temp=%.2f speed=%.2f rep=%.2f",
                        chunk.index,
                        temperature_adj,
                        speed_adj,
                        repetition_penalty_adj,
                    )
                elif attempt == 2:
                    temperature_adj = 0.35
                    speed_adj = 0.8
                    repetition_penalty_adj = 2.8
                    logger.info(
                        "Retry 2/5 with conservative params | chunk=%s temp=%.2f speed=%.2f rep=%.2f",
                        chunk.index,
                        temperature_adj,
                        speed_adj,
                        repetition_penalty_adj,
                    )
                elif attempt == 3:
                    temperature_adj = 0.3
                    speed_adj = 0.75
                    repetition_penalty_adj = 3.0
                    logger.info(
                        "Retry 3/5 with very conservative params | chunk=%s temp=%.2f speed=%.2f rep=%.2f",
                        chunk.index,
                        temperature_adj,
                        speed_adj,
                        repetition_penalty_adj,
                    )
                else:
                    temperature_adj = 0.3
                    speed_adj = 0.7
                    repetition_penalty_adj = 2.8
                    logger.info(
                        "Final retry 4/5 with ultra conservative params | chunk=%s temp=%.2f speed=%.2f rep=%.2f",
                        chunk.index,
                        temperature_adj,
                        speed_adj,
                        repetition_penalty_adj,
                    )

                success = await asyncio.to_thread(
                    engine.generate_audio,
                    text=chunk.text_content,
                    speaker_wav=project.voice_ref_path,
                    output_path=output_path,
                    language=project.language or settings.DEFAULT_LANGUAGE,
                    temperature=temperature_adj,
                    top_p=project.top_p or settings.DEFAULT_TOP_P,
                    repetition_penalty=repetition_penalty_adj,
                    speed=speed_adj,
                )

                if success:
                    # Başarılı chunk için detaylı log
                    if settings.DEBUG_MODE:
                        logger.info(f"✅ Chunk {chunk.index} quality OK | temp={temperature_adj:.2f} speed={speed_adj:.2f}")
                    return True, None, output_path

                if not success:
                    logger.warning(f"⚠️ Quality control failed for chunk {chunk.index} | temp={temperature_adj:.2f} speed={speed_adj:.2f} | Audio discarded by engine")
                    # Retry counter implicitly increases via while loop end, but we can be explicit if needed
                    # as attempt is incremented at the end of the loop.
                    pass

            except torch.cuda.OutOfMemoryError as oom:
                _handle_oom_error()
                chunk_error = f"OOM: {str(oom)}"
            except Exception as e:
                chunk_error = str(e)

            attempt += 1

            if attempt < 5:
                logger.warning("Retry %s/5 for chunk %s", attempt, chunk.index)
                if hasattr(engine, "release_memory"):
                    engine.release_memory()

        # 5 deneme başarısız olduysa chunk'ı atla
        if not success:
            logger.error(
                "❌ Chunk %s failed after 5 attempts, skipping...",
                chunk.index
            )
            return False, f"Failed after 5 retries", None

        # Recursive split fallback (artık kullanılmayacak çünkü 5 deneme yeterli)
        if not success and len(chunk.text_content) > 200:
            logger.warning("All retries failed. Attempting split for chunk %s", chunk.index)
            try:
                processor = TextProcessor()
                split_text = processor._smart_split(chunk.text_content, len(chunk.text_content) // 2 + 50)

                if len(split_text) >= 2:
                    temp_files = []
                    all_parts_success = True

                    for i, part_text in enumerate(split_text):
                        part_output = output_path.replace(".wav", f"_part{i}.wav")
                        temp_files.append(part_output)
                        part_success = False
                        try:
                            part_success = await asyncio.to_thread(
                                engine.generate_audio,
                                text=part_text,
                                speaker_wav=project.voice_ref_path,
                                output_path=part_output,
                                language=project.language or settings.DEFAULT_LANGUAGE,
                                temperature=0.3,
                                top_p=0.8,
                                repetition_penalty=2.5,
                                speed=settings.DEFAULT_SPEED,
                            )
                        except Exception as e:
                            logger.error("Split part %s failed: %s", i, e)

                        if not part_success:
                            all_parts_success = False
                            break

                    if all_parts_success:
                        combined = AudioSegment.empty()
                        for temp_file in temp_files:
                            if os.path.exists(temp_file):
                                combined += AudioSegment.from_wav(temp_file)
                                combined += AudioSegment.silent(duration=50)
                                try:
                                    os.remove(temp_file)
                                except Exception:
                                    pass

                        combined.export(output_path, format="wav")
                        return True, None, output_path
                    else:
                        for temp_file in temp_files:
                            if os.path.exists(temp_file):
                                try:
                                    os.remove(temp_file)
                                except Exception:
                                    pass
            except Exception as e:
                logger.error("Recursive split failed: %s", e)

    return False, chunk_error or "Unknown error", None


async def process_chunks(
    project: Project,
    chunks: List[Chunk],
    use_gpu: bool,
    db,
    engine_provider,
) -> ChunkRunResult:
    """Chunk üretimi akışı; progress ve iptal kontrolüyle."""
    session_failed_chunks: List[int] = []
    last_error_message: str = ""

    total_chunks = len(chunks)
    unprocessed_chunks = [c for c in chunks if not c.is_processed]

    for chunk in unprocessed_chunks:
        db.refresh(project)
        if project.is_cancelled or project.status == "cancelled":
            await manager.broadcast({
                "type": "status_update",
                "project_id": project.id,
                "status": "cancelled",
                "progress": (db.query(Chunk)
                             .filter(Chunk.project_id == project.id,
                                     Chunk.is_processed == True)
                             .count() / max(total_chunks, 1)) * 100,
            })
            project.status = "cancelled"
            db.commit()
            return ChunkRunResult(
                processed_count=db.query(Chunk).filter(Chunk.project_id == project.id, Chunk.is_processed == True).count(),
                total_chunks=total_chunks,
                failed_chunks=session_failed_chunks,
                last_error=last_error_message or None,
                cancelled=True,
            )

        output_path = str(settings.OUTPUT_DIR / str(project.id) / f"chunk_{chunk.index}.wav")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        success, err, path_out = await _process_single_chunk(
            chunk, project, output_path, use_gpu, engine_provider
        )

        if success:
            chunk.is_processed = True
            chunk.chunk_audio_path = path_out
            db.commit()

            processed_count = db.query(Chunk).filter(
                Chunk.project_id == project.id, Chunk.is_processed == True
            ).count()
            progress = (processed_count / total_chunks) * 100

            await manager.broadcast({
                "type": "progress_update",
                "project_id": project.id,
                "chunk_index": chunk.index,
                "chunk_text_preview": (chunk.text_content or "")[:120],
                "progress": progress,
            })
        else:
            session_failed_chunks.append(chunk.index)
            if err:
                last_error_message = f"Chunk {chunk.index}: {err}"

            logger.error(
                "Chunk failed | project=%s chunk=%s error=%s text_len=%s",
                project.id,
                chunk.index,
                err,
                len(chunk.text_content) if chunk.text_content else 0,
            )

            await manager.broadcast({
                "type": "status_update",
                "project_id": project.id,
                "status": "chunk_skipped",
                "chunk_index": chunk.index,
                "chunk_text_preview": (chunk.text_content or "")[:120],
                "message": f"Chunk {chunk.index} skipped: {err}",
            })

        # Periodic memory cleanup
        if chunk.index % 30 == 0:
            engine = engine_provider(use_gpu=use_gpu)
            if hasattr(engine, "release_memory"):
                engine.release_memory()

    processed_count = db.query(Chunk).filter(
        Chunk.project_id == project.id, Chunk.is_processed == True
    ).count()

    return ChunkRunResult(
        processed_count=processed_count,
        total_chunks=total_chunks,
        failed_chunks=session_failed_chunks,
        last_error=last_error_message or None,
        cancelled=False,
    )
