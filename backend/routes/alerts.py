"""
Member 4 (Backend Engineer) owns this file.

Exposes high-risk content as "alerts" for the dashboard's alerts panel.

TODO for Member 4:
- Wire this up to a real notification channel (email/Slack/webhook) when a
  new high-risk item is inserted, instead of only polling via GET
"""

import logging

from fastapi import APIRouter, HTTPException

from database import get_storage
from schemas import AnalysisResult, ReviewRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AnalysisResult])
async def get_alerts(limit: int = 20):
    storage = get_storage()
    docs = await storage.find_analyses(
        query={"risk_level": "high", "reviewed": False},
        limit=limit,
    )
    return [AnalysisResult(**doc) for doc in docs]


@router.post("/{content_id}/review")
async def mark_reviewed(content_id: str, body: ReviewRequest = None):
    storage = get_storage()
    doc = await storage.find_one({"content_id": content_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Alert not found")

    notes = body.notes if body else None
    await storage.update_one(
        {"content_id": content_id},
        {"$set": {"reviewed": True, "reviewer_notes": notes}},
    )
    logger.info(f"Alert {content_id} marked as reviewed.")
    return {"status": "reviewed", "content_id": content_id}
