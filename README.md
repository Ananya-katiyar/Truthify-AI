# Truthify-AI 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite)](https://vitejs.dev)

> **Autonomous Multimodal Misinformation Detection, Live Internet Fact-Checking & Self-Expanding Knowledge Base**

Truthify-AI evaluates news headlines, social media posts, articles, **Images**, **Videos**, and **PDF documents** to detect misinformation, unmask manipulative framing, verify claims against real-time trusted internet sources (Reuters, WHO, CDC, Snopes, FactCheck.org, Wikipedia), and dynamically expand its own verified intelligence repository.

---

## 🌟 Key Highlights

- 🖼️ **Multimodal Inputs**: Accepts raw text, **Images** (`.png`, `.jpg`, `.webp`), **Videos** (`.mp4`, `.mov`, `.webm`), and **PDF Documents** (`.pdf`). Automatically extracts text using OCR, scans video banners/keyframes, and parses multi-page documents.
- 🌐 **No Hardcoded Facts — Live Internet Grounding**: Queries live trusted internet sources in real time via DuckDuckGo and Wikipedia REST APIs, plus Google Fact Check Tools.
- 🏛️ **Certified Trusted Sources**: Cross-checks claims against certified IFCN fact-checkers (**Reuters Fact Check**, **AP Fact Check**, **FactCheck.org**, **Snopes**, **PolitiFact**, **AFP**) and global health/science authorities (**WHO**, **CDC**, **NASA**, **Nature**).
- 🧠 **Automated Stance & Verdict Engine**: Analyzes whether external reporting **refutes**, **confirms**, or **disputes** claims, providing clickable source links (`View Source Link ↗`).
- 📈 **Self-Expanding Database**: Conclusive findings from live web searches are automatically cached and ingested into the database, expanding the system's verified intelligence with every query.
- ⚖️ **Explainable Risk Scoring (0–100)**: Combines intent analysis (informative vs. manipulative), tone/bias detection, and live evidence checks into an explainable verdict (Low / Medium / High Risk).
- 🗄️ **Knowledge & Database Hub**: Interactive UI tab to explore, filter, add, and curate verified facts and manage trusted domains.
- 🔔 **Alerts & Human-in-the-Loop Review**: Surfaces high-risk alerts for operator review and feedback.

---

## 🏗️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Truthify-AI Web Studio                          │
│        (React 18 + Vite + Modern Glassmorphic Dark-Mode UI)            │
│   [Detection Studio]  [Database & Sources Hub]  [Feed]  [Alerts]       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / Multipart Uploads
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend Service (:8000)                    │
│   • /content/submit-media (Files)     • /database/facts (CRUD)         │
│   • /content/submit (Text)            • /database/sources (Directory)  │
│   • /alerts (High-risk triage)        • /uploads (Static media preview)│
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │ REST Proxy                    │ Persist & Query
                    ▼                               ▼
┌───────────────────────────────────┐    ┌───────────────────────────────┐
│     AI Microservice (:8001)       │    │      Persistent Storage       │
│                                   │    │  (MongoDB or JSON Data Store) │
│ 1. Multimodal Extractor           │    │  • analyses                   │
│    (PDFs, Image OCR, Video Frames)│    │  • verified_facts             │
│ 2. Claim Extraction Engine        │    │  • trusted_sources            │
│ 3. Zero-Shot NLP Classifier       │    │  • media_records              │
│    (Intent, Tone, Propaganda)     │    └───────────────────────────────┘
│ 4. Live Internet Fact-Checker     │
│    (DDG, Wikipedia, IFCN checks)  │
│ 5. Agentic Decision Engine        │
└─────────────────┬─────────────────┘
                  │ Live Web Queries
                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Trusted Internet Sources                          │
│  • Reuters Fact Check  • WHO & CDC            • Snopes & PolitiFact    │
│  • AP Fact Check       • Wikipedia REST API   • FactCheck.org & AFP    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Custom CSS (Glassmorphism, Dark Mode tokens) |
| **Backend API** | FastAPI, Pydantic v2, Motor (MongoDB driver), HTTPX |
| **AI Microservice** | FastAPI, Sentence-Transformers, HuggingFace Transformers, PyPDF, Pillow, OpenCV |
| **Search & Fact-Checking** | Real-Time DuckDuckGo Parser, Wikipedia REST API, Google Fact Check API |
| **Database** | MongoDB (Production) with auto-switching local persistent JSON storage |
| **Optional LLM Enhancements** | Google Gemini API (Multimodal Vision), Groq API |

---

## 📂 Project Directory Structure

