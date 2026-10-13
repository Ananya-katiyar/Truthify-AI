"""
Decision Engine for Truthify-AI.

Takes the outputs of:
- Multimodal content / NLP analysis (intent, tone, content_type)
- Live internet fact-checking (Reuters, WHO, CDC, Wikipedia, FactCheck.org)
and produces:
- risk_level: "low" | "medium" | "high"
- numeric risk_score (0-100)
- detailed explanations with cited trusted internet sources
- confidence score
- natural-language summary
"""

RISK_WEIGHTS = {
    "debunked_claim": 45,             # Claim directly debunked by trusted internet sources
    "manipulative_intent": 30,
    "alarmist_or_biased_tone": 15,
    "propaganda_content_type": 15,
    "disputed_claim": 20,
    "no_verified_evidence": 20,
}


def _generate_summary(risk_level: str, risk_score: int, reasons: list[str],
                       nlp_result: dict, fact_check_results: list[dict],
                       media_info: dict = None) -> str:
    """Generate a comprehensive natural-language summary with live internet citations."""
    intent = nlp_result.get("intent", {}).get("top_label", "unknown")
    tone = nlp_result.get("tone", {}).get("top_label", "unknown")
    content_type = nlp_result.get("content_type", {}).get("top_label", "unknown")
    num_claims = len(fact_check_results)

    debunked = [r for r in fact_check_results if r.get("verdict") in ("debunked_as_false", "refuted")]
    confirmed = [r for r in fact_check_results if r.get("verdict") in ("confirmed_true", "supported_or_related")]
    disputed = [r for r in fact_check_results if r.get("verdict") == "disputed_or_misleading"]

    # Media prefix
    media_prefix = ""
    if media_info and media_info.get("media_type") not in ("text", None):
        m_type = media_info.get("media_type", "media").upper()
        media_prefix = f"[{m_type} Analysis] "

    if risk_level == "high":
        opening = "This content shows severe indicators of misinformation or deliberate manipulation."
    elif risk_level == "medium":
        opening = "This content shows concerning indicators or unverified claims that warrant caution."
    else:
        opening = "This content appears consistent with verified factual reporting and reliable information."

    analysis = f"Content style: {content_type} with {intent} intent and {tone} tone."

    # Evidence details
    sources_cited = []
    for r in fact_check_results:
        src = r.get("source")
        if src and src not in sources_cited:
            sources_cited.append(src)

    source_text = f" Verified against trusted sources: {', '.join(sources_cited[:3])}." if sources_cited else ""

    if debunked:
        claim_info = f"Critical alert: {len(debunked)} of {num_claims} claim(s) were directly refuted or debunked by independent fact-checkers."
    elif confirmed and len(confirmed) == num_claims:
        claim_info = f"All {num_claims} extracted claim(s) were corroborated by authoritative sources."
    elif confirmed:
        claim_info = f"{len(confirmed)} of {num_claims} claim(s) were verified as accurate, while others remain unverified."
    elif disputed:
        claim_info = f"{len(disputed)} claim(s) are actively disputed or missing essential context."
    elif num_claims > 0:
        claim_info = f"{num_claims} claim(s) could not be verified in public trusted records."
    else:
        claim_info = "No specific factual claims were detected for internet verification."

    return f"{media_prefix}{opening} {analysis} {claim_info}{source_text}"


