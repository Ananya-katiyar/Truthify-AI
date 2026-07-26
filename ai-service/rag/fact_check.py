"""
Member 1 & Member 3 share ownership of this file (retrieval = M1, comparison logic = M3).

Takes a list of extracted claims, retrieves the most relevant verified documents
for each, and produces a verdict per claim based on similarity + (optionally) an
LLM-based entailment check.

TODO:
- Replace the similarity-threshold heuristic with a proper NLI (entailment/
  contradiction/neutral) model, e.g. HuggingFace `facebook/bart-large-mnli`,
  for a more reliable "does the evidence support or contradict the claim" check.
- Tune SUPPORT_THRESHOLD / CONTRADICT handling using real labeled examples.
"""

from rag.embed_store import search

SUPPORT_THRESHOLD = 0.55  # cosine similarity above this = likely relevant evidence found
NO_EVIDENCE_THRESHOLD = 0.35  # below this = no relevant verified info exists


def verify_claim(claim: str, k: int = 3) -> dict:
    evidence = search(claim, k=k)
    top_score = evidence[0]["similarity"] if evidence else 0.0

    if top_score >= SUPPORT_THRESHOLD:
        verdict = "supported_or_related"
    elif top_score >= NO_EVIDENCE_THRESHOLD:
        verdict = "weakly_related"
    else:
        verdict = "no_verified_evidence"

    return {
        "claim": claim,
        "verdict": verdict,
        "top_similarity": top_score,
        "evidence": evidence,
    }


def verify_claims(claims: list[str], k: int = 3) -> list[dict]:
    return [verify_claim(c, k=k) for c in claims]
