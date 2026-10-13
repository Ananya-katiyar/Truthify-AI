"""
Truthify-AI Backend Entrypoint.
Exposes API routes for content submissions (text & multimodal media),
high-risk alerts, and expanded database & knowledge base management.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import alerts, content, database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Truthify-AI Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploaded media previews
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(content.router)
app.include_router(alerts.router)
app.include_router(database.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend", "db_expanded": True}


logger.info("Backend API initialized. Docs at http://localhost:8000/docs")
