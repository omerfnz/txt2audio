import os
import asyncio
import subprocess
from sqlalchemy.orm import Session
from pydub import AudioSegment
from ..db.models import Project, Chunk
from ..core.config import settings
from .websocket import manager

# Global instance for lazy loading
tts_engine = None

def get_tts_engine(use_gpu: bool = False):
    """Lazy loading for TTS engine"""
    global tts_engine
    if tts_engine is None:
        from ..ai.tts_engine import TTSEngine
        tts_engine = TTSEngine(use_gpu=use_gpu)
    return tts_engine

async def merge_audio_files(project_id: int, db: Session):
    """
    Merge all chunk audio files into a single MP3 file.
    Deletes individual chunk files after merging to save disk space.
    Sends progress updates via WebSocket.
    """
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ ffmpeg not found, skipping merge")
        return
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return
    
    chunks = db.query(Chunk).filter(
        Chunk.project_id == project_id,
        Chunk.is_processed == True
    ).order_by(Chunk.index).all()
    
    if not chunks:
        return
    
    project_output_dir = settings.OUTPUT_DIR / str(project_id)
    project_output_dir.mkdir(exist_ok=True)
    
    # Check if merged file already exists
    output_filename_mp3 = f"{project.name}_final.mp3"
    output_path_mp3 = project_output_dir / output_filename_mp3
    
    if output_path_mp3.exists():
        print(f"✓ Merged file already exists for project {project_id}")
        project.audio_path = str(output_path_mp3)
        db.commit()
        return
    
    # Update status to merging
    project.status = "merging"
    db.commit()
    
    # Broadcast merging status
    await manager.broadcast({
        "type": "status_update",
        "project_id": project_id,
        "status": "merging",
        "progress": 99.0  # Start at 99% (processing was 100%)
    })
    
    print(f"🔄 Merging {len(chunks)} chunks for project {project_id}...")
    
    # Merge audio files
    combined = AudioSegment.empty()
    chunk_files_to_delete = []
    
    # Phase 1: Load and combine chunks (99% to 99.5% of total progress)
    valid_chunks = [chunk for chunk in chunks if chunk.chunk_audio_path and os.path.exists(chunk.chunk_audio_path)]
    total_valid = len(valid_chunks)
    
    for idx, chunk in enumerate(valid_chunks):
        try:
            audio = AudioSegment.from_wav(chunk.chunk_audio_path)
            # Add silence between chunks
            combined += audio + AudioSegment.silent(duration=settings.CHUNK_SILENCE_DURATION)
            chunk_files_to_delete.append(chunk.chunk_audio_path)
            
            # Update progress: 99% + (idx/total_valid * 0.5) = 99% to 99.5%
            if total_valid > 0:
                merge_progress = 99.0 + (idx / total_valid) * 0.5
                await manager.broadcast({
                    "type": "progress_update",
                    "project_id": project_id,
                    "progress": merge_progress
                })
        except Exception as e:
            print(f"⚠ Warning: Could not load chunk {chunk.index}: {e}")
            continue
    
    if len(combined) == 0:
        print(f"⚠ No valid audio chunks found to merge for project {project_id}")
        project.status = "completed"
        db.commit()
        return
    
    # Phase 2: Export as MP3 (99.5% to 99.8% of total progress)
    await manager.broadcast({
        "type": "progress_update",
        "project_id": project_id,
        "progress": 99.5
    })
    
    try:
        print(f"💾 Exporting merged audio as MP3...")
        combined.export(
            str(output_path_mp3), 
            format=settings.EXPORT_FORMAT,
            bitrate=settings.EXPORT_BITRATE
        )
        print(f"✓ Merged audio saved: {output_path_mp3}")
        
        await manager.broadcast({
            "type": "progress_update",
            "project_id": project_id,
            "progress": 99.8
        })
    except Exception as e:
        print(f"❌ Error exporting merged audio: {e}")
        project.status = "failed"
        db.commit()
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "failed",
            "error": str(e)
        })
        return
    
    # Phase 3: Delete chunk files (99.8% to 100% of total progress)
    deleted_count = 0
    total_to_delete = len(chunk_files_to_delete)
    for idx, chunk_file in enumerate(chunk_files_to_delete):
        try:
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
                deleted_count += 1
                
                # Update progress: 99.8% + (idx/total_to_delete * 0.2) = 99.8% to 100%
                if total_to_delete > 0:
                    delete_progress = 99.8 + (idx / total_to_delete) * 0.2
                    await manager.broadcast({
                        "type": "progress_update",
                        "project_id": project_id,
                        "progress": delete_progress
                    })
        except Exception as e:
            print(f"⚠ Could not delete chunk file {chunk_file}: {e}")
    
    print(f"🗑️ Deleted {deleted_count} chunk files")
    
    # Update project with merged file path
    project.audio_path = str(output_path_mp3)
    project.status = "completed"
    db.commit()
    
    # Clear chunk_audio_path in database (files are deleted)
    for chunk in chunks:
        chunk.chunk_audio_path = None
    db.commit()
    
    # Broadcast completion
    await manager.broadcast({
        "type": "status_update",
        "project_id": project_id,
        "status": "completed",
        "progress": 100
    })
    
    print(f"✅ Merge completed for project {project_id}")

