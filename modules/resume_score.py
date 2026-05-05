"""Resume scoring and structure feedback."""

from __future__ import annotations

import re
from typing import Any


SECTION_KEYWORDS = {
    "skills": ["skills", "technical skills"],
    "experience": ["experience", "employment", "work history"],
    "education": ["education", "academic"],
    "projects": ["projects", "portfolio"],
    "certifications": ["certifications", "certificates"],
}


def structure_feedback(raw_text: str) -> list[str]:
    """Return actionable structure feedback based on common resume sections."""

    lower = raw_text.lower()
    feedback: list[str] = []
    for section, keywords in SECTION_KEYWORDS.items():
        if not any(keyword in lower for keyword in keywords):
            feedback.append(f"Add a clear {section.title()} section.")
    if not re.search(r"\b\d+%|\b\d+\+|\b(increased|reduced|improved|built|led|delivered)\b", lower):
        feedback.append("Add measurable achievements and stronger action verbs.")
    if len(raw_text.split()) < 250:
        feedback.append("Resume is short; add relevant project, impact, and responsibility details.")
    return feedback


def score_resume(parsed_resume: dict[str, Any], target_role: str | None = None) -> dict[str, Any]:
    """Score resume from 0 to 100 using skills, experience, structure, keywords."""

    raw_text = parsed_resume.get("raw_text", "")
    skills = parsed_resume.get("skills", [])
    experience_years = float(parsed_resume.get("estimated_experience_years") or 0)
    lower = raw_text.lower()

    skills_score = min(len(skills) * 4, 30)
    experience_score = min(experience_years * 5, 20)
    structure_present = sum(any(key in lower for key in keys) for keys in SECTION_KEYWORDS.values())
    structure_score = int((structure_present / len(SECTION_KEYWORDS)) * 25)
    keyword_score = 0
    if parsed_resume.get("email"):
        keyword_score += 5
    if parsed_resume.get("phone"):
        keyword_score += 5
    if parsed_resume.get("projects"):
        keyword_score += 5
    if target_role and target_role.lower() in lower:
        keyword_score += 5
    if any(word in lower for word in ["achieved", "improved", "optimized", "led", "built"]):
        keyword_score += 5

    total = int(min(skills_score + experience_score + structure_score + keyword_score, 100))
    return {
        "score": total,
        "breakdown": {
            "skills": skills_score,
            "experience": experience_score,
            "structure": structure_score,
            "keywords": keyword_score,
        },
        "feedback": structure_feedback(raw_text),
    }

