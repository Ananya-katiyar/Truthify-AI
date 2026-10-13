"""
Member 2 (NLP / Content Analysis Engineer) owns this file.

Responsibilities:
- Clean raw input text (strip HTML/urls/emojis if needed)
- Split into candidate factual claims for downstream RAG verification

Current version: improved rule-based sentence splitting + filtering.

TODO for Member 2:
- Replace the naive sentence splitter with spaCy or nltk for robustness
- Filter out purely subjective/opinion sentences (e.g. using the tone
  classifier in nlp/classifier.py) so only checkable factual claims go to RAG
- Handle multi-sentence claims and coreference (e.g. "It causes cancer" -> what is "it"?)
"""

import re


def clean_text(text: str) -> str:
    """Remove URLs, excessive whitespace, and basic HTML tags."""
    text = re.sub(r"<[^>]+>", "", text)  # strip HTML tags
    text = re.sub(r"http\S+|www\.\S+", "", text)  # strip URLs
    text = re.sub(r"#\w+", "", text)  # strip hashtags
    text = re.sub(r"@\w+", "", text)  # strip mentions
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> list[str]:
    """Split text into sentences. Handles common abbreviations."""
    # Protect common abbreviations from splitting
    protected = text
    abbrevs = ["Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "Jr.", "Sr.", "Inc.", "Ltd.", "vs.", "etc.", "i.e.", "e.g.", "U.S.", "U.K."]
    for abbr in abbrevs:
        protected = protected.replace(abbr, abbr.replace(".", "<<DOT>>"))

    sentences = re.split(r"(?<=[.!?])\s+", protected)
    # Restore dots
    sentences = [s.replace("<<DOT>>", ".").strip() for s in sentences]
    return [s for s in sentences if len(s.strip()) > 0]


def _is_checkable_claim(sentence: str) -> bool:
    """Filter out sentences that are unlikely to be factual claims."""
    s = sentence.strip()

    # Skip questions
    if s.endswith("?"):
        return False

    # Skip very short fragments
    if len(s.split()) < 4:
        return False

    # Skip purely imperative/exclamatory fragments like "Share this now!"
    imperative_starters = ["share", "click", "subscribe", "follow", "like", "retweet", "rt", "watch"]
    first_word = s.split()[0].lower().strip("!.,")
    if first_word in imperative_starters:
        return False

    return True


def extract_claims(text: str) -> list[str]:
    """Return sentences that look like checkable factual statements."""
    cleaned = clean_text(text)
    sentences = split_sentences(cleaned)
    claims = [s for s in sentences if _is_checkable_claim(s)]
    return claims


if __name__ == "__main__":
    sample = "Doctors say vaccines are dangerous!! I read it on a blog. Visit http://example.com for more. Share this now!"
    print(extract_claims(sample))
