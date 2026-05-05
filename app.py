"""FastAPI backend for CareerLensAI.

Run locally:
    uvicorn app:app --reload

Primary endpoint:
    POST /analyze/resume
    Accepts one of: PDF upload, raw_text form field, or JSON body.
"""

from __future__ import annotations

import tempfile
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from modules.chatbot import chat_with_resume
from modules.description_generator import generate_job_description
from modules.job_prediction import predict_top_roles
from modules.recommendations import build_recommendations
from modules.resume_parser import parse_resume
from modules.resume_score import score_resume
from modules.skill_gap import analyze_skill_gap


try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

app = FastAPI(
    title="CareerLensAI Backend",
    description="AI-powered resume parsing, role prediction, skill-gap analysis, scoring, and recommendations.",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/demo", StaticFiles(directory=FRONTEND_DIR, html=True), name="demo")


class ResumeTextRequest(BaseModel):
    """JSON request model for text or structured resume input."""

    resume: str | dict[str, Any] = Field(..., description="Raw resume text or structured resume JSON")


class ChatRequest(BaseModel):
    """Request model for the optional AI career chatbot."""

    question: str
    analysis: dict[str, Any] | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


def _full_analysis(parsed_resume: dict[str, Any]) -> dict[str, Any]:
    predictions = predict_top_roles(parsed_resume["clean_text"], k=3)
    top_role = predictions[0]["role"] if predictions else "General Professional"
    gap = analyze_skill_gap(parsed_resume.get("skills", []), str(top_role))
    resume_score = score_resume(parsed_resume, str(top_role))
    recommendations = build_recommendations(
        score=resume_score["score"],
        missing_skills=gap["missing_skills"],
        feedback=resume_score["feedback"],
        role=str(top_role),
    )

    return {
        "parsed_resume": {
            key: value
            for key, value in parsed_resume.items()
            if key not in {"raw_text", "clean_text"}
        },
        "top_predictions": predictions,
        "role_context": generate_job_description(str(top_role), parsed_resume.get("skills", [])),
        "skill_gap": gap,
        "resume_score": resume_score,
        "recommendations": recommendations,
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Simple service health check."""

    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Open the local demo UI by default."""

    return RedirectResponse(url="/demo/")


@app.post("/analyze/text")
def analyze_text(payload: ResumeTextRequest) -> dict[str, Any]:
    """Analyze raw text or JSON resume input."""

    parsed = parse_resume(payload.resume)
    return _full_analysis(parsed)


@app.post("/chat")
def chat(payload: ChatRequest) -> dict[str, str]:
    """Ask follow-up questions about a resume analysis."""

    return {"answer": chat_with_resume(payload.question, payload.analysis, payload.history)}


@app.post("/analyze/resume")
async def analyze_resume(
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
) -> dict[str, Any]:
    """Analyze a PDF upload or raw text form field."""

    if file is None and not raw_text:
        raise HTTPException(status_code=400, detail="Upload a PDF file or provide raw_text.")

    if raw_text:
        parsed = parse_resume(raw_text)
        return _full_analysis(parsed)

    assert file is not None
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF upload is supported for file input.")

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await file.read())

    try:
        parsed = parse_resume(temp_path, is_pdf=True)
        return _full_analysis(parsed)
    finally:
        temp_path.unlink(missing_ok=True)
