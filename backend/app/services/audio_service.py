import os
import json
import asyncio
import subprocess
from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from ..db.models import Project, Chunk
from ..core.config import settings
from .websocket import manager
from .chunk_runner import process_chunks
from .merge_concat import merge_project_audio
from .background_music import mix_background_music

logger = logging.getLogger("ai_audiobook_studio")

# Global instance for model management
active_engine = None

def get_tts_engine(use_gpu: bool = False):
    """
    Model Factory with VRAM management for XTTS.
    Ensures only one heavy model is loaded at a time.
    """
    global active_engine
    
    # If already active, return it
    if active_engine is not None:
        return active_engine
        
    from ..ai.tts_engine import TTSEngine
    active_engine = TTSEngine(use_gpu=use_gpu)
    return active_engine
async def process_audio_task(project_id: int, use_gpu: bool = False):
    """
    Chunk üretimi, merge ve opsiyonel BG müzik miks akışı.
    """
    from ..db.session import SessionLocal
    db = SessionLocal()

    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("Project %s not found", project_id)
            return

        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).order_by(Chunk.index).all()
        total_chunks = len(chunks)

        existing_failed: List[int] = []
        if project.failed_chunks:
            try:
                existing_failed = json.loads(project.failed_chunks)
            except json.JSONDecodeError:
                existing_failed = []

        already_processed = sum(1 for c in chunks if c.is_processed)
        initial_progress = (already_processed / total_chunks) * 100 if total_chunks > 0 else 0

        project.status = "processing"
        project.is_cancelled = False
        db.commit()

        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "processing",
            "progress": initial_progress
        })

        run_result = await process_chunks(
            project=project,
            chunks=chunks,
            use_gpu=use_gpu,
            db=db,
            engine_provider=get_tts_engine,
        )

        if run_result.cancelled:
            return

        all_failed = sorted(set(existing_failed + run_result.failed_chunks))
        project.failed_chunks = json.dumps(all_failed) if all_failed else None
        project.last_error = run_result.last_error

        # FFmpeg availability
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg not found, skipping merge")
            project.status = "failed"
            db.commit()
            await manager.broadcast({
                "type": "status_update",
                "project_id": project_id,
                "status": "failed",
                "error": "ffmpeg not available"
            })
            return

        project_output_dir = settings.OUTPUT_DIR / str(project_id)
        project_output_dir.mkdir(exist_ok=True)

        project.status = "merging"
        db.commit()
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "merging",
            "progress": 99.0
        })

        merged_path = await merge_project_audio(
            project=project,
            chunks=chunks,
            project_output_dir=project_output_dir,
        )
        db.commit()

        final_path = await mix_background_music(
            voice_mp3_path=merged_path,
            bg_music_file=project.bg_music_file if project.bg_music_enabled else "",
            volume=project.bg_music_volume or settings.DEFAULT_BG_MUSIC_VOLUME,
        )

        project.audio_path = str(final_path)
        project.status = "completed"
        db.commit()

        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "completed",
            "progress": 100,
            "failed_chunks": all_failed if all_failed else None
        })

    except Exception as e:
        error_msg = str(e)
        logger.error("Error processing project %s: %s", project_id, error_msg)
        if 'project' in locals() and project:
            project.status = "failed"
            project.last_error = error_msg
            db.commit()
            await manager.broadcast({
                "type": "status_update",
                "project_id": project_id,
                "status": "failed",
                "error": error_msg
            })
    finally:
        db.close()
