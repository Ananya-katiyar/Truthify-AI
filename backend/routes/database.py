"""
Database Management & Knowledge Hub Routes.

Provides endpoints to explore and manage the expanded database:
- Dynamic Verified Facts (search, filter, create, delete)
- Trusted Internet Sources Directory (inspect, add custom sources)
- Media Records Registry
- Database Overview Statistics
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from database import get_storage
from schemas import (
    DatabaseOverview,
    VerifiedFact,
    VerifiedFactCreate,
    TrustedSource,
    TrustedSourceCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])


@router.get("/overview", response_model=DatabaseOverview)
async def get_database_overview():
    """Returns overview statistics of the expanded database collections."""
    storage = get_storage()
    data = await storage.get_overview()
    return DatabaseOverview(**data)


@router.get("/facts", response_model=List[VerifiedFact])
async def list_verified_facts(
    topic: Optional[str] = Query(None, description="Filter by topic (health, elections, tech, etc.)"),
    verdict: Optional[str] = Query(None, description="Filter by verdict"),
    search: Optional[str] = Query(None, description="Search claim text or explanation"),
    limit: int = Query(50, ge=1, le=200)
):
    """Retrieve verified facts stored in the dynamic knowledge base."""
    storage = get_storage()
    facts = await storage.find_facts(topic=topic, verdict=verdict, search=search, limit=limit)
    return [VerifiedFact(**f) for f in facts]


@router.post("/facts", response_model=VerifiedFact)
async def add_verified_fact(payload: VerifiedFactCreate):
    """Add a new custom verified fact to expand the database."""
    storage = get_storage()
    doc = payload.model_dump()
    saved = await storage.insert_fact(doc)
    return VerifiedFact(**saved)


@router.delete("/facts/{fact_id}")
async def delete_verified_fact(fact_id: str):
    """Delete a verified fact from the database."""
    storage = get_storage()
    deleted = await storage.delete_fact(fact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fact not found")
    return {"status": "ok", "deleted_fact_id": fact_id}


@router.get("/sources", response_model=List[TrustedSource])
async def list_trusted_sources():
    """List all trusted internet domains and their reputation scores."""
    storage = get_storage()
    sources = await storage.find_trusted_sources()
    return [TrustedSource(**s) for s in sources]


@router.post("/sources", response_model=TrustedSource)
async def add_trusted_source(payload: TrustedSourceCreate):
    """Register or update a trusted internet source in the database."""
    storage = get_storage()
    saved = await storage.insert_trusted_source(payload.model_dump())
    return TrustedSource(**saved)


@router.delete("/sources/{domain}")
async def delete_trusted_source(domain: str):
    """Remove a trusted source domain from the directory."""
    storage = get_storage()
    deleted = await storage.delete_trusted_source(domain)
    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found in trusted sources")
    return {"status": "ok", "deleted_domain": domain}


@router.get("/media")
async def list_media_records(limit: int = Query(50, ge=1, le=100)):
    """List uploaded media files and their extraction records."""
    storage = get_storage()
    return await storage.list_media(limit=limit)
