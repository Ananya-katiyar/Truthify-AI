# Architecture

```
React Frontend (5173)
        |
        v
FastAPI Backend (8000)  <---->  MongoDB (27017)
        |
        v
AI Microservice (8001)
   |         |          |
   v         v          v
Preprocess  NLP        RAG (FAISS + sentence-transformers)
(claims)   (intent/     |
            tone/       v
            type)   Agent Decision Engine
                     (risk score + explanation)
```

## Request flow (single content submission)

1. User pastes text into the frontend `SubmitContent` form.
2. Frontend calls `POST /content/submit` on the backend.
3. Backend forwards the raw text to the AI microservice: `POST /analyze`.
4. AI microservice runs `agent/graph.py::run_pipeline`:
   a. `preprocessing/claim_extraction.py` splits text into candidate claims.
   b. `nlp/classifier.py` classifies intent / tone / content type (zero-shot, open-source model).
   c. `rag/fact_check.py` retrieves top-k similar verified documents per claim from the FAISS index
      (built by `rag/embed_store.py` from `data/verified_sources/*.json`).
   d. `agent/decision_engine.py` combines all signals into a risk score (0-100), risk level
      (low/medium/high), and a list of explanation strings.
5. Backend stores the full result in MongoDB (`analyses` collection) and returns it to the frontend.
6. If `risk_level == "high"`, the item shows up in `GET /alerts/`, surfaced in the frontend's
   `AlertsPanel` for human review (human-in-the-loop step).

## Where each team member plugs in

| Member | Files |
|---|---|
| 1 - Data & KB | `ai-service/data/verified_sources/`, `ai-service/rag/embed_store.py` |
| 2 - NLP | `ai-service/preprocessing/claim_extraction.py`, `ai-service/nlp/classifier.py` |
| 3 - RAG & Agent | `ai-service/rag/fact_check.py`, `ai-service/agent/decision_engine.py`, `ai-service/agent/graph.py` |
| 4 - Backend | `backend/` (all files) |
| 5 - Frontend | `frontend/` (all files) |
| 6 - Integration/DevOps | `docker-compose.yml`, Dockerfiles, `docs/`, deployment |

## Key upgrade paths (once the skeleton works end-to-end)

- Swap `agent/graph.py`'s sequential function calls for a real **LangGraph** `StateGraph` with
  conditional edges (e.g., re-retrieve with a rephrased query if similarity is low).
- Swap the zero-shot classifier in `nlp/classifier.py` for a fine-tuned BERT/RoBERTa model once
  you have labeled data.
- Swap `rag/fact_check.py`'s similarity-threshold heuristic for a proper NLI (entailment) model.
- Add a local LLM (via Ollama, or HF `text-generation` pipeline) to turn the structured explanation
  reasons into a natural-language paragraph.
- Move from MongoDB to PostgreSQL if the team prefers relational data + easier analytics queries.
