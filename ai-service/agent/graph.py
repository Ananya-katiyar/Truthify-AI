"""
Member 3 (RAG & Agentic AI Engineer) owns this file.

This is a simple SEQUENTIAL stand-in for a real agent graph. It exists so the
whole pipeline runs end-to-end today. Swap this out for an actual LangGraph
StateGraph or CrewAI Crew once you're ready to add agentic behavior like:
  - conditional branching (e.g. re-retrieve with a rephrased query if
    similarity is too low)
  - multi-agent debate (a "skeptic" agent challenges the "verifier" agent)
  - tool use (e.g. calling a live news API instead of only the static KB)

TODO for Member 3:
- Port this into LangGraph: each function below becomes a node, edges define
  the flow, and you can add conditional edges for re-querying / escalation.
"""

from preprocessing.claim_extraction import extract_claims
from nlp.classifier import analyze_content
from rag.fact_check import verify_claims
from agent.decision_engine import score_content


def run_pipeline(text: str) -> dict:
    """Runs the full analysis pipeline on a single piece of content."""
    claims = extract_claims(text)
    nlp_result = analyze_content(text)
    fact_check_results = verify_claims(claims) if claims else []
    decision = score_content(nlp_result, fact_check_results)

    return {
        "input_text": text,
        "extracted_claims": claims,
        "content_analysis": nlp_result,
        "fact_check": fact_check_results,
        "risk_score": decision["risk_score"],
        "risk_level": decision["risk_level"],
        "explanation": decision["explanation"],
    }


if __name__ == "__main__":
    import json
    sample = "BREAKING: Scientists SHOCKED as new study proves vaccines are secretly dangerous and the government is hiding it!"
    print(json.dumps(run_pipeline(sample), indent=2))
