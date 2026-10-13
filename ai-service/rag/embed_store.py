"""
Member 1 (Data & Knowledge Base Engineer) owns this file.

Responsibilities:
- Load verified source documents (data/verified_sources/*.json)
- Generates neural embeddings with sentence-transformers if installed,
  or uses an intelligent token/BM25 similarity fallback if dependencies are still downloading.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "verified_sources"
DOCS_PATH = Path(__file__).resolve().parent / "indexed_docs.json"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False
    logger.info("sentence-transformers not yet installed. Using fast keyword-similarity fallback.")

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_docs = None
_embeddings = None


def _get_model():
    global _model
    if not HAS_SENTENCE_TRANSFORMERS:
        return None
    if _model is None:
        try:
            logger.info(f"Loading embedding model: {EMBED_MODEL_NAME}...")
            _model = SentenceTransformer(EMBED_MODEL_NAME)
            logger.info("Embedding model loaded.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using fallback search.")
            return None
    return _model


def load_documents() -> list[dict]:
    """Load all verified-source JSON files from data/verified_sources/."""
    docs = []
    if not DATA_DIR.exists():
        logger.warning(f"Data directory does not exist: {DATA_DIR}")
        return docs

    json_files = list(DATA_DIR.glob("*.json"))
    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    docs.extend(data)
                else:
                    docs.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file}: {e}")
    return docs


def build_index(force_rebuild: bool = False) -> None:
    """Load verified documents and build index."""
    global _docs, _embeddings
    _docs = load_documents()

    model = _get_model()
    if model is not None and HAS_NUMPY and _docs:
        try:
            texts = [d["text"] for d in _docs]
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
            _embeddings = embeddings.astype(np.float32)
            logger.info(f"Neural embeddings ready for {len(_docs)} documents.")
            return
        except Exception as e:
            logger.warning(f"Encoding failed: {e}. Fallback active.")

    logger.info(f"Loaded {len(_docs)} verified facts for similarity search.")


def _keyword_similarity(query: str, doc_text: str) -> float:
    """Calculate token overlap similarity with length normalization."""
    q_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
    d_words = set(re.findall(r"\b\w{3,}\b", doc_text.lower()))

    if not q_words or not d_words:
        return 0.0

    intersection = q_words.intersection(d_words)
    if not intersection:
        return 0.0

    # Jaccard / Overlap coefficient
    overlap = len(intersection) / min(len(q_words), len(d_words))
    jaccard = len(intersection) / len(q_words.union(d_words))
    # Blend overlap and jaccard
    sim = (overlap * 0.6) + (jaccard * 0.4)
    return min(round(sim, 4), 1.0)


def search(query: str, k: int = 3) -> list[dict]:
    """Return top-k most similar verified documents with similarity scores."""
    global _docs, _embeddings
    if _docs is None:
        build_index()

    if not _docs:
        return []

    model = _get_model()
    if model is not None and _embeddings is not None and HAS_NUMPY:
        try:
            q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
            sims = np.dot(_embeddings, q_emb[0])
            top_k_indices = np.argsort(sims)[::-1][:k]
            results = []
            for idx in top_k_indices:
                doc = dict(_docs[idx])
                doc["similarity"] = round(float(sims[idx]), 4)
                results.append(doc)
            return results
        except Exception as e:
            logger.warning(f"Neural search failed: {e}, falling back to keyword search.")

    # High quality keyword overlap similarity
    scored = []
    for doc in _docs:
        sim = _keyword_similarity(query, doc["text"])
        doc_copy = dict(doc)
        doc_copy["similarity"] = sim
        scored.append(doc_copy)

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:k]


if __name__ == "__main__":
    build_index()
    print(f"Loaded {len(_docs)} documents.")
    print(search("vaccines cause autism", k=2))
