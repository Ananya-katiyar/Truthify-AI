## Truthify-AI

**AI-Based Misinformation Detection and Risk Analysis System using RAG and Agentic AI**

Truthify-AI analyzes news articles, social media posts, and user-submitted content to detect misinformation, assess intent and bias, verify claims against trusted sources, and assign explainable risk scores — helping flag misleading or harmful content before it spreads.

---

## Problem Statement

- Rapid spread of fake news and misinformation
- AI-generated propaganda influencing public opinion
- Difficulty verifying the authenticity of information
- Lack of real-time tools to detect misleading or harmful content
- Potential risks to national security, elections, and public trust

## Proposed Solution

Truthify-AI is an AI-powered system that:

- Accepts input from social media posts, news articles, and user-submitted content
- Uses **Generative AI** to analyze intent, tone, and bias
- Uses **RAG (Retrieval-Augmented Generation)** to verify claims against trusted, verified sources
- Uses **Agentic AI** to reason over evidence, assign risk levels, and generate explanations
- Surfaces risk scores, supporting evidence, and alerts for high-risk content via a dashboard

## Key Features

- Intent and tone detection (informative vs. manipulative)
- Fact-checking using RAG with verified knowledge sources
- Risk-based classification (Low / Medium / High)
- Explainable AI — reasoning and supporting evidence for every verdict
- Dashboard for monitoring flagged content
- Alert system for high-risk misinformation
- Human-in-the-loop validation for critical decisions

---

## System Architecture
```
┌─────────────┐      ┌──────────────┐       ┌────────────────────┐
│ Frontend    │ ───▶│ Backend       | ───▶ │ AI Microservice    │
│ (React)     │ ◀───│ (FastAPI)     │ ◀─── │ (Python)           │
└─────────────┘      └──────────────┘       └────────────────────┘
                          │ │
                          ▼ ▼
            ┌─────────────┐ ┌───────────────┐
            │ PostgreSQL  │ │ ChromaDB      │
            │ (content,   │ │(vector store, │
            │ scores,     │ │verified facts)│
            │ history)    │ └───────────────┘
            └─────────────┘
```
**Flow:** Content submitted → preprocessing & claim extraction → intent/tone/bias classification → RAG retrieval & fact comparison → agentic decision engine (risk scoring + explanation) → stored & surfaced on dashboard, with alerts for high-risk content.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend API | FastAPI (Python) |
| Database | PostgreSQL |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Classification (intent/tone/bias) | HuggingFace Transformers (RoBERTa fine-tunes) |
| LLM (RAG comparison + explanations) | Groq API (Llama 3.3 / 4) |
| RAG Orchestration | LangChain |
| Agent Framework | LangGraph |
| Containerization | Docker + docker-compose |
| CI/CD | GitHub Actions |
| Deployment | Render (backend + PostgreSQL), Vercel (frontend) |

---

## Project Structure
```
misinfo-system/
├── ai-service/
│ ├── agent/ # Agentic decision engine (LangGraph)
│ │ ├── decision_engine.py
│ │ └── graph.py
│ ├── data/
│ │ └── verified_sources/ # Trusted fact/knowledge data
│ ├── nlp/ # Intent/tone/bias classification
│ │ └── classifier.py
│ ├── preprocessing/ # Claim extraction
│ │ └── claim_extraction.py
│ ├── rag/ # Retrieval + fact verification
│ │ ├── embed_store.py
│ │ └── fact_check.py
│ ├── main.py
│ ├── requirements.txt
│ └── Dockerfile
├── backend/
│ ├── routes/
│ │ ├── alerts.py
│ │ └── content.py
│ ├── database.py
│ ├── schemas.py
│ ├── main.py
│ ├── requirements.txt
│ └── Dockerfile
├── frontend/
│ ├── src/
│ │ ├── api/client.js
│ │ ├── components/
│ │ │ ├── AlertsPanel.jsx
│ │ │ ├── Dashboard.jsx
│ │ │ └── SubmitContent.jsx
│ │ ├── App.jsx
│ │ └── main.jsx
│ ├── index.html
│ ├── package.json
│ └── vite.config.js
├── docs/
│ └── architecture.md
├── docker-compose.yml
└── README.md
```
---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (recommended)
- A free Groq API key (https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/Ananya-katiyar/Truthify-AI.git
cd Truthify-AI
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/truthify
GROQ_API_KEY=your_groq_api_key_here
CHROMA_PERSIST_DIR=./ai-service/data/chroma
```

### 3. Run with Docker

```bash
docker-compose up --build
```

This spins up the frontend, backend, AI microservice, and PostgreSQL together.

### 4. Or run services individually

**AI Service**
```bash
cd ai-service
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## Module Overview

| Module | Responsibility |
|---|---|
| Data & Knowledge Base | Collects verified data (news APIs, fact-check DBs, govt sources) and builds the embedding-based vector store |
| NLP / Content Analysis | Extracts claims from raw text and classifies intent, tone, bias, and content type |
| RAG & Agentic AI | Retrieves relevant facts, compares against claims, and runs the agentic workflow to score risk and generate explanations |
| Backend API | Connects frontend, AI microservice, and database; handles alerts and notifications |
| Frontend Dashboard | Content submission, results display, flagged-content monitoring, and human-in-the-loop review |
| Integration & DevOps | End-to-end testing, deployment, CI/CD, and documentation |

---

## Roadmap
```
- [x] Phase 0 — Setup & planning
- [x] Phase 1 — Data & knowledge base ingestion pipeline
- [ ] Phase 2 — Core AI modules (claim extraction, classification, RAG retrieval)
- [ ] Phase 3 — Agentic decision engine (risk scoring + explanations)
- [ ] Phase 4 — Backend API
- [ ] Phase 5 — Frontend dashboard
- [ ] Phase 6 — Integration & testing
- [ ] Phase 7 — Deployment & polish

```
---

## Contributors

| Role | Focus Area |
|---|---|
| Data & Knowledge Base Engineer | Verified data pipeline, embeddings, vector store |
| NLP / Content Analysis Engineer | Claim extraction, intent/tone/bias classification |
| RAG & Agentic AI Engineer | Fact verification, agentic decision engine, risk scoring |
| Backend Engineer | API layer, database schema, alerts |
| Frontend Engineer | Dashboard, alerts UI, review interface |
| Integration, DevOps & Documentation Lead | Testing, deployment, CI/CD, docs |

---

## License

This project is licensed under the MIT License.

---