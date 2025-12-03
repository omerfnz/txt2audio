from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket import manager
import asyncio

router = APIRouter()

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
