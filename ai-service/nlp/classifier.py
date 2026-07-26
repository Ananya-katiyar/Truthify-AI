"""
Member 2 (NLP / Content Analysis Engineer) owns this file.

Uses a zero-shot classification pipeline (facebook/bart-large-mnli, open-source,
no API key) so you don't need to fine-tune a model to get started. This can
later be swapped for a fine-tuned BERT/RoBERTa classifier once you have
labeled training data.

TODO for Member 2:
- Collect/label a dataset of misinformation vs. legitimate content to fine-tune
  a dedicated classifier (better accuracy than zero-shot)
- Add a bias-detection dimension (e.g. left/right/neutral framing)
- Cache the pipeline object across requests (already done via module-level singleton)
"""

from functools import lru_cache

from transformers import pipeline

INTENT_LABELS = ["informative", "manipulative", "satirical", "promotional"]
TONE_LABELS = ["neutral", "emotional", "biased", "alarmist"]
CONTENT_TYPE_LABELS = ["news report", "opinion piece", "propaganda", "personal anecdote"]


@lru_cache(maxsize=1)
def _get_classifier():
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def _classify(text: str, labels: list[str]) -> dict:
    clf = _get_classifier()
    result = clf(text, candidate_labels=labels, multi_label=False)
    return {"top_label": result["labels"][0], "scores": dict(zip(result["labels"], result["scores"]))}


def analyze_content(text: str) -> dict:
    """Run intent, tone, and content-type classification on the input text."""
    return {
        "intent": _classify(text, INTENT_LABELS),
        "tone": _classify(text, TONE_LABELS),
        "content_type": _classify(text, CONTENT_TYPE_LABELS),
    }


if __name__ == "__main__":
    sample = "BREAKING: Scientists SHOCKED as new study proves the government is hiding the truth from you!"
    import json
    print(json.dumps(analyze_content(sample), indent=2))
