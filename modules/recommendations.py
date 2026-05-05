"""Learning resource and resume improvement recommendations."""

from __future__ import annotations

from urllib.parse import quote_plus


PLATFORMS = {
    "YouTube": "https://www.youtube.com/results?search_query={query}",
    "Coursera": "https://www.coursera.org/search?query={query}",
    "Udemy": "https://www.udemy.com/courses/search/?q={query}",
    "Infosys Springboard": "https://infyspringboard.onwingspan.com/web/en/page/search?query={query}",
}


def recommend_learning_resources(missing_skills: list[str], role: str | None = None) -> list[dict[str, str]]:
    """Build learning resource links for missing skills across major platforms."""

    resources: list[dict[str, str]] = []
    for skill in missing_skills:
        query = quote_plus(f"{role or ''} {skill} course tutorial".strip())
        for platform, url_template in PLATFORMS.items():
            resources.append(
                {
                    "skill": skill,
                    "platform": platform,
                    "title": f"{skill.title()} learning path",
                    "url": url_template.format(query=query),
                }
            )
    return resources[:16]


def improvement_suggestions(score: int, missing_skills: list[str], feedback: list[str]) -> list[str]:
    """Create resume improvement suggestions from score and gaps."""

    suggestions = list(feedback)
    if missing_skills:
        suggestions.append("Add evidence for missing target-role skills: " + ", ".join(missing_skills[:6]) + ".")
    if score < 70:
        suggestions.append("Prioritize quantified bullets, role-specific keywords, and stronger project descriptions.")
    suggestions.append("Tailor the summary and skills section to the top predicted role before applying.")
    return suggestions


def build_recommendations(
    score: int,
    missing_skills: list[str],
    feedback: list[str],
    role: str | None = None,
) -> dict[str, list]:
    """Return learning resources plus resume-improvement guidance."""

    return {
        "learning_resources": recommend_learning_resources(missing_skills, role),
        "improvements": improvement_suggestions(score, missing_skills, feedback),
        "resume_tips": [
            "Use clear section headings that ATS systems can parse.",
            "Start bullets with action verbs and include measurable outcomes.",
            "Keep skills honest, specific, and aligned with the job role.",
        ],
    }
