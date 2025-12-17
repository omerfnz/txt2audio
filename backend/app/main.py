from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
import os
from .db.session import engine
from .db import models
from .routers import projects, audio, websocket
from .core.logging import logger
from .core.exceptions import global_exception_handler
from .core.config import settings

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# RangeHTTPServer thread'i için global değişken
_range_server_thread = None
_range_server_process = None


def _start_range_server():
    """RangeHTTPServer'ı background thread'de başlat"""
    global _range_server_thread, _range_server_process
    
    if not settings.RANGE_SERVER_ENABLED:
        logger.info("RangeHTTPServer disabled in config")
        return
    
    try:
        from RangeHTTPServer import RangeHTTPRequestHandler
        import socketserver
        
        # Serve edilecek dizin
        serve_dir = str(settings.RANGE_SERVER_ROOT_DIR)
        
        # Port
        port = settings.RANGE_SERVER_PORT
        
        # Thread içinde working directory'yi değiştir (daemon thread olduğu için güvenli)
        original_cwd = os.getcwd()
        os.chdir(serve_dir)
        
        # Custom handler with Range support and CORS
        class RangeRequestHandler(RangeHTTPRequestHandler):
            def end_headers(self):
                # CORS headers ekle
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Range')
                super().end_headers()
        
        # HTTP Server oluştur
        httpd = socketserver.TCPServer(("", port), RangeRequestHandler)
        
        logger.info(f"🌐 RangeHTTPServer started on port {port}")
        logger.info(f"   Serving directory: {serve_dir}")
        logger.info(f"   Access: http://localhost:{port}/")
        
        try:
            # Server'ı başlat (blocking call)
            httpd.serve_forever()
        finally:
            # Cleanup: working directory'yi geri al
            os.chdir(original_cwd)
        
    except ImportError:
        logger.warning("⚠ RangeHTTPServer not installed. Install with: pip install rangehttpserver")
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f"⚠ Port {settings.RANGE_SERVER_PORT} already in use. RangeHTTPServer not started.")
        else:
            logger.error(f"❌ RangeHTTPServer error: {e}")
    except Exception as e:
        logger.error(f"❌ RangeHTTPServer startup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup ve shutdown event'leri"""
    # Startup
    logger.info("Application starting up...")
    
    # RangeHTTPServer'ı başlat
    if settings.RANGE_SERVER_ENABLED:
        range_thread = threading.Thread(target=_start_range_server, daemon=True)
        range_thread.start()
        logger.info("✓ RangeHTTPServer thread started")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="AI Audiobook Studio",
    description="Convert text to professional audiobooks with AI voice cloning",
    version="1.0.0",
    lifespan=lifespan
)

# Register Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# CORS Middleware - WEBSOCKER İÇİN KRITIK!
# CloudSpaces origin'leri için regex kullanıyoruz (wildcard ile credentials uyumsuz)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_origin_regex=settings.CLOUDSPACES_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "AI Audiobook Studio API is running",
        "docs": "http://localhost:8000/docs",
        "health": "✓ OK"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/health")
def health_check_api():
    """Health check endpoint with /api prefix for Vite proxy compatibility"""
    return {"status": "healthy"}