def score_content(nlp_result: dict, fact_check_results: list[dict], media_info: dict = None) -> dict:
    score = 0
    reasons = []
    confidence_signals = []

    # 1. Fact-Check Scoring (Heaviest Weight based on live internet verification)
    debunked_claims = [r for r in fact_check_results if r.get("verdict") in ("debunked_as_false", "refuted")]
    confirmed_claims = [r for r in fact_check_results if r.get("verdict") in ("confirmed_true", "supported_or_related")]
    disputed_claims = [r for r in fact_check_results if r.get("verdict") == "disputed_or_misleading"]
    unverified_claims = [r for r in fact_check_results if r.get("verdict") == "no_verified_evidence"]

    if debunked_claims:
        score += RISK_WEIGHTS["debunked_claim"]
        for d in debunked_claims[:2]:
            src = d.get("source") or "trusted fact-checkers"
            reasons.append(f"Claim debunked as false: '{d.get('claim', '')[:65]}...' refuted by {src}.")
        confidence_signals.append(0.92)

    if disputed_claims:
        score += RISK_WEIGHTS["disputed_claim"]
        reasons.append(f"{len(disputed_claims)} claim(s) are flagged as disputed or missing context by independent reporting.")
        confidence_signals.append(0.80)

    if unverified_claims and not debunked_claims and not confirmed_claims:
        score += RISK_WEIGHTS["no_verified_evidence"]
        reasons.append("None of the extracted claims could be corroborated by trusted news or fact-check archives.")
        confidence_signals.append(0.60)
    elif unverified_claims and not debunked_claims:
        partial = RISK_WEIGHTS["no_verified_evidence"] * (len(unverified_claims) / max(1, len(fact_check_results)))
        score += partial
        reasons.append(f"{len(unverified_claims)}/{len(fact_check_results)} claim(s) lack independent verification.")
        confidence_signals.append(0.65)

    if confirmed_claims and not debunked_claims:
        if len(confirmed_claims) == len(fact_check_results):
            score = max(0, score - 20)
            reasons.append(f"All claims verified as accurate by trusted sources ({', '.join(set(c.get('source', '') for c in confirmed_claims))}).")
        else:
            score = max(0, score - 10)
            reasons.append(f"{len(confirmed_claims)} claim(s) corroborated by authoritative sources.")
        confidence_signals.append(0.90)

    # 2. Intent Scoring
    intent = nlp_result.get("intent", {}).get("top_label", "unknown")
    intent_conf = nlp_result.get("intent", {}).get("confidence", 0.0)
    if intent == "manipulative":
        score += RISK_WEIGHTS["manipulative_intent"]
        reasons.append("Linguistic analysis detected manipulative intent designed to mislead.")
        confidence_signals.append(intent_conf)
    elif intent != "unknown":
        confidence_signals.append(intent_conf)

    # 3. Tone Scoring
    tone = nlp_result.get("tone", {}).get("top_label", "unknown")
    tone_conf = nlp_result.get("tone", {}).get("confidence", 0.0)
    if tone in ("alarmist", "biased"):
        score += RISK_WEIGHTS["alarmist_or_biased_tone"]
        reasons.append(f"Tone flagged as highly {tone}.")
        confidence_signals.append(tone_conf)
    elif tone != "unknown":
        confidence_signals.append(tone_conf)

    # 4. Content Type Scoring
    content_type = nlp_result.get("content_type", {}).get("top_label", "unknown")
    ct_conf = nlp_result.get("content_type", {}).get("confidence", 0.0)
    if content_type == "propaganda":
        score += RISK_WEIGHTS["propaganda_content_type"]
        reasons.append("Content style is characteristic of political or commercial propaganda.")
        confidence_signals.append(ct_conf)
    elif content_type != "unknown":
        confidence_signals.append(ct_conf)

    # 5. Media Analysis Signals (if media was provided)
    if media_info:
        m_type = media_info.get("media_type")
        if m_type == "pdf":
            pages = media_info.get("metadata", {}).get("pages", 1)
            reasons.append(f"Analyzed {pages}-page PDF document structure and text content.")
        elif m_type == "image":
            ocr_src = media_info.get("ocr_source", "none")
            reasons.append(f"Image inspected (dimensions: {media_info.get('metadata', {}).get('dimensions', 'N/A')}, OCR: {ocr_src}).")
        elif m_type == "video":
            dur = media_info.get("metadata", {}).get("duration_seconds", 0)
            reasons.append(f"Video inspected (duration: {dur}s, on-screen text scanned across keyframes).")

    score = min(max(round(score), 0), 100)

    if score >= 60:
        risk_level = "high"
    elif score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    if not reasons:
        reasons.append("Content appears consistent with informative, verifiable reporting.")

    confidence = round(sum(confidence_signals) / len(confidence_signals), 4) if confidence_signals else 0.5

    summary = _generate_summary(risk_level, score, reasons, nlp_result, fact_check_results, media_info)

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "explanation": reasons,
        "confidence": confidence,
        "summary": summary,
    }
