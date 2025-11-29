from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import Project, Chunk
from ..ai.text_processor import TextProcessor
from typing import List, Dict, Any, Optional
import asyncio
import shutil
import os
from pathlib import Path

router = APIRouter()

# Reference voices directory
REFERENCE_VOICES_DIR = Path(__file__).parent.parent.parent / "storage" / "reference_voices"

@router.get("/reference-voices")
async def get_reference_voices() -> Dict[str, Any]:
    """
    Get list of available reference voices grouped by category
    """
    voices: Dict[str, List[Dict[str, str]]] = {}
    
    try:
        if not REFERENCE_VOICES_DIR.exists():
            return {"voices": {}}
            
        for category_dir in REFERENCE_VOICES_DIR.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            
            # Check if category has subdirectories (like male/female)
            subdirs = [d for d in category_dir.iterdir() if d.is_dir()]
            
            if subdirs:
                # Has subdirectories (e.g., adult/male, adult/female)
                for subdir in subdirs:
                    subcategory_name = f"{category_name}/{subdir.name}"
                    voices[subcategory_name] = []
                    
                    for voice_file in subdir.glob("*.wav"):
                        voices[subcategory_name].append({
                            "name": voice_file.stem,
                            "path": str(voice_file.relative_to(REFERENCE_VOICES_DIR)),
                            "filename": voice_file.name
                        })
            else:
                # No subdirectories, wav files directly in category
                voices[category_name] = []
                for voice_file in category_dir.glob("*.wav"):
                    voices[category_name].append({
                        "name": voice_file.stem,
                        "path": str(voice_file.relative_to(REFERENCE_VOICES_DIR)),
                        "filename": voice_file.name
                    })
        
        return {"voices": voices}
    except Exception as e:
        return {"voices": {}, "error": str(e)}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# Global instances
text_processor = TextProcessor()
tts_engine = None

def get_tts_engine(use_gpu: bool = False):
    """Lazy loading için TTS engine getter"""
    global tts_engine
    if tts_engine is None:
        from ..ai.tts_engine import TTSEngine
        tts_engine = TTSEngine(use_gpu=use_gpu)
    return tts_engine

