"""
Fact-checking module for Truthify-AI.

Verifies claims dynamically against live trusted internet sources
(Reuters Fact Check, AP Fact Check, WHO, CDC, FactCheck.org, Wikipedia, etc.)
and the local verified knowledge store.
"""

import logging
from rag.embed_store import search as search_local_kb
from rag.internet_search import verify_claim_against_internet

logger = logging.getLogger(__name__)


def verify_claim(claim: str, k: int = 3) -> dict:
    """
    Verify a single claim against live internet sources first,
    corroborating with local knowledge base.
    """
    if not claim or not claim.strip():
        return {
            "claim": claim,
            "verdict": "empty_claim",
            "top_similarity": 0.0,
            "evidence": [],
            "source": None,
        }

    # 1. Primary: Live Internet Fact-Checking across trusted sources
    internet_result = None
    try:
        internet_result = verify_claim_against_internet(claim)
    except Exception as e:
        logger.error(f"Live internet verification error for '{claim[:60]}': {e}")

    # 2. Corroborating: Local knowledge base (if available)
    local_evidence = []
    try:
        local_evidence = search_local_kb(claim, k=2)
    except Exception as e:
        logger.warning(f"Local KB search error: {e}")

    # Combine evidence
    combined_evidence = []
    if internet_result and internet_result.get("evidence"):
        combined_evidence.extend(internet_result["evidence"])

    for loc in local_evidence:
        # Avoid duplicate source names
        if not any(e.get("title") == loc.get("text") for e in combined_evidence):
            combined_evidence.append({
                "title": f"Knowledge Base Fact ({loc.get('topic', 'General')})",
                "url": "",
                "domain": "local_kb",
                "source_name": loc.get("source", "Verified KB"),
                "trust_score": round(loc.get("similarity", 0.8), 2),
                "category": "verified_kb",
                "is_trusted": True,
                "snippet": loc.get("text", ""),
                "stance": "contextual_mention"
            })

    if internet_result and internet_result.get("evidence"):
        # Use live internet verdict
        return {
            "claim": claim,
            "verdict": internet_result.get("verdict", "context_found_unverified"),
            "top_similarity": internet_result.get("top_similarity", 0.85),
            "evidence": combined_evidence[:6],
            "source": internet_result.get("source"),
            "top_url": internet_result.get("top_url", ""),
            "confidence": internet_result.get("confidence", 0.75),
            "explanation": internet_result.get("explanation", ""),
            "verification_source": "live_internet",
        }

    # Fallback to local KB only if internet had zero hits
    if local_evidence and local_evidence[0].get("similarity", 0) >= 0.50:
        top_loc = local_evidence[0]
        return {
            "claim": claim,
            "verdict": "supported_or_related",
            "top_similarity": top_loc.get("similarity", 0.0),
            "evidence": combined_evidence[:4],
            "source": top_loc.get("source", "Verified KB"),
            "top_url": "",
            "confidence": 0.65,
            "explanation": f"Matched local verified knowledge entry from {top_loc.get('source', 'KB')}.",
            "verification_source": "local_kb",
        }

    return {
        "claim": claim,
        "verdict": "no_verified_evidence",
        "top_similarity": 0.0,
        "evidence": combined_evidence,
        "source": None,
        "top_url": "",
        "confidence": 0.30,
        "explanation": "No matching reporting found on trusted internet sources or fact-check archives.",
        "verification_source": "none",
    }


def verify_claims(claims: list[str], k: int = 3) -> list[dict]:
    """Verify a list of claims and return results for each."""
    results = []
    for claim in claims:
        result = verify_claim(claim, k=k)
        results.append(result)
    return results
