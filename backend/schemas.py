from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ContentSubmission(BaseModel):
    text: str
    source_type: str = Field(default="user_submitted", description="social_media | news_article | user_submitted")
    submitted_by: Optional[str] = None


class AnalysisResult(BaseModel):
    content_id: str
    input_text: str
    extracted_claims: list[str]
    content_analysis: dict
    fact_check: list[dict]
    risk_score: int
    risk_level: str
    explanation: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    reviewer_notes: Optional[str] = None


class FeedbackSubmission(BaseModel):
    content_id: str
    correct_risk_level: str
    notes: Optional[str] = None
