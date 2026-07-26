"""
Member 4 (Backend Engineer) owns this file.

Exposes high-risk content as "alerts" for the dashboard's alerts panel.

TODO for Member 4:
- Wire this up to a real notification channel (email/Slack/webhook) when a
  new high-risk item is inserted, instead of only polling via GET
- Add a mark-as-reviewed endpoint (human-in-the-loop step)
"""

from fastapi import APIRouter

from database import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def get_alerts(limit: int = 20):
    db = get_db()
    cursor = db.analyses.find({"risk_level": "high", "reviewed": False}).sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]


@router.post("/{content_id}/review")
async def mark_reviewed(content_id: str, notes: str | None = None):
    db = get_db()
    await db.analyses.update_one(
        {"content_id": content_id},
        {"$set": {"reviewed": True, "reviewer_notes": notes}},
    )
    return {"status": "reviewed"}
