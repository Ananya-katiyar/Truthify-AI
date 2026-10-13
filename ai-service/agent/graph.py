"""
Agentic Analysis Pipeline for Truthify-AI.

Orchestrates:
1. Media Extraction (PDF, Image, Video, Text)
2. Claim Extraction
3. NLP Intent/Tone/Bias Analysis
4. Live Internet Fact-Checking across trusted sources
5. Agentic Risk Scoring & Decision Engine
"""

import logging
import time

from preprocessing.claim_extraction import extract_claims
from nlp.classifier import analyze_content
from rag.fact_check import verify_claims
from agent.decision_engine import score_content

logger = logging.getLogger(__name__)


def run_pipeline(text: str, media_info: dict = None) -> dict:
    """Runs the full analysis pipeline on content (text or multimodal extraction)."""
    start = time.time()
    errors = []

    # If text is empty but media_info provided extracted_text
    effective_text = text
    if not effective_text.strip() and media_info:
        effective_text = media_info.get("extracted_text", "")

    # Stage 1: Claim extraction
    try:
        claims = extract_claims(effective_text) if effective_text.strip() else []
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}", exc_info=True)
        claims = []
        errors.append(f"Claim extraction error: {str(e)}")

    # Stage 2: NLP content analysis
    try:
        nlp_result = analyze_content(effective_text) if effective_text.strip() else {
            "intent": {"top_label": "neutral", "scores": {}, "confidence": 0.5},
            "tone": {"top_label": "neutral", "scores": {}, "confidence": 0.5},
            "content_type": {"top_label": "document", "scores": {}, "confidence": 0.5},
        }
    except Exception as e:
        logger.error(f"NLP analysis failed: {e}", exc_info=True)
        nlp_result = {
            "intent": {"top_label": "unknown", "scores": {}, "confidence": 0.0},
            "tone": {"top_label": "unknown", "scores": {}, "confidence": 0.0},
            "content_type": {"top_label": "unknown", "scores": {}, "confidence": 0.0},
        }
        errors.append(f"NLP analysis error: {str(e)}")

    # Stage 3: Live Internet & Knowledge Base fact-check
    try:
        fact_check_results = verify_claims(claims) if claims else []
    except Exception as e:
        logger.error(f"Fact-check failed: {e}", exc_info=True)
        fact_check_results = []
        errors.append(f"Fact-check error: {str(e)}")

    # Stage 4: Decision engine
    try:
        decision = score_content(nlp_result, fact_check_results, media_info=media_info)
    except Exception as e:
        logger.error(f"Decision engine failed: {e}", exc_info=True)
        decision = {
            "risk_score": 0,
            "risk_level": "unknown",
            "explanation": ["Analysis could not be completed due to an internal error."],
            "confidence": 0.0,
            "summary": "Analysis failed.",
        }
        errors.append(f"Decision engine error: {str(e)}")

    elapsed = round(time.time() - start, 2)

    # Collect unique internet sources queried
    all_internet_sources = []
    seen_domains = set()
    for fc in fact_check_results:
        for ev in fc.get("evidence", []):
            dom = ev.get("domain", "")
            if dom and dom not in seen_domains:
                seen_domains.add(dom)
                all_internet_sources.append({
                    "name": ev.get("source_name", dom),
                    "domain": dom,
                    "trust_score": ev.get("trust_score", 0.8),
                    "category": ev.get("category", "general"),
                    "is_trusted": ev.get("is_trusted", False),
                    "url": ev.get("url", ""),
                })

    result = {
        "input_text": effective_text,
        "extracted_claims": claims,
        "content_analysis": nlp_result,
        "fact_check": fact_check_results,
        "risk_score": decision["risk_score"],
        "risk_level": decision["risk_level"],
        "explanation": decision["explanation"],
        "confidence": decision.get("confidence", 0.0),
        "summary": decision.get("summary", ""),
        "processing_time_seconds": elapsed,
        "media_info": media_info or {
            "media_type": "text",
            "filename": "",
            "metadata": {},
            "thumbnail_b64": ""
        },
        "internet_sources_queried": all_internet_sources,
    }

    if errors:
        result["warnings"] = errors

    logger.info(f"Pipeline completed in {elapsed}s — risk={decision['risk_level']} score={decision['risk_score']}")
    return result


if __name__ == "__main__":
    import json
    sample = "BREAKING: Scientists confirm vaccines cause autism and inject microchips to track citizens."
    print(json.dumps(run_pipeline(sample), indent=2))
