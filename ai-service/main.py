"""
AI Microservice entrypoint. Exposes the full multimodal analysis pipeline:
- Multimodal extraction (PDF, Image, Video, Text)
- Claim extraction
- NLP analysis (intent, tone, content type)
- Live internet fact-checking across trusted sources
- Agentic decision engine
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph import run_pipeline
from preprocessing.multimodal import process_media_file
from rag.embed_store import build_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-build local embedding store on startup."""
    logger.info("Initializing knowledge store...")
    try:
        build_index()
        logger.info("Knowledge store ready.")
    except Exception as e:
        logger.warning(f"Could not build local index on startup: {e}")
    yield


app = FastAPI(title="Truthify-AI Microservice", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str
    media_info: Optional[dict] = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-service", "multimodal": True, "live_internet": True}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not req.text.strip() and not req.media_info:
        raise HTTPException(status_code=400, detail="Text or media content cannot be empty")
    try:
        result = run_pipeline(req.text, media_info=req.media_info)
        return result
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze-media")
async def analyze_media(
    file: UploadFile = File(...),
    text: Optional[str] = Form("")
):
    """Directly uploads and analyzes an image, video, or PDF document."""
    try:
        file_bytes = await file.read()
        media_result = process_media_file(
            file_bytes=file_bytes,
            filename=file.filename or "uploaded_media",
            mime_type=file.content_type or ""
        )

        extracted_text = media_result.get("extracted_text", "")
        combined_text = (text or "").strip()
        if extracted_text.strip():
            if combined_text:
                combined_text = f"{combined_text}\n\n[Extracted from {file.filename}]:\n{extracted_text}"
            else:
                combined_text = extracted_text

        result = run_pipeline(combined_text, media_info=media_result)
        return result
    except Exception as e:
        logger.error(f"Multimodal pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multimodal analysis failed: {str(e)}")
