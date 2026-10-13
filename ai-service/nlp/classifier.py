"""
Member 2 (NLP / Content Analysis Engineer) owns this file.

Uses a zero-shot classification pipeline (facebook/bart-large-mnli) when
transformers is installed, and gracefully falls back to linguistic pattern
heuristics if transformers is still downloading or not yet installed.
"""

import logging
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

INTENT_LABELS = ["informative", "manipulative", "satirical", "promotional"]
TONE_LABELS = ["neutral", "emotional", "biased", "alarmist"]
CONTENT_TYPE_LABELS = ["news report", "opinion piece", "propaganda", "personal anecdote"]

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.info("Transformers not yet installed. Using fast heuristic classifier fallback.")


@lru_cache(maxsize=1)
def _get_classifier():
    if not HAS_TRANSFORMERS:
        return None
    logger.info("Loading zero-shot classification model (facebook/bart-large-mnli)...")
    try:
        clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        logger.info("Classification model loaded successfully.")
        return clf
    except Exception as e:
        logger.warning(f"Could not load HuggingFace pipeline ({e}). Will use heuristic analysis.")
        return None


def _classify_heuristic(text: str) -> dict:
    """Fast, accurate heuristic classification based on linguistic cues."""
    lower = text.lower()
    words = set(re.findall(r"\b\w+\b", lower))

    # --- Intent Scoring ---
    manipulative_cues = {
        "secretly", "hiding", "shocking", "urgent", "warning", "exposed", "truth",
        "conspiracy", "banned", "deleted", "wake", "plandemic", "rigged", "agenda",
        "hoax", "poison", "dangerous", "they", "don't", "want", "know"
    }
    promotional_cues = {"buy", "discount", "sale", "order", "limited", "click", "deal", "offer", "shop"}
    satirical_cues = {"satire", "parody", "joke", "spoof", "humor", "onion"}

    manip_score = min(len(words.intersection(manipulative_cues)) * 0.25, 0.95)
    promo_score = min(len(words.intersection(promotional_cues)) * 0.35, 0.95)
    satire_score = min(len(words.intersection(satirical_cues)) * 0.45, 0.95)
    info_score = max(0.1, 1.0 - max(manip_score, promo_score, satire_score))

    intent_scores = {
        "manipulative": round(manip_score, 4),
        "promotional": round(promo_score, 4),
        "satirical": round(satire_score, 4),
        "informative": round(info_score, 4),
    }
    top_intent = max(intent_scores, key=intent_scores.get)

    # --- Tone Scoring ---
    alarmist_cues = {
        "danger", "dangerous", "deadly", "fatal", "crisis", "disaster", "destroy",
        "shocks", "shocked", "shocking", "scandal", "catastrophe", "threat", "emergency"
    }
    biased_cues = {"corrupt", "evil", "tyranny", "liars", "sheep", "clowns", "traitors", "shameful"}
    emotional_cues = {"heartbreaking", "furious", "unbelievable", "disgusted", "amazing", "horrible", "crying"}

    has_caps = bool(re.search(r"\b[A-Z]{3,}\b", text))
    has_excl = "!" in text

    alarm_score = min(len(words.intersection(alarmist_cues)) * 0.3 + (0.2 if has_caps else 0) + (0.15 if has_excl else 0), 0.95)
    bias_score = min(len(words.intersection(biased_cues)) * 0.35, 0.95)
    emot_score = min(len(words.intersection(emotional_cues)) * 0.3, 0.95)
    neut_score = max(0.1, 1.0 - max(alarm_score, bias_score, emot_score))

    tone_scores = {
        "alarmist": round(alarm_score, 4),
        "biased": round(bias_score, 4),
        "emotional": round(emot_score, 4),
        "neutral": round(neut_score, 4),
    }
    top_tone = max(tone_scores, key=tone_scores.get)

    # --- Content Type Scoring ---
    propaganda_score = min((manip_score + alarm_score) / 2.0, 0.95)
    opinion_cues = {"i think", "in my opinion", "i believe", "we feel", "my view", "personally"}
    is_opinion = any(cue in lower for cue in opinion_cues)
    opinion_score = 0.85 if is_opinion else 0.15

    personal_cues = {"my friend", "my doctor", "my cousin", "i heard", "i saw with my own eyes"}
    is_personal = any(cue in lower for cue in personal_cues)
    personal_score = 0.85 if is_personal else 0.15

    news_score = max(0.1, 1.0 - max(propaganda_score, opinion_score, personal_score))

    ct_scores = {
        "propaganda": round(propaganda_score, 4),
        "opinion piece": round(opinion_score, 4),
        "personal anecdote": round(personal_score, 4),
        "news report": round(news_score, 4),
    }
    top_ct = max(ct_scores, key=ct_scores.get)

    return {
        "intent": {"top_label": top_intent, "confidence": intent_scores[top_intent], "scores": intent_scores},
        "tone": {"top_label": top_tone, "confidence": tone_scores[top_tone], "scores": tone_scores},
        "content_type": {"top_label": top_ct, "confidence": ct_scores[top_ct], "scores": ct_scores},
    }


def _classify_transformers(text: str, labels: list[str]) -> dict:
    clf = _get_classifier()
    result = clf(text, candidate_labels=labels, multi_label=False)
    scores = dict(zip(result["labels"], result["scores"]))
    top_label = result["labels"][0]
    confidence = result["scores"][0]
    return {
        "top_label": top_label,
        "confidence": round(confidence, 4),
        "scores": {k: round(v, 4) for k, v in scores.items()},
    }


def analyze_content(text: str) -> dict:
    """Run intent, tone, and content-type classification on the input text."""
    analysis_text = text[:2000] if len(text) > 2000 else text

    # Try transformer model if loaded
    clf = _get_classifier()
    if clf is not None:
        try:
            return {
                "intent": _classify_transformers(analysis_text, INTENT_LABELS),
                "tone": _classify_transformers(analysis_text, TONE_LABELS),
                "content_type": _classify_transformers(analysis_text, CONTENT_TYPE_LABELS),
            }
        except Exception as e:
            logger.warning(f"Transformer inference failed: {e}. Using heuristic fallback.")

    return _classify_heuristic(analysis_text)


if __name__ == "__main__":
    sample = "BREAKING: Scientists SHOCKED as new study proves the government is hiding the truth from you!"
    import json
    print(json.dumps(analyze_content(sample), indent=2))
