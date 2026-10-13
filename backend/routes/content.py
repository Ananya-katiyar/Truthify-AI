"""
Content Submission and Evaluation Routes.

Handles:
- Text submissions (JSON)
- Multimodal submissions (Images, Videos, PDFs via multipart upload)
- Auto-expansion of the verified facts database from high-confidence internet findings.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from database import get_storage
from schemas import AnalysisResult, ContentSubmission, FeedbackSubmission, StatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def _auto_ingest_verified_facts(fact_checks: list[dict], storage):
    """
    Dynamically expands the database by auto-ingesting verified facts
    uncovered by live internet search.
    """
    for fc in fact_checks:
        verdict = fc.get("verdict")
        confidence = fc.get("confidence", 0.0)
        claim = fc.get("claim", "").strip()

        # Only ingest high-confidence conclusive findings
        if claim and verdict in ("debunked_as_false", "confirmed_true") and confidence >= 0.80:
            top_ev = fc.get("evidence", [{}])[0] if fc.get("evidence") else {}
            explanation = fc.get("explanation") or top_ev.get("snippet", "")
            source_name = fc.get("source") or top_ev.get("source_name", "Verified Fact Check")
            source_url = fc.get("top_url") or top_ev.get("url", "")
            domain = top_ev.get("domain", "")

            fact_doc = {
                "claim": claim,
                "verdict": verdict,
                "explanation": explanation,
                "source_name": source_name,
                "source_url": source_url,
                "domain": domain,
                "topic": "general",
                "trust_score": round(confidence, 2),
                "auto_ingested": True,
            }
            try:
                await storage.insert_fact(fact_doc)
                logger.info(f"Auto-ingested verified fact into database: '{claim[:50]}'")
            except Exception as e:
                logger.warning(f"Could not auto-ingest fact: {e}")


@router.post("/submit", response_model=AnalysisResult)
async def submit_content(payload: ContentSubmission):
    storage = get_storage()

    # Call AI microservice
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{AI_SERVICE_URL}/analyze", json={"text": payload.text})
            resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=502,
                detail="AI service is not running. Start it with: cd ai-service && uvicorn main:app --port 8001"
            )
        except httpx.HTTPError as e:
            logger.error(f"AI service error: {e}")
            raise HTTPException(status_code=502, detail=f"AI service error: {e}")

    ai_result = resp.json()
    content_id = str(uuid.uuid4())

    media_info = ai_result.get("media_info") or {}

    result = AnalysisResult(
        content_id=content_id,
        input_text=ai_result.get("input_text", payload.text),
        source_type=payload.source_type,
        extracted_claims=ai_result.get("extracted_claims", []),
        content_analysis=ai_result.get("content_analysis", {}),
        fact_check=ai_result.get("fact_check", []),
        risk_score=ai_result.get("risk_score", 0),
        risk_level=ai_result.get("risk_level", "unknown"),
        explanation=ai_result.get("explanation", []),
        confidence=ai_result.get("confidence", 0.0),
        summary=ai_result.get("summary", ""),
        processing_time_seconds=ai_result.get("processing_time_seconds", 0.0),
        media_type=media_info.get("media_type", "text"),
        media_filename=media_info.get("filename"),
        media_metadata=media_info.get("metadata", {}),
        thumbnail_b64=media_info.get("thumbnail_b64"),
        internet_sources_queried=ai_result.get("internet_sources_queried", []),
    )

    await storage.insert_analysis(result.model_dump())

    # Dynamically expand verified facts database
    await _auto_ingest_verified_facts(result.fact_check, storage)

    logger.info(f"Analyzed content {content_id}: risk={result.risk_level} score={result.risk_score}")
    return result


@router.post("/submit-media", response_model=AnalysisResult)
async def submit_media(
    file: UploadFile = File(...),
    text: Optional[str] = Form(""),
    source_type: Optional[str] = Form("user_submitted")
):
    """
    Submits a media file (Image, Video, or PDF) for full multimodal analysis,
    OCR, keyframe extraction, and live internet fact checking.
    """
    storage = get_storage()

    # Save local copy for permanent record
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex[:12]}{file_ext}"
    local_path = UPLOAD_DIR / unique_filename

    file_bytes = await file.read()
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    # Forward to AI service multipart endpoint
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            files = {"file": (file.filename, file_bytes, file.content_type)}
            data = {"text": text or ""}
            resp = await client.post(f"{AI_SERVICE_URL}/analyze-media", files=files, data=data)
            resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=502,
                detail="AI service is not running. Start it with: cd ai-service && uvicorn main:app --port 8001"
            )
        except httpx.HTTPError as e:
            logger.error(f"AI service media error: {e}")
            raise HTTPException(status_code=502, detail=f"AI service media error: {e}")

    ai_result = resp.json()
    content_id = str(uuid.uuid4())
    media_info = ai_result.get("media_info") or {}

    # Store media record in DB
    media_record = {
        "media_id": f"media-{uuid.uuid4().hex[:8]}",
        "filename": file.filename,
        "stored_filename": unique_filename,
        "media_type": media_info.get("media_type", "file"),
        "file_size_bytes": len(file_bytes),
        "mime_type": file.content_type or "",
        "extracted_text": media_info.get("extracted_text", ""),
        "metadata": media_info.get("metadata", {}),
        "thumbnail_b64": media_info.get("thumbnail_b64", ""),
    }
    await storage.insert_media(media_record)

    result = AnalysisResult(
        content_id=content_id,
        input_text=ai_result.get("input_text", text or file.filename),
        source_type=source_type or "user_submitted",
        extracted_claims=ai_result.get("extracted_claims", []),
        content_analysis=ai_result.get("content_analysis", {}),
        fact_check=ai_result.get("fact_check", []),
        risk_score=ai_result.get("risk_score", 0),
        risk_level=ai_result.get("risk_level", "unknown"),
        explanation=ai_result.get("explanation", []),
        confidence=ai_result.get("confidence", 0.0),
        summary=ai_result.get("summary", ""),
        processing_time_seconds=ai_result.get("processing_time_seconds", 0.0),
        media_type=media_info.get("media_type", "image"),
        media_filename=file.filename,
        media_metadata=media_info.get("metadata", {}),
        thumbnail_b64=media_info.get("thumbnail_b64"),
        internet_sources_queried=ai_result.get("internet_sources_queried", []),
    )

    await storage.insert_analysis(result.model_dump())

    # Dynamically expand verified facts database
    await _auto_ingest_verified_facts(result.fact_check, storage)

    logger.info(f"Analyzed media {file.filename}: type={result.media_type} risk={result.risk_level}")
    return result


@router.get("/", response_model=list[AnalysisResult])
async def list_content(risk_level: str | None = None, limit: int = 50):
    storage = get_storage()
    query = {"risk_level": risk_level} if risk_level else {}
    docs = await storage.find_analyses(query=query, limit=limit)
    return [AnalysisResult(**doc) for doc in docs]


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    storage = get_storage()
    total = await storage.count()
    high = await storage.count({"risk_level": "high"})
    medium = await storage.count({"risk_level": "medium"})
    low = await storage.count({"risk_level": "low"})
    pending = await storage.count({"risk_level": "high", "reviewed": False})
    return StatsResponse(
        total_analyzed=total,
        high_risk=high,
        medium_risk=medium,
        low_risk=low,
        pending_review=pending,
    )


@router.get("/{content_id}", response_model=AnalysisResult)
async def get_content(content_id: str):
    storage = get_storage()
    doc = await storage.find_one({"content_id": content_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return AnalysisResult(**doc)


@router.post("/{content_id}/feedback")
async def submit_feedback(content_id: str, feedback: FeedbackSubmission):
    storage = get_storage()
    doc = await storage.find_one({"content_id": content_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")

    updated = await storage.update_one(
        {"content_id": content_id},
        {"$set": {
            "human_feedback": feedback.correct_risk_level,
            "feedback_notes": feedback.notes,
            "risk_level": feedback.correct_risk_level,
        }}
    )
    return {"status": "ok", "updated": updated}
