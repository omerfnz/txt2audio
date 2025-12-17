from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import Project, Chunk
from ..core.config import settings
from ..services.merge_concat import merge_project_audio
from ..services.background_music import mix_background_music
from pathlib import Path
import os
import asyncio
from typing import AsyncGenerator

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


async def async_file_reader(file_path: str, chunk_size: int = 8 * 1024 * 1024) -> AsyncGenerator[bytes, None]:
    """
    Async file reader for faster streaming downloads.
    
    Args:
        file_path: Path to file
        chunk_size: Size of each chunk (default 8MB for faster downloads)
        
    Yields:
        File chunks as bytes
    """
    loop = asyncio.get_event_loop()
    
    def read_chunk(f, size):
        return f.read(size)
    
    with open(file_path, 'rb') as f:
        while True:
            # Use thread pool for non-blocking file I/O
            chunk = await loop.run_in_executor(None, read_chunk, f, chunk_size)
            if not chunk:
                break
            yield chunk


@router.get("/audio/download/{project_id}")
async def download_merged_audio(project_id: int, db: Session = Depends(get_db)):
    """
    Download merged final audio (WAV format).
    
    Optimized for faster downloads with:
    - Async streaming
    - Larger chunk sizes (8MB)
    - Proper Content-Length header
    """
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
    # Önce WAV'ı kontrol et, yoksa MP3'e fallback (geriye dönük uyumluluk)
    output_filename_wav = f"{project.name}_final.wav"
    output_filename_mp3 = f"{project.name}_final.mp3"
    output_path_wav = project_output_dir / output_filename_wav
    output_path_mp3 = project_output_dir / output_filename_mp3
    
    # WAV varsa onu kullan, yoksa MP3'e bak
    if output_path_wav.exists():
        output_path = output_path_wav
        output_filename = output_filename_wav
    elif output_path_mp3.exists():
        output_path = output_path_mp3
        output_filename = output_filename_mp3
    else:
        output_path = output_path_wav  # Varsayılan WAV
        output_filename = output_filename_wav
    
    # Check if merged file already exists (from automatic merge)
    if project.audio_path and os.path.exists(project.audio_path):
        # project.audio_path string olabilir, Path'e çevir
        output_path = Path(project.audio_path)
        output_filename = output_path.name
        print(f"✓ Using existing merged file: {output_path}")
    else:
        # Fallback: merge on-demand if file doesn't exist
        print(f"⚠ Merged file not found, merging on-demand...")
        try:
            merged_path = await merge_project_audio(
                project=project,
                chunks=chunks,
                project_output_dir=project_output_dir,
            )
            # Optional background music mix on-demand
            final_path = await mix_background_music(
                voice_mp3_path=str(merged_path),  # mix_background_music string bekliyor
                bg_music_file=project.bg_music_file if project.bg_music_enabled else "",
                volume=project.bg_music_volume if project.bg_music_volume is not None else settings.DEFAULT_BG_MUSIC_VOLUME,
            )
            project.audio_path = str(final_path)
            db.commit()
            db.refresh(project)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to merge audio files: {str(e)}"
            )
        
        if project.audio_path and os.path.exists(project.audio_path):
            # project.audio_path string olabilir, Path'e çevir
            output_path = Path(project.audio_path)
            output_filename = output_path.name
        else:
            raise HTTPException(status_code=500, detail="Failed to create merged audio file")
    
    # Verify file exists and get size
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    file_size = output_path.stat().st_size
    
    # Media type'ı dosya uzantısına göre belirle
    if output_path.suffix.lower() == '.wav':
        media_type = "audio/wav"
    else:
        media_type = "audio/mpeg"  # MP3 fallback
    
    # Use async streaming for faster downloads
    return StreamingResponse(
        async_file_reader(str(output_path), chunk_size=8 * 1024 * 1024),  # 8MB chunks
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{output_filename}"',
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        }
    )


@router.get("/audio/stream/{project_id}")
async def stream_audio(project_id: int, db: Session = Depends(get_db)):
    """
    Stream audio for playback (without download prompt).
    
    Uses smaller chunks for smoother playback.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.audio_path or not os.path.exists(project.audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    file_size = os.path.getsize(project.audio_path)
    
    # Media type'ı dosya uzantısına göre belirle
    file_ext = os.path.splitext(project.audio_path)[1].lower()
    if file_ext == '.wav':
        media_type = "audio/wav"
    else:
        media_type = "audio/mpeg"  # MP3 fallback
    
    # Smaller chunks for streaming playback (1MB)
    return StreamingResponse(
        async_file_reader(project.audio_path, chunk_size=1024 * 1024),
        media_type=media_type,
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        }
    )
