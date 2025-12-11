from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import Project, Chunk
from ..ai.text_processor import TextProcessor
from ..ai.tts_presets import get_all_presets, get_preset, validate_preset_params

from ..core.config import settings
from ..services.audio_service import process_audio_task
from ..services.audio_analyzer import AudioAnalyzer
from ..services.audio_mastering import AudioMastering
from ..core.logging import logger
from ..services.websocket import manager
from pydub import AudioSegment
from typing import List, Dict, Any, Optional
import shutil
import os
from pathlib import Path

router = APIRouter()
text_processor = TextProcessor()
audio_analyzer = AudioAnalyzer()
audio_mastering = AudioMastering()


@router.get("/tts-presets")
async def get_tts_presets() -> Dict[str, Any]:
    """
    Get all available TTS preset configurations.
    
    Returns dictionary of preset IDs mapped to their full configuration,
    including temperature, top_p, repetition_penalty, and descriptions.
    """
    presets = get_all_presets()
    
    return {
        "presets": {
            preset_id: {
                "name": preset.name,
                "description": preset.description,
                "language": preset.language,
                "content_type": preset.content_type,
                "parameters": {
                    "temperature": preset.temperature,
                    "top_p": preset.top_p,
                    "repetition_penalty": preset.repetition_penalty,
                    "speed": preset.speed,
                    "enable_text_splitting": preset.enable_text_splitting
                }
            }
            for preset_id, preset in presets.items()
        }
    }

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


@router.get("/music")
async def list_background_music() -> Dict[str, Any]:
    """
    storage/music içindeki dosyaları listeler.
    Dosya yoksa boş liste döner, hata fırlatmaz.
    """
    music_dir: Path = settings.MUSIC_DIR
    if not music_dir.exists():
        return {"music": []}

    music_files = []
    for file_path in music_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}:
            music_files.append({
                "name": file_path.stem,
                "filename": file_path.name,
                "path": str(file_path)
            })

    return {"music": music_files}

