from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContentSubmission(BaseModel):
    text: str = ""
    source_type: str = Field(default="user_submitted", description="social_media | news_article | user_submitted | document | broadcast")
    submitted_by: Optional[str] = None


class AnalysisResult(BaseModel):
    content_id: str
    input_text: str
    source_type: str = "user_submitted"
    extracted_claims: list[str] = []
    content_analysis: dict = {}
    fact_check: list[dict] = []
    risk_score: int = 0
    risk_level: str = "unknown"
    explanation: list[str] = []
    confidence: float = 0.0
    summary: str = ""
    processing_time_seconds: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reviewed: bool = False
    reviewer_notes: Optional[str] = None
    # Multimodal additions
    media_type: str = "text"
    media_filename: Optional[str] = None
    media_metadata: dict = {}
    thumbnail_b64: Optional[str] = None
    # Internet sources additions
    internet_sources_queried: list[dict] = []


class FeedbackSubmission(BaseModel):
    correct_risk_level: str
    notes: Optional[str] = None


class ReviewRequest(BaseModel):
    notes: Optional[str] = None


class StatsResponse(BaseModel):
    total_analyzed: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0
    pending_review: int = 0


# --- Expanded Database Schemas ---

class VerifiedFact(BaseModel):
    fact_id: str
    claim: str
    verdict: str = Field(description="debunked_as_false | confirmed_true | disputed_or_misleading | unverified")
    explanation: str
    source_name: str
    source_url: Optional[str] = ""
    domain: Optional[str] = ""
    topic: str = "general"
    trust_score: float = 0.90
    auto_ingested: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class VerifiedFactCreate(BaseModel):
    claim: str
    verdict: str = "debunked_as_false"
    explanation: str
    source_name: str
    source_url: Optional[str] = ""
    topic: Optional[str] = "general"
    trust_score: Optional[float] = 0.90


class TrustedSource(BaseModel):
    domain: str
    name: str
    category: str = Field(description="fact_checker | health_authority | news_agency | scientific_authority | encyclopedia")
    trust_score: float = 0.95
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TrustedSourceCreate(BaseModel):
    domain: str
    name: str
    category: str = "fact_checker"
    trust_score: float = 0.95
    is_active: bool = True


class DatabaseOverview(BaseModel):
    storage_mode: str
    total_analyses: int
    total_verified_facts: int
    total_trusted_sources: int
    total_media_records: int
    topics_breakdown: Dict[str, int]
    sources_breakdown: Dict[str, int]
