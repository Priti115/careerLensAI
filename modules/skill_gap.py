"""Skill gap analysis between resume skills and target job-role skills."""

from __future__ import annotations

from .role_profiles import canonical_role, skills_for_role


def required_skills_for_role(role: str) -> set[str]:
    """Return configured skills for a role, with fuzzy fallback by role name."""

    return skills_for_role(role)


def analyze_skill_gap(resume_skills: list[str], role: str) -> dict[str, list[str] | float]:
    """Compare extracted resume skills with expected role skills."""

    resume_set = {skill.lower().strip() for skill in resume_skills}
    required = required_skills_for_role(role)
    matched = sorted(required & resume_set)
    missing = sorted(required - resume_set)
    coverage = round(len(matched) / len(required), 2) if required else 1.0
    return {
        "role": canonical_role(role),
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage": coverage,
    }
