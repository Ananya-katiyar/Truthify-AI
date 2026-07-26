"""
Member 4 (Backend Engineer) owns this file.

Handles content submission: forwards the text to the AI microservice
(ai-service/), stores the result in the DB, and returns it to the frontend.

TODO for Member 4:
- Add auth/rate limiting on the submit endpoint
- Add pagination to GET /content
- Handle AI service downtime gracefully (retry/queue instead of failing request)
"""

import os
import uuid

import httpx
from fastapi import APIRouter, HTTPException

from database import get_db
from schemas import AnalysisResult, ContentSubmission

router = APIRouter(prefix="/content", tags=["content"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


@router.post("/submit", response_model=AnalysisResult)
async def submit_content(payload: ContentSubmission):
    db = get_db()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{AI_SERVICE_URL}/analyze", json={"text": payload.text})
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"AI service error: {e}")

    ai_result = resp.json()
    content_id = str(uuid.uuid4())

    result = AnalysisResult(
        content_id=content_id,
        input_text=ai_result["input_text"],
        extracted_claims=ai_result["extracted_claims"],
        content_analysis=ai_result["content_analysis"],
        fact_check=ai_result["fact_check"],
        risk_score=ai_result["risk_score"],
        risk_level=ai_result["risk_level"],
        explanation=ai_result["explanation"],
    )

    await db.analyses.insert_one(result.model_dump())
    return result


@router.get("/", response_model=list[AnalysisResult])
async def list_content(risk_level: str | None = None, limit: int = 50):
    db = get_db()
    query = {"risk_level": risk_level} if risk_level else {}
    cursor = db.analyses.find(query).sort("created_at", -1).limit(limit)
    return [AnalysisResult(**doc) async for doc in cursor]


@router.get("/{content_id}", response_model=AnalysisResult)
async def get_content(content_id: str):
    db = get_db()
    doc = await db.analyses.find_one({"content_id": content_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return AnalysisResult(**doc)
