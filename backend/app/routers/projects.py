from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import Project, Chunk
from ..ai.text_processor import TextProcessor
from ..core.config import settings
from ..services.audio_service import process_audio_task
from typing import List, Dict, Any, Optional
import shutil
import os

router = APIRouter()
text_processor = TextProcessor()

@router.get("/reference-voices")
async def get_reference_voices() -> Dict[str, Any]:
    """
    Get list of available reference voices grouped by category
    """
    voices: Dict[str, List[Dict[str, str]]] = {}
    
    try:
        if not settings.REFERENCE_VOICES_DIR.exists():
            return {"voices": {}}
            
        for category_dir in settings.REFERENCE_VOICES_DIR.iterdir():
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
                            "path": str(voice_file.relative_to(settings.REFERENCE_VOICES_DIR)),
                            "filename": voice_file.name
                        })
            else:
                # No subdirectories, wav files directly in category
                voices[category_name] = []
                for voice_file in category_dir.glob("*.wav"):
                    voices[category_name].append({
                        "name": voice_file.stem,
                        "path": str(voice_file.relative_to(settings.REFERENCE_VOICES_DIR)),
                        "filename": voice_file.name
                    })
        
        return {"voices": voices}
    except Exception as e:
        return {"voices": {}, "error": str(e)}

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
        text_path = settings.UPLOAD_DIR / f"{name}_{text_file.filename}"
        
        with open(text_path, "wb") as buffer:
            shutil.copyfileobj(text_file.file, buffer)
        
        # 2. Handle voice file (uploaded or reference)
        if voice_file:
            voice_path = settings.UPLOAD_DIR / f"{name}_{voice_file.filename}"
            with open(voice_path, "wb") as buffer:
                shutil.copyfileobj(voice_file.file, buffer)
            voice_path = str(voice_path)
        elif reference_voice_path:
            voice_path = settings.REFERENCE_VOICES_DIR / reference_voice_path
            if not voice_path.exists():
                raise HTTPException(status_code=400, detail="Reference voice not found")
            voice_path = str(voice_path)
        else:
            raise HTTPException(status_code=400, detail="Either voice_file or reference_voice_path must be provided")

        # Convert text_path to string for DB
        text_path = str(text_path)

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
        project_output_dir = settings.OUTPUT_DIR / str(project_id)
        if project_output_dir.exists():
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
