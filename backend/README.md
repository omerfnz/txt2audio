# 🎙️ AI Audiobook Studio - Backend

High-performance FastAPI backend for AI Audiobook Studio, powered by Coqui TTS (XTTS v2).

## 🚀 Features

- **XTTS v2 Integration**: State-of-the-art voice cloning and text-to-speech.
- **FastAPI**: High-performance, easy-to-use web framework.
- **WebSocket Support**: Real-time progress updates for long-running tasks.
- **Text Processing**: Spacy-based NLP for intelligent sentence splitting.
- **Audio Processing**: FFmpeg integration for merging audio chunks.
- **ACX Compliance**: Audio quality analysis and normalization for Audible ACX standards.
- **Chunk Quality Control**: Automatic detection and retry for failed audio chunks.
- **Reference Voice Validation**: Duration and loudness validation for reference audio files.
- **Process Cancellation**: Graceful cancellation of ongoing audio generation tasks.
- **Database**: SQLite with SQLAlchemy for project management.
- **GPU Acceleration**: CUDA support for faster generation.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Model**: [Coqui TTS](https://github.com/coqui-ai/TTS)
- **NLP**: [Spacy](https://spacy.io/)
- **Audio Analysis**: [Pydub](https://github.com/jiaaro/pydub) for ACX compliance
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) (SQLite)
- **Task Queue**: Asyncio for background tasks
- **WebSocket**: Native WebSocket support for real-time updates

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
│   ├── tts_engine.py      # XTTS v2 engine wrapper
│   ├── text_processor.py   # Text chunking and normalization
│   ├── text_normalizer.py # Text normalization utilities
│   └── tts_presets.py     # TTS preset configurations
├── routers/        # API endpoints (routers)
│   ├── projects.py        # Project CRUD and processing
│   ├── audio.py           # Audio streaming and download
│   └── websocket.py       # WebSocket connection handler
├── services/       # Business logic
│   ├── audio_service.py      # Audio generation and merging
│   ├── audio_analyzer.py      # ACX quality analysis
│   ├── audio_mastering.py     # ACX normalization
│   └── websocket.py           # WebSocket broadcasting
├── core/           # Configuration and settings
│   ├── config.py          # Application settings
│   ├── logger.py          # Logging configuration
│   └── exceptions.py      # Custom exceptions
├── db/             # Database models and session
│   ├── models.py          # SQLAlchemy models
│   └── session.py          # Database session management
├── utils/          # Utility functions
│   ├── epub_parser.py     # EPUB file parsing
│   ├── epub_cleaner.py    # EPUB content cleaning
│   └── gutenberg.py       # Project Gutenberg integration
└── main.py         # Application entry point
storage/            # Generated files and models
├── models/         # TTS model cache
├── uploads/         # Uploaded text/epub files
├── outputs/        # Generated audio files
└── reference_voices/ # Reference voice samples
```

## 🔧 Environment Variables

- `TTS_HOME`: Path to store/load TTS models (optional).
- `COQUI_TOS_AGREED`: Must be set to `1` to accept Coqui license.

## 📊 API Endpoints

### Projects
- `POST /api/projects` - Create a new project
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get project details
- `POST /api/projects/{id}/process` - Start audio generation
- `POST /api/projects/{id}/cancel` - Cancel ongoing processing
- `GET /api/projects/{id}/chunks` - Get project chunks
- `GET /api/projects/{id}/audio-quality` - Analyze ACX compliance
- `POST /api/projects/{id}/normalize` - Normalize audio for ACX

### Audio
- `GET /api/audio/chunk/{project_id}/{chunk_index}` - Stream chunk audio
- `GET /api/audio/download/{project_id}` - Download final audio

### WebSocket
- `WS /api/ws` - Real-time project status updates
