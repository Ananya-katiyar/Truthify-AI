"""
Backend entrypoint. This is the API the React frontend talks to. It in turn
calls the AI microservice (ai-service/) for analysis.

Run:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import alerts, content

app = FastAPI(title="Misinformation Detection Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(content.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}
