from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine
from .db import models
from .api import endpoints

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Audiobook Studio",
    description="Convert text to professional audiobooks with AI voice cloning",
    version="1.0.0"
)

# CORS Middleware - WEBSOCKER İÇİN KRITIK!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

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