@router.post("/projects/")
async def create_project(
    name: str = Form(...),
    text_file: UploadFile = File(...),
    voice_file: Optional[UploadFile] = File(None),
    reference_voice_path: Optional[str] = Form(None),
    use_gpu: bool = Form(False),
    # TTS Preset (NEW)
    preset_id: str = Form("en_fiction"),
    content_type: Optional[str] = Form(None),
    # TTS Model (legacy - XTTS only)
    modelType: str = Form("xtts"),
    # XTTS Parameters (can override preset)
    language: Optional[str] = Form(None),
    speed: Optional[float] = Form(None),
    temperature: Optional[float] = Form(None),
    top_k: int = Form(50),
    top_p: Optional[float] = Form(None),
    repetition_penalty: Optional[float] = Form(None),
    # Background music
    bg_music_enabled: bool = Form(False),
    bg_music_file: Optional[str] = Form(None),
    bg_music_volume: Optional[float] = Form(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create new audiobook project with TTS preset support.
    
    Supports ONLY TXT file format. Parameters can either
    use a preset configuration or be manually specified.
    """
    try:
        # 1. Get preset configuration
        preset = get_preset(preset_id)
        if not preset:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid preset_id: {preset_id}"
            )
        
        # 2. Determine source type (Force TXT)
        source_type = "txt"
        
        # 3. Use preset values or form overrides
        final_language = language or preset.language
        final_temperature = temperature if temperature is not None else preset.temperature
        final_top_p = top_p if top_p is not None else preset.top_p
        final_repetition_penalty = (
            repetition_penalty if repetition_penalty is not None
            else preset.repetition_penalty
        )
        final_speed = speed if speed is not None else preset.speed
        final_content_type = content_type or preset.content_type
        # Background music config
        final_bg_enabled = bg_music_enabled
        final_bg_file = bg_music_file or settings.DEFAULT_BG_MUSIC_FILE
        final_bg_volume = bg_music_volume if bg_music_volume is not None else settings.DEFAULT_BG_MUSIC_VOLUME
        
        # 4. Validate parameters
        is_valid, error_msg = validate_preset_params(
            final_temperature,
            final_top_p,
            final_repetition_penalty,
            final_speed
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 5. Save text file
        text_path = settings.UPLOAD_DIR / f"{name}_{text_file.filename}"
        
        with open(text_path, "wb") as buffer:
            shutil.copyfileobj(text_file.file, buffer)
        
        # 6. Handle voice file (uploaded or reference)
        if voice_file:
            voice_path = settings.UPLOAD_DIR / f"{name}_{voice_file.filename}"
            with open(voice_path, "wb") as buffer:
                shutil.copyfileobj(voice_file.file, buffer)
            voice_path = str(voice_path)
        elif reference_voice_path:
            voice_path = settings.REFERENCE_VOICES_DIR / reference_voice_path
            if not voice_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail="Reference voice not found"
                )
            voice_path = str(voice_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either voice_file or reference_voice_path must be provided"
            )

        # 6.b Basic reference voice validation (duration & loudness)
        try:
            audio = AudioSegment.from_file(voice_path)
            duration_sec = len(audio) / 1000.0
            rms_db = audio.dBFS if audio.dBFS != float("-inf") else -100.0

            logger.info(
                "Reference voice stats | project_name=%s duration=%.2fs rms=%.2fdB path=%s",
                name,
                duration_sec,
                rms_db,
                voice_path,
            )

            # En stabil klonlama için 3–15 sn arası, orta seviye bir RMS önerilir
            if duration_sec < 3.0 or duration_sec > 15.0:
                raise HTTPException(
                    status_code=400,
                    detail="Reference voice duration must be between 3 and 15 seconds for stable voice cloning.",
                )

            # Çok sessiz veya aşırı yüksek referanslar için sadece uyarı logla
            if rms_db < -45.0 or rms_db > -5.0:
                logger.warning(
                    "Reference voice RMS out of recommended range | project_name=%s rms=%.2fdB path=%s",
                    name,
                    rms_db,
                    voice_path,
                )
        except HTTPException:
            raise
        except Exception as ref_error:
            logger.warning("Reference voice analysis failed | project_name=%s error=%s", name, ref_error)

        # Convert text_path to string for DB
        text_path = str(text_path)

        # 7. Create DB record with preset configuration
        project = Project(
            name=name,
            text_path=text_path,
            voice_ref_path=voice_path,
            status="created",
            # Source metadata
            source_type=source_type,
            content_type=final_content_type,
            preset_id=preset_id,
            tts_model="xtts",
            # XTTS Config
            language=final_language,
            speed=final_speed,
            temperature=final_temperature,
            top_k=top_k,
            top_p=final_top_p,
            repetition_penalty=final_repetition_penalty,
            # Background music config
            bg_music_enabled=final_bg_enabled,
            bg_music_file=final_bg_file,
            bg_music_volume=final_bg_volume
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # 8. Read and chunk text
        with open(text_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        # Chunk text (Gutenberg cleaner artık gerekli değil - temiz txt dosyası kullanılıyor)
        chunks = text_processor.split_into_chunks(full_text, language=final_language)

        # 9. Log chunk statistics for analysis
        if chunks:
            chunk_lengths = [len(c) for c in chunks if c]
            if chunk_lengths:
                total_chunks = len(chunk_lengths)
                min_len = min(chunk_lengths)
                max_len = max(chunk_lengths)
                avg_len = sum(chunk_lengths) / total_chunks
                logger.info(
                    "Text chunking stats | project_id=%s total_chunks=%s min_len=%s max_len=%s avg_len=%.2f language=%s",
                    project.id,
                    total_chunks,
                    min_len,
                    max_len,
                    avg_len,
                    final_language,
                )

        # 10. Create chunks in database
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
            "source_type": source_type,
            "preset_used": preset_id,
            "parameters": {
                "temperature": final_temperature,
                "top_p": final_top_p,
                "repetition_penalty": final_repetition_penalty,
                "speed": final_speed,
                "language": final_language
            },
            "message": "Project created and text chunked successfully."
        }
    except HTTPException:
        raise
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

    # Reset cancellation flag and status before starting
    project.is_cancelled = False
    project.status = "processing"
    db.commit()
    
    background_tasks.add_task(process_audio_task, project_id, use_gpu)
    
    return {"message": "Processing started in background."}


@router.post("/projects/{project_id}/cancel")
async def cancel_project(
    project_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    İşlemdeki bir projeyi iptal eder.

    Arka plandaki TTS işçisi, bir sonraki chunk'ta bu bayrağı görüp
    güvenli bir şekilde durur.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status in ("completed", "failed", "cancelled"):
        return {
            "project_id": project_id,
            "status": project.status,
            "message": f"Project already in terminal state: {project.status}"
        }

    project.is_cancelled = True
    project.status = "cancelled"
    db.commit()

    # Notify all connected clients via WebSocket
    await manager.broadcast({
        "type": "status_update",
        "project_id": project_id,
        "status": "cancelled",
        "progress": 0,
    })

    return {
        "project_id": project_id,
        "status": "cancelled",
        "message": "Project cancellation requested."
    }


@router.post("/projects/{project_id}/resume")
async def resume_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    use_gpu: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Yarıda kalan veya başarısız olan projeyi devam ettirir.
    
    Resume yapılabilir durumlar:
    - failed: İşlem sırasında hata oluşmuş
    - cancelled: Kullanıcı tarafından iptal edilmiş
    - processing: Sunucu çökmesi/yeniden başlatma durumu
    - created: Henüz başlatılmamış (ilk process gibi davranır)
    
    Resume yapılamaz durumlar:
    - completed: Zaten tamamlanmış
    - merging: Merge işlemi devam ediyor
    - Merge edilmiş ve chunk dosyaları silinmiş projeler
    
    Args:
        project_id: Devam ettirilecek proje ID
        use_gpu: GPU kullanılsın mı
        
    Returns:
        Resume durumu ve bilgileri
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Status kontrolü - completed ve merging durumlarında resume yapılamaz
    if project.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Project is already completed. Resume not needed."
        )
    
    if project.status == "merging":
        raise HTTPException(
            status_code=400,
            detail="Project is currently merging. Please wait for completion."
        )
    
    # Merge edilmiş proje kontrolü - audio_path varsa chunk dosyaları silinmiş olabilir
    if project.audio_path and os.path.exists(project.audio_path):
        raise HTTPException(
            status_code=400,
            detail="Project has been merged. Chunk files are deleted, resume not possible."
        )
    
    # Chunk'ları kontrol et
    chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No chunks found for this project."
        )
    
    # İşlenmemiş chunk sayısını hesapla
    unprocessed_chunks = [c for c in chunks if not c.is_processed]
    processed_chunks = [c for c in chunks if c.is_processed]
    
    if not unprocessed_chunks:
        # Tüm chunk'lar işlenmiş ama proje completed değil - merge yapılabilir
        raise HTTPException(
            status_code=400,
            detail="All chunks are processed. Project should be merged, not resumed."
        )
    
    # Resume count'u artır
    project.resume_count = (project.resume_count or 0) + 1
    
    # İptal bayrağını temizle ve durumu güncelle
    project.is_cancelled = False
    project.status = "processing"
    project.last_error = None  # Önceki hatayı temizle
    
    db.commit()
    
    # Mevcut ilerlemeyi hesapla (kaldığı yerden devam)
    current_progress = (len(processed_chunks) / len(chunks)) * 100
    
    # WebSocket ile resume başladı bildirimi
    await manager.broadcast({
        "type": "status_update",
        "project_id": project_id,
        "status": "processing",
        "progress": current_progress,
        "message": f"Resumed from {len(processed_chunks)}/{len(chunks)} chunks"
    })
    
    # Background task olarak işlemi başlat
    background_tasks.add_task(process_audio_task, project_id, use_gpu)
    
    return {
        "project_id": project_id,
        "status": "resumed",
        "resume_count": project.resume_count,
        "total_chunks": len(chunks),
        "processed_chunks": len(processed_chunks),
        "remaining_chunks": len(unprocessed_chunks),
        "progress": current_progress,
        "message": f"Project resumed. Processing {len(unprocessed_chunks)} remaining chunks."
    }


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

@router.get("/projects/{project_id}/audio-quality")
def get_audio_quality(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Proje audio kalitesini analiz eder ve ACX uyumluluk raporu döndürür.
    
    Args:
        project_id: Proje ID
        
    Returns:
        Audio kalite metrikleri ve ACX uyumluluk durumu
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.audio_path or not os.path.exists(project.audio_path):
        raise HTTPException(
            status_code=400,
            detail="Audio file not found. Project may not be completed yet."
        )
    
    try:
        # MP3'ü WAV'a çevir (analiz için)
        from pydub import AudioSegment
        temp_wav = project.audio_path.replace('.mp3', '_temp.wav')
        
        audio = AudioSegment.from_mp3(project.audio_path)
        audio.export(temp_wav, format='wav')
        
        # Analiz yap
        analysis = audio_analyzer.analyze(temp_wav)
        compliance = audio_analyzer.get_compliance_details(analysis)

        # FastAPI/Pydantic JSON serileştirmesi için numpy.bool tiplerini
        # native Python bool tipine dönüştür
        analysis["acx_compliant"] = bool(analysis["acx_compliant"])
        for key in ("rms", "peak", "noise_floor"):
            if key in compliance and "pass" in compliance[key]:
                compliance[key]["pass"] = bool(compliance[key]["pass"])
        
        # Temp dosyayı sil
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        
        return {
            "project_id": project_id,
            "audio_path": project.audio_path,
            "analysis": analysis,
            "compliance_details": compliance,
            "overall_acx_compliant": analysis["acx_compliant"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio analysis failed: {str(e)}"
        )

@router.post("/projects/{project_id}/normalize")
async def normalize_audio(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Proje ses dosyasını ACX standartlarına göre normalize eder.
    
    Args:
        project_id: Proje ID
        
    Returns:
        İşlem durumu
    """
    # Project kontrolü
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Dosya kontrolü
    if not project.audio_path:
        raise HTTPException(
            status_code=400,
            detail="Audio path not set. Project may not be completed yet."
        )
    
    if not os.path.exists(project.audio_path):
        raise HTTPException(
            status_code=400,
            detail=f"Audio file not found on disk: {project.audio_path}"
        )
    
    # Dosya boyutu kontrolü
    file_size = os.path.getsize(project.audio_path)
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty (0 bytes)"
        )
    
    try:
        # Normalized dosya yolu
        original_path = project.audio_path
        normalized_path = original_path.replace('.mp3', '_normalized.mp3')
        
        # Background task olarak normalize et
        def normalize_task():
            try:
                print(f"🎚️ Starting normalization for project {project_id}...")
                print(f"   Input: {original_path} ({file_size:,} bytes)")
                
                success = audio_mastering.normalize_for_acx(
                    original_path,
                    normalized_path,
                    use_ffmpeg_normalize=True
                )
                
                if success and os.path.exists(normalized_path):
                    # Yeni dosya boyutu kontrolü
                    new_size = os.path.getsize(normalized_path)
                    if new_size > 0:
                        # Eski dosyayı sil, yeniyi orijinal isimle kaydet
                        os.remove(original_path)
                        os.rename(normalized_path, original_path)
                        print(f"✓ Audio normalized for project {project_id}")
                        print(f"   Output: {original_path} ({new_size:,} bytes)")
                    else:
                        print(f"⚠ Normalized file is empty, keeping original")
                        if os.path.exists(normalized_path):
                            os.remove(normalized_path)
                else:
                    print(f"⚠ Normalization failed for project {project_id}")
                    # Temp dosyayı temizle
                    if os.path.exists(normalized_path):
                        os.remove(normalized_path)
                        
            except Exception as e:
                print(f"❌ Normalization error for project {project_id}: {e}")
                # Temp dosyayı temizle
                if os.path.exists(normalized_path):
                    try:
                        os.remove(normalized_path)
                    except:
                        pass
        
        background_tasks.add_task(normalize_task)
        
        return {
            "project_id": project_id,
            "message": "Normalization started in background",
            "status": "processing",
            "file_size": file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Normalization setup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Normalization setup failed: {str(e)}"
        )
