import json
import asyncio
import subprocess
from pathlib import Path
from typing import List
import logging
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

        from datetime import datetime
        if project.started_at is None:
            project.started_at = datetime.utcnow()
            
        project.status = "processing"
        project.is_cancelled = False
        db.commit()

        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "processing",
            "progress": initial_progress
        })

        if settings.DEBUG_MODE:
            logger.info(f"🔍 DEBUG MODE: Processing {len(chunks)} chunks for project {project_id}")

        run_result = await process_chunks(
            project=project,
            chunks=chunks,
            use_gpu=use_gpu,
            db=db,
            engine_provider=get_tts_engine,
        )

        if settings.DEBUG_MODE:
            logger.info(f"🔍 DEBUG MODE: Processing completed | Processed: {run_result.processed_count} | "
                       f"Failed: {len(run_result.failed_chunks)} | Total: {run_result.total_chunks}")

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

        # Background music mixing (mastering'den ÖNCE)
        mixed_path = await mix_background_music(
            voice_mp3_path=merged_path,
            bg_music_file=project.bg_music_file if project.bg_music_enabled else "",
            volume=project.bg_music_volume if project.bg_music_volume is not None else settings.DEFAULT_BG_MUSIC_VOLUME,
        )

        # ACX Mastering (background music mixing'den SONRA)
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "mastering",
            "progress": 99.9
        })

        from .audio_mastering import AudioMastering
        from .audio_analyzer import AudioAnalyzer

        analyzer = AudioAnalyzer()
        mastering = AudioMastering()

        # Pre-mastering analizi
        logger.info("🔍 Pre-mastering ACX analysis for project %s", project_id)
        try:
            pre_analysis = analyzer.analyze(str(mixed_path))
            logger.info("📊 Pre-mastering ACX results | RMS: %.2f dB | Peak: %.2f dB | ACX Compliant: %s",
                       pre_analysis['rms_db'], pre_analysis['peak_db'], pre_analysis['acx_compliant'])

            if not pre_analysis['acx_compliant']:
                logger.warning("⚠️ Pre-mastering: Audio not ACX compliant - applying mastering")
            else:
                logger.info("✅ Pre-mastering: Audio already ACX compliant")
        except Exception as e:
            logger.warning("⚠️ Pre-mastering analysis failed: %s", e)
            pre_analysis = None

        # Mastering uygula
        mastered_output = Path(mixed_path).with_name(f"{Path(mixed_path).stem}_mastered{Path(mixed_path).suffix}")
        logger.info("🎛️ Applying ACX audio mastering for project %s", project_id)
        
        success = await asyncio.to_thread(
            mastering.normalize_for_acx,
            str(mixed_path),
            str(mastered_output)
        )

        if success:
            # Post-mastering analizi
            logger.info("✅ Audio mastering completed, analyzing results...")
            try:
                post_analysis = analyzer.analyze(str(mastered_output))
                logger.info("📊 Post-mastering ACX results | RMS: %.2f dB | Peak: %.2f dB | ACX Compliant: %s",
                           post_analysis['rms_db'], post_analysis['peak_db'], post_analysis['acx_compliant'])

                if post_analysis['acx_compliant']:
                    logger.info("🎉 SUCCESS: Audio now ACX compliant after mastering!")
                else:
                    logger.warning("⚠️ WARNING: Audio still not ACX compliant after mastering")

                if pre_analysis:
                    rms_improvement = post_analysis['rms_db'] - pre_analysis['rms_db']
                    peak_improvement = post_analysis['peak_db'] - pre_analysis['peak_db']
                    logger.info("📈 Mastering improvements | RMS change: %.2f dB | Peak change: %.2f dB",
                               rms_improvement, peak_improvement)
            except Exception as e:
                logger.warning("⚠️ Post-mastering analysis failed: %s", e)

            # Mastering başarılı, orijinal dosyayı değiştir
            import shutil
            shutil.move(str(mastered_output), str(mixed_path))
            logger.info("✅ Final: Audio mastering workflow completed for project %s", project_id)
            final_path = mixed_path
        else:
            logger.error("❌ Audio mastering failed for project %s, keeping mixed audio", project_id)
            if mastered_output.exists():
                try:
                    mastered_output.unlink()
                except Exception:
                    pass
            final_path = mixed_path

        project.audio_path = str(final_path)
        project.status = "completed"
        project.completed_at = datetime.utcnow()
        db.commit()
        
        # Calculate chapter timestamps after merge (non-blocking)
        try:
            from .chapter_service import ChapterService
            chapter_service = ChapterService()
            timestamps = chapter_service.calculate_chapter_timestamps(project_id, db)
            if timestamps:
                logger.info(f"✅ Calculated timestamps for {len(timestamps)} chapters in project {project_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate chapter timestamps: {e}")
            # Non-critical, continue

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
            project.completed_at = datetime.utcnow()
            db.commit()
            await manager.broadcast({
                "type": "status_update",
                "project_id": project_id,
                "status": "failed",
                "error": error_msg
            })
    finally:
        db.close()
