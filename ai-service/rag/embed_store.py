"""
Member 1 (Data & Knowledge Base Engineer) owns this file.

Responsibilities:
- Load verified source documents (currently from data/verified_sources/*.json)
- Generate embeddings using a local sentence-transformers model (no API key needed)
- Build and persist a FAISS index for fast similarity search
- Expose a simple `search(query, k)` function used by rag/fact_check.py

TODO for Member 1:
- Replace sample_facts.json with real data pulled from news APIs / fact-check DBs
  (see knowledge_base.py for the ingestion pipeline to extend)
- Add periodic re-indexing (cron / scheduled task) so the KB stays current
- Consider chunking long articles before embedding (see docs/architecture.md)
"""

import json
import os
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "verified_sources"
INDEX_PATH = Path(__file__).resolve().parent / "faiss_index.bin"
DOCS_PATH = Path(__file__).resolve().parent / "indexed_docs.json"

# Small, fast, fully open-source embedding model (~80MB, runs on CPU)
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_index = None
_docs = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def load_documents() -> list[dict]:
    """Load all verified-source JSON files from data/verified_sources/."""
    docs = []
    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            docs.extend(json.load(f))
    return docs


def build_index(force_rebuild: bool = False) -> None:
    """Build (or load cached) FAISS index from verified documents."""
    global _index, _docs

    if not force_rebuild and INDEX_PATH.exists() and DOCS_PATH.exists():
        _index = faiss.read_index(str(INDEX_PATH))
        with open(DOCS_PATH, "r", encoding="utf-8") as f:
            _docs = json.load(f)
        return

    _docs = load_documents()
    if not _docs:
        raise ValueError(f"No verified source documents found in {DATA_DIR}")

    model = _get_model()
    texts = [d["text"] for d in _docs]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    _index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine similarity
    _index.add(embeddings.astype(np.float32))

    faiss.write_index(_index, str(INDEX_PATH))
    with open(DOCS_PATH, "w", encoding="utf-8") as f:
        json.dump(_docs, f)


def search(query: str, k: int = 3) -> list[dict]:
    """Return top-k most similar verified documents with similarity scores."""
    global _index, _docs
    if _index is None or _docs is None:
        build_index()

    model = _get_model()
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
    scores, indices = _index.search(q_emb, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        doc = dict(_docs[idx])
        doc["similarity"] = float(score)
        results.append(doc)
    return results


if __name__ == "__main__":
    build_index(force_rebuild=True)
    print(f"Indexed {len(_docs)} documents.")
    print(search("Do vaccines get tested before release?", k=2))
