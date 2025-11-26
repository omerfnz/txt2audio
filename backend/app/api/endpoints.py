from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
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
            status="created"
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
                
            output_filename = f"proj_{project_id}_chunk_{chunk.index}.wav"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            print(f"Processing chunk {chunk.index}/{total_chunks-1}")
            
            try:
                engine = get_tts_engine(use_gpu=use_gpu)
                
                success = await asyncio.to_thread(
                    engine.generate_audio,
                    text=chunk.text_content,
                    speaker_wav=project.voice_ref_path,
                    output_path=output_path
                )
            except RuntimeError as e:
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

                # Daha sık memory cleanup (her 3 chunk'ta bir - düşük VRAM için)
                if chunk.index % 3 == 0 and chunk.index > 0:
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
