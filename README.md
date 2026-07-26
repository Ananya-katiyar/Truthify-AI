# AI-Based Misinformation Detection and Risk Analysis System

A RAG + Agentic AI system that analyzes text content (social posts, articles),
fact-checks claims against a verified knowledge base, and produces a risk
score with an explanation. See `docs/architecture.md` for the full data flow
and team task breakdown.

## Project Structure

```
misinfo-system/
├── frontend/       React dashboard (Member 5)
├── backend/        FastAPI API layer + MongoDB (Member 4)
├── ai-service/      Python AI microservice (Members 1, 2, 3)
│   ├── preprocessing/   claim extraction (Member 2)
│   ├── nlp/              intent/tone/type classification (Member 2)
│   ├── rag/               FAISS vector store + fact-checking (Members 1 & 3)
│   ├── agent/             risk scoring + orchestration (Member 3)
│   └── data/verified_sources/   sample verified knowledge base (Member 1)
├── docs/            architecture notes
└── docker-compose.yml
```

## Quick Start (running everything locally, no Docker)

### 1. AI Microservice (start this first — it's the core)
```bash
cd ai-service
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python rag/embed_store.py        # builds the FAISS index from sample data
uvicorn main:app --reload --port 8001
```
Test it: `curl -X POST http://localhost:8001/analyze -H "Content-Type: application/json" -d '{"text": "Scientists SHOCKED as vaccines proven dangerous!"}'`

### 2. MongoDB
Easiest: `docker run -d -p 27017:27017 mongo:7`
(Or install MongoDB locally, or use MongoDB Atlas free tier and set `MONGO_URI` in `.env`.)

### 3. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Quick Start (Docker, backend + ai-service + mongo only)
```bash
docker compose up --build
```
Then run the frontend separately with `npm run dev` (Vite hot-reload works better outside Docker during development).

## Current Model Choices (all open-source, no API keys required)

- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (fast, ~80MB, CPU-friendly)
- **Vector store:** FAISS (local, in-process)
- **Classification:** `facebook/bart-large-mnli` zero-shot pipeline via HuggingFace `transformers`
- **Explanation generation:** currently rule-based (see `agent/decision_engine.py`); can be
  upgraded to a local LLM via Ollama or a HF `text-generation` pipeline

## Next Steps for the Team

1. Everyone: clone the repo, get your own service running locally using the Quick Start above.
2. Member 1: replace `data/verified_sources/sample_facts.json` with real scraped/API-sourced data.
3. Member 2: swap the naive sentence splitter for spaCy; consider fine-tuning a classifier.
4. Member 3: port `agent/graph.py` into an actual LangGraph `StateGraph`.
5. Member 4: add auth, pagination, and real alert notifications.
6. Member 5: polish the UI, add loading states, add charts (e.g. risk trends over time).
7. Member 6: set up CI, deploy to a cloud provider, write the final report/demo.

See `docs/architecture.md` for full details and the task/file ownership table.