async def process_audio_task(project_id: int, use_gpu: bool = False):
    from ..db.session import SessionLocal
    db = SessionLocal()
    
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"Project {project_id} not found")
            return
            
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).order_by(Chunk.index).all()
        total_chunks = len(chunks)
        
        print(f"Processing project {project_id}: {total_chunks} chunks, use_gpu={use_gpu}")
        
        project.status = "processing"
        db.commit()
        
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "processing",
            "progress": 0
        })

        for chunk in chunks:
            if chunk.is_processed:
                continue
                
            # Create project-specific output directory
            project_output_dir = settings.OUTPUT_DIR / str(project_id)
            project_output_dir.mkdir(exist_ok=True)
            
            output_filename = f"chunk_{chunk.index}.wav"
            output_path = project_output_dir / output_filename
            
            print(f"Processing chunk {chunk.index}/{total_chunks-1}")
            
            try:
                engine = get_tts_engine(use_gpu=use_gpu)
                
                success = await asyncio.to_thread(
                    engine.generate_audio,
                    text=chunk.text_content,
                    speaker_wav=project.voice_ref_path,
                    output_path=str(output_path),
                    language=project.language or settings.DEFAULT_LANGUAGE,
                    speed=project.speed or settings.DEFAULT_SPEED,
                    temperature=project.temperature or settings.DEFAULT_TEMPERATURE,
                    top_k=project.top_k or settings.DEFAULT_TOP_K,
                    top_p=project.top_p or settings.DEFAULT_TOP_P,
                    repetition_penalty=project.repetition_penalty or settings.DEFAULT_REPETITION_PENALTY
                )
            except RuntimeError as e:
                error_msg = str(e)
                if "CUDA" in error_msg or "device-side assert" in error_msg:
                    print(f"❌ CUDA Error on chunk {chunk.index}: {e}")
                    print("🔄 Attempting to recover: clearing GPU and reloading model...")
                    
                    # Force cleanup
                    engine.release_memory()
                    del engine
                    import gc
                    gc.collect()
                    
                    # Reload model
                    try:
                        engine = get_tts_engine(use_gpu=use_gpu)
                        print("✓ Model reloaded successfully")
                        success = False  # Skip this chunk for now
                    except Exception as reload_error:
                        print(f"❌ Failed to reload model: {reload_error}")
                        raise  # Critical failure
                else:
                    print(f"Critical error: {e}")
                    raise
            except Exception as e:
                print(f"Error processing chunk {chunk.index}: {e}")
                success = False
            
            if success:
                chunk.is_processed = True
                chunk.chunk_audio_path = str(output_path)
                db.commit()
                
                processed_count = db.query(Chunk).filter(
                    Chunk.project_id == project_id, 
                    Chunk.is_processed == True
                ).count()
                progress = (processed_count / total_chunks) * 100
                
                await manager.broadcast({
                    "type": "progress_update",
                    "project_id": project_id,
                    "chunk_index": chunk.index,
                    "progress": progress
                })

                # Aggressive memory cleanup AFTER EVERY CHUNK (for large projects)
                engine.release_memory()
            else:
                print(f"Failed to process chunk {chunk.index}")
        
        project.status = "completed"
        db.commit()
        
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "completed",
            "progress": 100
        })
        
        # Automatically merge audio files after processing completes
        print(f"🔄 Starting automatic merge for project {project_id}...")
        try:
            await merge_audio_files(project_id, db)
            print(f"✓ Merge completed for project {project_id}")
        except Exception as merge_error:
            print(f"⚠ Merge failed for project {project_id}: {merge_error}")
            # Don't fail the whole process if merge fails
        
    except Exception as e:
        print(f"Error processing project {project_id}: {e}")
        project.status = "failed"
        db.commit()
        
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "failed",
            "error": str(e)
        })
    finally:
        db.close()