UPLOAD_DIR = os.path.join(os.getcwd(), "storage", "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "storage", "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@router.post("/projects/")
async def create_project(
    name: str = Form(...),
    text_file: UploadFile = File(...),
    voice_file: Optional[UploadFile] = File(None),
    reference_voice_path: Optional[str] = Form(None),
    use_gpu: bool = Form(False),
    # XTTS Parameters
    language: str = Form("en"),
    speed: float = Form(1.0),
    temperature: float = Form(0.75),
    top_k: int = Form(50),
    top_p: float = Form(0.85),
    repetition_penalty: float = Form(2.0),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Yeni proje oluştur ve metni chunk'la"""
    try:
        # 1. Save text file
        text_path = os.path.join(UPLOAD_DIR, f"{name}_{text_file.filename}")
        
        with open(text_path, "wb") as buffer:
            shutil.copyfileobj(text_file.file, buffer)
        
        # 2. Handle voice file (uploaded or reference)
        if voice_file:
            voice_path = os.path.join(UPLOAD_DIR, f"{name}_{voice_file.filename}")
            with open(voice_path, "wb") as buffer:
                shutil.copyfileobj(voice_file.file, buffer)
        elif reference_voice_path:
            voice_path = str(REFERENCE_VOICES_DIR / reference_voice_path)
            if not os.path.exists(voice_path):
                raise HTTPException(status_code=400, detail="Reference voice not found")
        else:
            raise HTTPException(status_code=400, detail="Either voice_file or reference_voice_path must be provided")

        # 3. Create DB record
        project = Project(
            name=name,
            text_path=text_path,
            voice_ref_path=voice_path,
            status="created",
            # XTTS Config
            language=language,
            speed=speed,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # 4. Read and chunk text
        with open(text_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        
        chunks = text_processor.split_into_chunks(full_text)
        
        for i, chunk_text in enumerate(chunks):
            db_chunk = Chunk(
                project_id=project.id,
                index=i,
                text_content=chunk_text,
                is_processed=False
            )
            db.add(db_chunk)
        
        db.commit()

        return {
            "project_id": project.id,
            "total_chunks": len(chunks),
            "message": "Project created and text chunked."
        }
    except Exception as e:
        print(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/process")
async def process_project(
    project_id: int, 
    background_tasks: BackgroundTasks,
    use_gpu: bool = Query(False),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    background_tasks.add_task(process_audio_task, project_id, use_gpu)
    
    return {"message": "Processing started in background."}

async def merge_audio_files(project_id: int, db: Session):
    """
    Merge all chunk audio files into a single MP3 file.
    Deletes individual chunk files after merging to save disk space.
    Sends progress updates via WebSocket.
    """
    from pydub import AudioSegment
    import subprocess
    
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
    
    project_output_dir = os.path.join(OUTPUT_DIR, str(project_id))
    os.makedirs(project_output_dir, exist_ok=True)
    
    # Check if merged file already exists
    output_filename_mp3 = f"{project.name}_final.mp3"
    output_path_mp3 = os.path.join(project_output_dir, output_filename_mp3)
    
    if os.path.exists(output_path_mp3):
        print(f"✓ Merged file already exists for project {project_id}")
        project.audio_path = output_path_mp3
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
            # Add 350ms silence between chunks
            combined += audio + AudioSegment.silent(duration=350)
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
            output_path_mp3, 
            format="mp3",
            bitrate="192k"  # Good quality, reasonable file size
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
    project.audio_path = output_path_mp3
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
            project_output_dir = os.path.join(OUTPUT_DIR, str(project_id))
            os.makedirs(project_output_dir, exist_ok=True)
            
            output_filename = f"chunk_{chunk.index}.wav"
            output_path = os.path.join(project_output_dir, output_filename)
            
            print(f"Processing chunk {chunk.index}/{total_chunks-1}")
            
            try:
                engine = get_tts_engine(use_gpu=use_gpu)
                
                success = await asyncio.to_thread(
                    engine.generate_audio,
                    text=chunk.text_content,
                    speaker_wav=project.voice_ref_path,
                    output_path=output_path,
                    language=project.language or "en",
                    speed=project.speed or 1.0,
                    temperature=project.temperature or 0.75,
                    top_k=project.top_k or 50,
                    top_p=project.top_p or 0.85,
                    repetition_penalty=project.repetition_penalty or 2.0
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
                chunk.chunk_audio_path = output_path
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

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    client_addr = websocket.client
    print(f"🔌 WebSocket connection attempt from {client_addr}")
    
    try:
        # WebSocket'i doğrudan kabul et (403 hatası almamak için)
        await manager.connect(websocket)
        print(f"✓ WebSocket connected: {client_addr}")
        
        while True:
            try:
                # Keep connection alive - timeout ile mesaj bekle
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                print(f"📨 WebSocket message received: {data}")
            except asyncio.TimeoutError:
                # Timeout oluştu ama bağlantı hala açık
                # Heartbeat olarak cevap gönder
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                continue
            except Exception as e:
                print(f"❌ WebSocket receive error: {type(e).__name__}: {e}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket connection error: {type(e).__name__}: {e}")
    finally:
        try:
            manager.disconnect(websocket)
            print(f"✗ WebSocket disconnected: {client_addr}")
        except Exception as e:
            print(f"Error disconnecting: {e}")


@router.get("/projects")
def get_all_projects(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all projects"""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    
    return {
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "audio_path": project.audio_path  # Include audio_path to detect merge status
            }
            for project in projects
        ]
    }

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Delete a project and all its associated data"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Delete audio files from filesystem
        project_output_dir = os.path.join(OUTPUT_DIR, str(project_id))
        if os.path.exists(project_output_dir):
            shutil.rmtree(project_output_dir)
            print(f"✓ Deleted output directory: {project_output_dir}")
        
        # Delete uploaded files
        if project.text_path and os.path.exists(project.text_path):
            os.remove(project.text_path)
        
        # Delete chunks (cascade should handle this, but being explicit)
        db.query(Chunk).filter(Chunk.project_id == project_id).delete()
        
        # Delete project
        db.delete(project)
        db.commit()
        
        return {"message": f"Project {project_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@router.get("/projects/{project_id}")
def get_project_status(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()
    processed_count = sum(1 for c in chunks if c.is_processed)
    
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "total_chunks": len(chunks),
        "processed_chunks": processed_count,
        "progress": (processed_count / len(chunks)) * 100 if chunks else 0
    }

@router.get("/projects/{project_id}/chunks")
def get_project_chunks(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all chunks with their audio paths"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chunks = db.query(Chunk).filter(Chunk.project_id == project_id).order_by(Chunk.index).all()
    
    return {
        "project_id": project_id,
        "chunks": [
            {
                "index": chunk.index,
                "text": chunk.text_content,
                "is_processed": chunk.is_processed,
                "audio_path": chunk.chunk_audio_path if chunk.is_processed else None
            }
            for chunk in chunks
        ]
    }

@router.get("/audio/chunk/{project_id}/{chunk_index}")
async def serve_chunk_audio(project_id: int, chunk_index: int, db: Session = Depends(get_db)):
    """Serve individual chunk audio file"""
    chunk = db.query(Chunk).filter(
        Chunk.project_id == project_id,
        Chunk.index == chunk_index
    ).first()
    
    if not chunk or not chunk.is_processed or not chunk.chunk_audio_path:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    if not os.path.exists(chunk.chunk_audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    return FileResponse(
        chunk.chunk_audio_path,
        media_type="audio/wav",
        filename=f"chunk_{chunk_index}.wav"
    )

@router.get("/audio/download/{project_id}")
async def download_merged_audio(project_id: int, db: Session = Depends(get_db)):
    """Download merged final audio (MP3 format)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chunks = db.query(Chunk).filter(
        Chunk.project_id == project_id,
        Chunk.is_processed == True
    ).order_by(Chunk.index).all()
    
    if not chunks:
        raise HTTPException(status_code=404, detail="No processed chunks found")
    
    project_output_dir = os.path.join(OUTPUT_DIR, str(project_id))
    output_filename = f"{project.name}_final.mp3"
    output_path = os.path.join(project_output_dir, output_filename)
    
    # Check if merged file already exists (from automatic merge)
    if project.audio_path and os.path.exists(project.audio_path):
        output_path = project.audio_path
        output_filename = os.path.basename(output_path)
        print(f"✓ Using existing merged file: {output_path}")
    else:
        # Fallback: merge on-demand if file doesn't exist
        print(f"⚠ Merged file not found, merging on-demand...")
        await merge_audio_files(project_id, db)
        db.refresh(project)
        
        if project.audio_path and os.path.exists(project.audio_path):
            output_path = project.audio_path
            output_filename = os.path.basename(output_path)
        else:
            raise HTTPException(status_code=500, detail="Failed to create merged audio file")
    
    # Use StreamingResponse for faster downloads (larger chunks)
    def iterfile():
        with open(output_path, mode="rb") as file_like:
            while chunk := file_like.read(4 * 1024 * 1024):  # 4MB chunks (increased from 1MB)
                yield chunk
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={output_filename}",
            "Content-Length": str(os.path.getsize(output_path))
        }
    )

