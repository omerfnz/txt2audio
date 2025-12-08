from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine
from .db import models
from .routers import projects, audio, websocket, stream_f5
from .core.logging import logger
from .core.exceptions import global_exception_handler

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Audiobook Studio",
    description="Convert text to professional audiobooks with AI voice cloning",
    version="1.0.0"
)

# Register Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

logger.info("Application starting up...")

# CORS Middleware - WEBSOCKER İÇİN KRITIK!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")
app.include_router(stream_f5.router) # WebSocket root path, no /api prefix usually for WS


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
