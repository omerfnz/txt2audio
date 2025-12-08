import os
import json
import asyncio
import subprocess
import torch
from typing import List, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from pydub import AudioSegment
from ..db.models import Project, Chunk
from ..core.config import settings
from .websocket import manager

# Retry configuration
MAX_CHUNK_RETRIES = 3  # 3 kez deneme, başarısız olursa atla

# Failed chunks debug log file
FAILED_CHUNKS_LOG = "failed_chunks_log.txt"

# Global instances for model management
active_engine = None
active_model_type = None  # "xtts" or "f5"
gpu_lock = asyncio.Lock()

@dataclass
class ChunkResult:
    """Result of processing a single chunk."""
    chunk_index: int
    success: bool
    error: Optional[str] = None
    output_path: Optional[str] = None

def unload_active_model():
    """Unloads currently active model to free VRAM."""
    global active_engine, active_model_type
    
    if active_engine:
        if hasattr(active_engine, "unload_model"):
            active_engine.unload_model()
        elif hasattr(active_engine, "release_memory"):
            # XTTS Engine cleanup
            active_engine.release_memory()
        # Force garbage collection
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            # TTSEngine doesn't have explicit unload, so we force cleanup
            # Ideally TTSEngine should have an unload method, but for now we rely on gc
            pass
            
        print(f"🧹 Unloaded model: {active_model_type}")
        active_engine = None
        active_model_type = None
        torch.cuda.empty_cache()
        import gc
        gc.collect()

def get_tts_engine(use_gpu: bool = False, model_type: str = "xtts"):
    """
    Model Factory with VRAM management.
    Ensures only one heavy model is loaded at a time.
    """
    global active_engine, active_model_type
    
    # If requested model is already active, return it
    if active_engine is not None and active_model_type == model_type:
        return active_engine
        
    # If another model is active, unload it first
    if active_engine is not None:
        print(f"🔄 Switching model from {active_model_type} to {model_type}...")
        unload_active_model()
        
    # Load requested model
    if model_type == "xtts":
        from ..ai.tts_engine import TTSEngine
        active_engine = TTSEngine(use_gpu=use_gpu)
        active_model_type = "xtts"
    elif model_type == "f5":
        from ..ai.f5_engine import F5TTSEngine
        active_engine = F5TTSEngine()
        # F5 engine loads model explicitly via load_model() usually, 
        # but let's ensure it's ready if needed here or let caller handle load
        if not active_engine.is_loaded:
            active_engine.load_model()
        active_model_type = "f5"
        
    return active_engine


