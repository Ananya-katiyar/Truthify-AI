"""
AI Microservice entrypoint. Exposes the full analysis pipeline (preprocessing
-> NLP analysis -> RAG fact-check -> agentic decision engine) as an HTTP API
that the backend (backend/) calls.

Run:
    cd ai-service
    pip install -r requirements.txt
    python rag/embed_store.py   # builds the FAISS index once
    uvicorn main:app --reload --port 8001
"""

from fastapi import FastAPI
from pydantic import BaseModel

from agent.graph import run_pipeline

app = FastAPI(title="Misinformation Detection AI Service")


class AnalyzeRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return run_pipeline(req.text)
