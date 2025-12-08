import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import traceback

from ..services.audio_service import get_tts_engine

router = APIRouter()

@router.websocket("/ws/generate-f5")
async def websocket_f5_tts(websocket: WebSocket):
    """
    WebSocket endpoint for F5-TTS streaming.
    Receives JSON config and streams back audio chunks (binary).
    """
    await websocket.accept()
    print("🔌 WebSocket: Client connected to F5-TTS stream")
    
    try:
        # 1. Wait for configuration
        data = await websocket.receive_json()
        print(f"📄 WebSocket: Received job: {data}")
        
        text = data.get("text")
        ref_audio_path = data.get("ref_audio_path")
        ref_text = data.get("ref_text", "")
        speed = float(data.get("speed", 0.9))
        
        if not text or not ref_audio_path:
            await websocket.send_text("ERROR: Missing text or ref_audio_path")
            await websocket.close()
            return

        # 2. Get F5 Engine (This will unload XTTS if active)
        # We assume GPU is available since F5 requires it basically
        engine = get_tts_engine(use_gpu=True, model_type="f5")
        
        # 3. Stream Audio
        # F5 currently generates full sentence chunks. 
        # For better UX, we can split text by punctuation here or rely on engine.
        # Simple splitting by sentence for now:
        sentences = text.replace("!", ".").replace("?", ".").replace("\n", ".").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            sentences = [text]

        for i, sentence in enumerate(sentences):
            print(f"  🗣️ Streaming chunk {i+1}/{len(sentences)}: {sentence[:30]}...")
            
            # Generator consumes audio chunks
            chunk_generator = engine.generate_stream(
                text=sentence,
                ref_audio=ref_audio_path,
                ref_text=ref_text,
                speed=speed
            )
            
            for audio_chunk in chunk_generator:
                # Send binary audio data
                await websocket.send_bytes(audio_chunk)
                # Small yield to let event loop breathe
                await asyncio.sleep(0.01)
                
        # 4. Signal End of Stream
        await websocket.send_text("END_OF_STREAM")
        print("✅ WebSocket: Stream completed")
        
    except WebSocketDisconnect:
        print("🔌 WebSocket: Client disconnected")
    except Exception as e:
        print(f"❌ WebSocket Error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_text(f"ERROR: {str(e)}")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

