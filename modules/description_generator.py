"""Prompt-based job description generation.

If OPENAI_API_KEY is configured, this module uses the OpenAI Python SDK.
Otherwise it returns a deterministic local description so the backend remains
usable without network access or paid services.
"""

from __future__ import annotations

import os


def _fallback_description(role: str, skills: list[str]) -> str:
    skill_text = ", ".join(skills[:8]) if skills else "role-specific tools and best practices"
    return (
        f"{role} professionals analyze business needs, solve practical problems, "
        f"and deliver reliable outcomes using {skill_text}. The role typically "
        "requires strong communication, clean documentation, ownership of assigned "
        "work, and the ability to translate requirements into measurable results."
    )


def generate_job_description(role: str, resume_skills: list[str] | None = None) -> str:
    """Generate a short job description for the predicted role."""

    resume_skills = resume_skills or []
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_description(role, resume_skills)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = (
            "Create a concise, realistic job description for this resume-matched role.\n"
            f"Role: {role}\n"
            f"Candidate skills: {', '.join(resume_skills[:15]) or 'Not provided'}\n"
            "Include responsibilities, important skills, and expected impact in 120 words."
        )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You write practical job descriptions for career guidance."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_description(role, resume_skills)

