"""Optional AI career chatbot for resume analysis follow-up questions."""

from __future__ import annotations

import os
from typing import Any


def _fallback_chat(
    question: str,
    analysis: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> str:
    role = None
    missing = []
    if analysis:
        role = (analysis.get("top_predictions") or [{}])[0].get("role")
        missing = analysis.get("skill_gap", {}).get("missing_skills", [])

    parts = ["I can help you improve this resume with targeted, practical steps."]
    if role:
        parts.append(f"Your strongest current target role appears to be {role}.")
    if missing:
        parts.append("Start by adding evidence for: " + ", ".join(missing[:5]) + ".")
    if history:
        parts.append("I will keep your previous messages in mind while guiding the next step.")
    parts.append("Add quantified project bullets, tools used, and the outcome of each project.")
    parts.append(f"Question received: {question}")
    return " ".join(parts)


def chat_with_resume(
    question: str,
    analysis: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Answer career/resume questions using OpenAI when configured."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_chat(question, analysis, history)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are CareerLensAI, a concise career coach. Give specific, honest, "
                    "resume-improvement advice based on the provided analysis. Do not invent experience."
                ),
            },
            {"role": "user", "content": f"Current resume analysis JSON: {analysis or {}}"},
        ]
        for item in (history or [])[-10:]:
            role = item.get("role")
            if role in {"user", "assistant"} and item.get("content"):
                messages.append({"role": role, "content": item["content"]})
        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_chat(question, analysis, history)
