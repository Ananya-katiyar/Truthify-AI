"""
Member 3 (RAG & Agentic AI Engineer) owns this file.

This is the "decision" step of the agent workflow: it takes the outputs of
the NLP content analysis (nlp/classifier.py) and the RAG fact-check
(rag/fact_check.py) and produces:
  - a risk_level: "low" | "medium" | "high"
  - a numeric risk_score (0-100)
  - a human-readable explanation

TODO for Member 3:
- Replace the rule-based scoring below with a proper agent (LangGraph/CrewAI)
  that can also decide to re-query the KB, ask for more evidence, or route to
  human review when confidence is low (this is the "agentic" part).
- Tune weights against real examples; log false positives/negatives.
- Use a local LLM (via Ollama or HF `text-generation` pipeline) to turn the
  structured signals below into a more natural-language explanation.
"""

RISK_WEIGHTS = {
    "manipulative_intent": 35,
    "alarmist_or_biased_tone": 20,
    "propaganda_content_type": 20,
    "no_verified_evidence": 25,
}


def score_content(nlp_result: dict, fact_check_results: list[dict]) -> dict:
    score = 0
    reasons = []

    intent = nlp_result["intent"]["top_label"]
    if intent == "manipulative":
        score += RISK_WEIGHTS["manipulative_intent"]
        reasons.append("Content intent classified as manipulative.")

    tone = nlp_result["tone"]["top_label"]
    if tone in ("alarmist", "biased"):
        score += RISK_WEIGHTS["alarmist_or_biased_tone"]
        reasons.append(f"Tone classified as {tone}.")

    content_type = nlp_result["content_type"]["top_label"]
    if content_type == "propaganda":
        score += RISK_WEIGHTS["propaganda_content_type"]
        reasons.append("Content type classified as propaganda.")

    unverified_claims = [r for r in fact_check_results if r["verdict"] == "no_verified_evidence"]
    if fact_check_results and len(unverified_claims) == len(fact_check_results):
        score += RISK_WEIGHTS["no_verified_evidence"]
        reasons.append("No claims could be matched against verified sources.")
    elif unverified_claims:
        partial = RISK_WEIGHTS["no_verified_evidence"] * (len(unverified_claims) / len(fact_check_results))
        score += partial
        reasons.append(f"{len(unverified_claims)}/{len(fact_check_results)} claims lack verified evidence.")

    score = min(round(score), 100)

    if score >= 60:
        risk_level = "high"
    elif score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    if not reasons:
        reasons.append("Content appears consistent with informative, neutral, verifiable reporting.")

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "explanation": reasons,
    }
