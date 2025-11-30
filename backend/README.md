# 🎙️ AI Audiobook Studio - Backend

High-performance FastAPI backend for AI Audiobook Studio, powered by Coqui TTS (XTTS v2).

## 🚀 Features

- **XTTS v2 Integration**: State-of-the-art voice cloning and text-to-speech.
- **FastAPI**: High-performance, easy-to-use web framework.
- **WebSocket Support**: Real-time progress updates for long-running tasks.
- **Text Processing**: Spacy-based NLP for intelligent sentence splitting.
- **Audio Processing**: FFmpeg integration for merging audio chunks.
- **Database**: SQLite with SQLAlchemy for project management.
- **GPU Acceleration**: CUDA support for faster generation.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Model**: [Coqui TTS](https://github.com/coqui-ai/TTS)
- **NLP**: [Spacy](https://spacy.io/)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) (SQLite)
- **Task Queue**: Asyncio for background tasks

## 📦 Installation & Setup

The backend is automatically set up via the root `setup-all.cmd` script. Manual setup:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## 🏃‍♂️ Running Locally

```bash
cd backend
venv\Scripts\activate
set COQUI_TOS_AGREED=1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **API Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📂 Directory Structure

```
app/
├── ai/             # TTS and Text processing logic
├── api/            # API endpoints (routers)
├── core/           # Configuration and settings
├── db/             # Database models and session
└── main.py         # Application entry point
storage/            # Generated files and models
```

## 🔧 Environment Variables

- `TTS_HOME`: Path to store/load TTS models.
- `COQUI_TOS_AGREED`: Must be set to `1` to accept Coqui license.
