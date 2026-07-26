"""
Member 2 (NLP / Content Analysis Engineer) owns this file.

Responsibilities:
- Clean raw input text (strip HTML/urls/emojis if needed)
- Split into candidate factual claims for downstream RAG verification

Current version: simple rule-based sentence splitting + basic filtering.

TODO for Member 2:
- Replace the naive sentence splitter with spaCy or nltk for robustness
- Filter out purely subjective/opinion sentences (e.g. using the tone
  classifier in nlp/classifier.py) so only checkable factual claims go to RAG
- Handle multi-sentence claims and coreference (e.g. "It causes cancer" -> what is "it"?)
"""

import re


def clean_text(text: str) -> str:
    text = re.sub(r"http\S+|www\.\S+", "", text)  # strip URLs
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> list[str]:
    # naive splitter; swap for spaCy/nltk for production use
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]


def extract_claims(text: str, min_words: int = 4) -> list[str]:
    """Return sentences that look like checkable factual statements."""
    cleaned = clean_text(text)
    sentences = split_sentences(cleaned)
    claims = [s for s in sentences if len(s.split()) >= min_words]
    return claims


if __name__ == "__main__":
    sample = "Doctors say vaccines are dangerous!! I read it on a blog. Visit http://example.com for more."
    print(extract_claims(sample))