async def _process_single_chunk(
    chunk: Chunk,
    project: Project,
    output_path: str,
    use_gpu: bool
) -> ChunkResult:
    """
    Process a single chunk with retry logic.
    
    Args:
        chunk: Chunk to process
        project: Parent project
        output_path: Output file path
        use_gpu: Whether to use GPU
        
    Returns:
        ChunkResult with success status and any error
    """
    # Determine which model to use from project settings
    # Default to 'xtts' if not specified (backward compatibility)
    model_type = getattr(project, "tts_model", "xtts") or "xtts"
    
    engine = get_tts_engine(use_gpu=use_gpu, model_type=model_type)
    
    # Serialize GPU access
    async with gpu_lock:
        attempt = 0
        success = False
        chunk_error = ""
        
        while attempt < MAX_CHUNK_RETRIES and not success:
            try:
                # Adaptive parameters for each retry attempt
                base_temp = project.temperature or settings.DEFAULT_TEMPERATURE
                base_speed = project.speed or settings.DEFAULT_SPEED
                base_rep_penalty = project.repetition_penalty or settings.DEFAULT_REPETITION_PENALTY
                
                if attempt == 0:
                    # First attempt: Use normal parameters
                    temperature_adj = base_temp
                    speed_adj = base_speed
                    repetition_penalty_adj = base_rep_penalty
                elif attempt == 1:
                    # Second attempt: More conservative (slower, lower temperature)
                    temperature_adj = max(0.35, base_temp * 0.7)
                    speed_adj = base_speed * 0.85  # 15% slower
                    repetition_penalty_adj = min(3.0, base_rep_penalty * 1.2)
                    print(f"  🔧 Retry with adjusted params: temp={temperature_adj:.2f}, speed={speed_adj:.2f}, rep_pen={repetition_penalty_adj:.2f}")
                else:
                    # Third attempt: Very conservative (safest settings)
                    temperature_adj = 0.3
                    speed_adj = 0.7
                    repetition_penalty_adj = 2.8
                    print(f"  🔧 Final retry with conservative params: temp={temperature_adj:.2f}, speed={speed_adj:.2f}, rep_pen={repetition_penalty_adj:.2f}")
                
                if model_type == "f5":
                    # F5-TTS Call
                    success = await asyncio.to_thread(
                        engine.generate_audio_file,
                        text=chunk.text_content,
                        ref_audio=project.voice_ref_path,
                        output_path=output_path,
                        speed=speed_adj
                    )
                else:
                    # XTTS Call with adaptive parameters
                    success = await asyncio.to_thread(
                        engine.generate_audio,
                        text=chunk.text_content,
                        speaker_wav=project.voice_ref_path,
                        output_path=output_path,
                        language=project.language or settings.DEFAULT_LANGUAGE,
                        temperature=temperature_adj,
                        top_p=project.top_p or settings.DEFAULT_TOP_P,
                        repetition_penalty=repetition_penalty_adj,
                        speed=speed_adj
                    )
                
                if success:
                    if attempt > 0:
                        print(f"  ✅ Chunk {chunk.index} succeeded on attempt {attempt + 1}")
                    return ChunkResult(
                        chunk_index=chunk.index,
                        success=True,
                        output_path=output_path
                    )
                    
            except torch.cuda.OutOfMemoryError as oom:
                _handle_oom_error()
                chunk_error = f"OOM: {str(oom)}"
                # OOM sonrası retry şansı ver
                
            except Exception as e:
                chunk_error = str(e)
                
            attempt += 1
            
            if attempt < MAX_CHUNK_RETRIES:
                print(f"  🔁 Retry {attempt}/{MAX_CHUNK_RETRIES} for chunk {chunk.index}")
                # Memory cleanup between retries
                engine.release_memory()
        
    return ChunkResult(
        chunk_index=chunk.index,
        success=False,
        error=chunk_error or "Unknown error"
    )

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
            
            # Add silence between chunks based on text content
            silence_duration = settings.CHUNK_SILENCE_DURATION
            if chunk.text_content:
                text = chunk.text_content.strip()
                # If chunk does not end with sentence terminator, reduce silence
                if text and not any(text.endswith(end) for end in ['.', '!', '?', '"', "'", '”', '’']):
                    if text.endswith((',', ';', ':')):
                        silence_duration = 150  # Short pause for sub-clauses
                    else:
                        silence_duration = 20   # Very short pause for split sentences (just to avoid clicks)
            
            combined += audio + AudioSegment.silent(duration=silence_duration)
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
    """
    Process all unprocessed chunks for a project.
    
    Features:
    - Skips already processed chunks (supports resume)
    - Retries failed chunks up to MAX_CHUNK_RETRIES times
    - Tracks permanently failed chunks in project.failed_chunks
    - Updates progress from where it left off
    - Concurrent processing support (configurable)
    """
    from ..db.session import SessionLocal
    db = SessionLocal()
    
    # Track failed chunks during this processing session
    session_failed_chunks: List[int] = []
    last_error_message: str = ""
    
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"Project {project_id} not found")
            return

        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).order_by(Chunk.index).all()
        total_chunks = len(chunks)
        
        # Load existing failed chunks (from previous attempts)
        existing_failed: List[int] = []
        if project.failed_chunks:
            try:
                existing_failed = json.loads(project.failed_chunks)
            except json.JSONDecodeError:
                existing_failed = []

        # Calculate initial progress (for resume support)
        already_processed = sum(1 for c in chunks if c.is_processed)
        initial_progress = (already_processed / total_chunks) * 100 if total_chunks > 0 else 0

        print(f"Processing project {project_id}: {total_chunks} chunks, use_gpu={use_gpu}")
        print(f"  Already processed: {already_processed}/{total_chunks} ({initial_progress:.1f}%)")
        if existing_failed:
            print(f"  Previously failed chunks: {existing_failed}")

        # Status ve cancellation bayrağı güncelle
        project.status = "processing"
        project.is_cancelled = False
        db.commit()

        # Broadcast with initial progress (resume support)
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "processing",
            "progress": initial_progress
        })

        # Get unprocessed chunks
        unprocessed_chunks = [c for c in chunks if not c.is_processed]
        
        # Create project output directory
        project_output_dir = settings.OUTPUT_DIR / str(project_id)
        project_output_dir.mkdir(exist_ok=True)
        
        # Process chunks sequentially (XTTS v2 is not thread-safe)
        for chunk in unprocessed_chunks:
            # Check cancellation
            db.refresh(project)
            if project.is_cancelled or project.status == "cancelled":
                print(f"Project {project_id} cancelled. Stopping processing.")
                await manager.broadcast({
                    "type": "status_update",
                    "project_id": project_id,
                    "status": "cancelled",
                    "progress": (db.query(Chunk)
                                 .filter(Chunk.project_id == project_id,
                                         Chunk.is_processed == True)
                                 .count() / max(total_chunks, 1)) * 100,
                })
                project.status = "cancelled"
                db.commit()
                return
            
            output_path = str(project_output_dir / f"chunk_{chunk.index}.wav")
            print(f"  Processing chunk {chunk.index}/{total_chunks-1}")
            
            # Process single chunk
            result = await _process_single_chunk(chunk, project, output_path, use_gpu)
            
            if result.success:
                # Update chunk in database
                chunk.is_processed = True
                chunk.chunk_audio_path = result.output_path
                db.commit()
                
                # Calculate and broadcast progress
                processed_count = db.query(Chunk).filter(
                    Chunk.project_id == project_id,
                    Chunk.is_processed == True
                ).count()
                progress = (processed_count / total_chunks) * 100
                
                # HER CHUNK için WebSocket mesajı gönder
                await manager.broadcast({
                    "type": "progress_update",
                    "project_id": project_id,
                    "chunk_index": chunk.index,
                    "chunk_text_preview": (chunk.text_content or "")[:120],
                    "progress": progress,
                })
            else:
                # Track failed chunk
                session_failed_chunks.append(chunk.index)
                if result.error:
                    last_error_message = f"Chunk {chunk.index}: {result.error}"
                
                # Debug logging for failed chunks
                print(f"❌ FAILED CHUNK #{chunk.index}")
                print(f"   Text length: {len(chunk.text_content)} chars")
                print(f"   Text preview: {chunk.text_content[:200]}...")
                print(f"   Error: {result.error}")
                
                # Save failed chunk to log file for analysis
                try:
                    import os
                    log_path = os.path.join(os.getcwd(), FAILED_CHUNKS_LOG)
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"Chunk #{chunk.index} - Project {project_id}\n")
                        f.write(f"Text length: {len(chunk.text_content)} chars\n")
                        f.write(f"Text: {chunk.text_content}\n")
                        f.write(f"Error: {result.error}\n")
                except Exception as log_error:
                    print(f"⚠ Could not write to log file: {log_error}")
                
                await manager.broadcast({
                    "type": "status_update",
                    "project_id": project_id,
                    "status": "chunk_skipped",
                    "chunk_index": chunk.index,
                    "chunk_text_preview": (chunk.text_content or "")[:120],
                    "message": f"Chunk {chunk.index} skipped: {result.error}"
                })
            
            # Memory cleanup periodically
            # T4 has 16GB VRAM, frequent cleanup hurts performance (sync overhead)
            # Optimized to 30 for better stability vs performance balance
            if chunk.index % 30 == 0:
                # Re-fetch engine with correct type to call release/unload
                model_type = getattr(project, "tts_model", "xtts") or "xtts"
                engine = get_tts_engine(use_gpu=use_gpu, model_type=model_type)
                
                if hasattr(engine, "release_memory"):
                    engine.release_memory()
                elif hasattr(engine, "_log_gpu_memory"):
                     # F5 engine has no release_memory per chunk but we can log
                     engine._log_gpu_memory("Periodic Check")
        
        # Eğer iptal edilmediyse normal tamamlanma ve merge
        db.refresh(project)
        if not project.is_cancelled and project.status != "cancelled":
            # Update failed chunks list (combine existing + new)
            all_failed = list(set(existing_failed + session_failed_chunks))
            if all_failed:
                project.failed_chunks = json.dumps(sorted(all_failed))
                print(f"⚠ Project {project_id} completed with {len(all_failed)} failed chunks: {all_failed}")
            else:
                project.failed_chunks = None
            
            # Update last error if any
            if last_error_message:
                project.last_error = last_error_message
            else:
                project.last_error = None
            
            project.status = "completed"
            db.commit()

            # Calculate final progress (may be <100% if chunks failed)
            processed_count = db.query(Chunk).filter(
                Chunk.project_id == project_id,
                Chunk.is_processed == True
            ).count()
            final_progress = (processed_count / total_chunks) * 100 if total_chunks > 0 else 100

            await manager.broadcast({
                "type": "status_update",
                "project_id": project_id,
                "status": "completed",
                "progress": final_progress,
                "failed_chunks": all_failed if all_failed else None
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
        error_msg = str(e)
        print(f"Error processing project {project_id}: {error_msg}")
        
        # Save error and failed chunks info
        project.status = "failed"
        project.last_error = error_msg
        
        # Save any failed chunks from this session
        all_failed = list(set(existing_failed + session_failed_chunks))
        if all_failed:
            project.failed_chunks = json.dumps(sorted(all_failed))
        
        db.commit()
        
        await manager.broadcast({
            "type": "status_update",
            "project_id": project_id,
            "status": "failed",
            "error": error_msg,
            "failed_chunks": all_failed if all_failed else None
        })
    finally:
        db.close()
