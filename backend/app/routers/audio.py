from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import Project, Chunk
from ..core.config import settings
from ..services.audio_service import merge_audio_files
import os

router = APIRouter()

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
    
    project_output_dir = settings.OUTPUT_DIR / str(project_id)
    output_filename = f"{project.name}_final.mp3"
    output_path = project_output_dir / output_filename
    
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
            while chunk := file_like.read(4 * 1024 * 1024):  # 4MB chunks
                yield chunk
    
    return StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={output_filename}",
            "Content-Length": str(os.path.getsize(output_path))
        }
    )