```text
misinfo-system/
├── ai-service/
│   ├── agent/
│   │   ├── decision_engine.py      # Risk scoring, stance weighting, and explanations
│   │   └── graph.py                # Sequential agentic execution pipeline
│   ├── data/
│   │   ├── cache/                  # Live internet search cache
│   │   └── verified_sources/       # Initial knowledge base seeds
│   ├── nlp/
│   │   └── classifier.py           # Zero-shot intent, tone, and propaganda classification
│   ├── preprocessing/
│   │   ├── claim_extraction.py     # Rule-based and NLP claim extractor
│   │   └── multimodal.py           # PDF parsing, image OCR/EXIF, video frame extraction
│   ├── rag/
│   │   ├── embed_store.py          # Neural embeddings & vector similarity
│   │   ├── fact_check.py           # Fact verification router
│   │   └── internet_search.py      # Real-time web fact-checking (Reuters, WHO, Wikipedia)
│   ├── main.py                     # AI microservice entrypoint (:8001)
│   └── requirements.txt
├── backend/
│   ├── routes/
│   │   ├── alerts.py               # High-risk alert management & human review
│   │   ├── content.py              # Text & multimodal submissions, auto-fact ingestion
│   │   └── database.py             # Verified facts & trusted sources CRUD
│   ├── database.py                 # Hybrid storage (MongoDB + Persistent file store)
│   ├── schemas.py                  # Pydantic data schemas
│   ├── main.py                     # Backend API entrypoint (:8000)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.js           # API client for backend communication
│   │   ├── components/
│   │   │   ├── AlertsPanel.jsx     # High-risk alert review panel
│   │   │   ├── Dashboard.jsx       # Feed, inspection modal & media badges
│   │   │   ├── DatabaseHub.jsx     # Dynamic facts & trusted sources explorer
│   │   │   └── SubmitContent.jsx   # Multimodal upload & live detection studio
│   │   ├── App.jsx                 # Main layout & navigation
│   │   └── index.css               # Design system & responsive styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── .env
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- *(Optional)* **Docker & Docker Compose** for containerized execution.

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ananya-katiyar/Truthify-AI.git
cd Truthify-AI
```

---

### Step 2: Configure Environment Variables

Create or review `.env` in the root directory:

```env
# Backend & AI Service
MONGO_URI=mongodb://localhost:27017
DB_NAME=misinfo_system
AI_SERVICE_URL=http://localhost:8001
VITE_BACKEND_URL=http://localhost:8000

# Optional Enhancements (Internet search works out-of-the-box without keys!)
# GEMINI_API_KEY=your_gemini_api_key_here
# GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_api_key_here
# GROQ_API_KEY=your_groq_api_key_here
```

---

### Step 3: Run Locally (Recommended)

Open 3 terminal windows:

#### Terminal 1 — AI Microservice
```powershell
cd ai-service
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload
```
*Health check:* `http://localhost:8001/health`

#### Terminal 2 — Backend API
```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```
*API documentation:* `http://localhost:8000/docs`

#### Terminal 3 — Frontend Web App
```powershell
cd frontend
npm install
npm run dev
```
*Open in browser:* `http://localhost:5173`

---

### Step 4: Run with Docker Compose (Alternative)

```bash
docker compose up --build
```
This spins up MongoDB, the AI microservice, the FastAPI backend, and the Vite React frontend simultaneously.

---

## 📡 API Reference

### Multimodal & Content Analysis
- `POST /content/submit` — Submit text/articles for analysis.
- `POST /content/submit-media` — Multipart upload for **Images**, **Videos**, or **PDFs**.
- `GET /content/` — List all analyzed items with optional risk-level filter.
- `GET /content/{content_id}` — Get single analysis report.
- `GET /content/stats` — Summary metrics (total evaluated, risk distribution).
- `POST /content/{content_id}/feedback` — Submit human-in-the-loop corrections.

### Knowledge Base & Database Hub
- `GET /database/overview` — Collection record counts and topic breakdowns.
- `GET /database/facts` — Search & filter verified facts by topic and verdict.
- `POST /database/facts` — Manually add a verified fact to expand the database.
- `DELETE /database/facts/{fact_id}` — Remove a fact from the database.
- `GET /database/sources` — List trusted internet domains with reputation ratings.
- `POST /database/sources` — Register a new trusted domain.
- `DELETE /database/sources/{domain}` — Remove a domain from trusted sources.

### High-Risk Alerts
- `GET /alerts/` — Fetch unreviewed high-risk misinformation alerts.
- `POST /alerts/{content_id}/review` — Mark an alert as reviewed by an operator.

---

## 🔍 How Live Fact Verification Works

1. **Extraction**: The input (text or uploaded media) is parsed to isolate testable factual claims.
2. **Multi-Source Real-Time Search**:
   - Queries certified fact-check archives and news wires via DuckDuckGo.
   - Queries Wikipedia's REST API for neutral encyclopedic summaries.
   - Queries Google Fact Check Tools API when enabled.
3. **Stance Analysis**: Compares the claim against evidence snippets using linguistic signals (`refutes`, `supports`, `disputed`).
4. **Agent Scoring**: Debunked claims incur high risk penalties; corroborated claims reduce risk.
5. **Continuous Learning**: High-confidence findings are auto-ingested into the local database, permanently expanding the knowledge repository.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Commit your changes: `git commit -m 'Add amazing feature'`.
4. Push to the branch: `git push origin feature/amazing-feature`.
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).