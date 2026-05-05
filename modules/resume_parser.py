"""Resume parsing helpers for PDF and text inputs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .data_preprocessing import preprocess_input


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/\S+|linkedin\.com/\S+", re.I)
GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/\S+|github\.com/\S+", re.I)
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)", re.I)

COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "sql",
    "excel",
    "power bi",
    "tableau",
    "machine learning",
    "statistics",
    "data visualization",
    "dashboarding",
    "api",
    "api testing",
    "testing",
    "manual testing",
    "test automation",
    "selenium",
    "testng",
    "pytest",
    "jira",
    "postman",
    "jenkins",
    "bug tracking",
    "spring",
    "spring boot",
    "oop",
    "maven",
    "junit",
    "etl",
    "data warehouse",
    "data pipeline",
    "airflow",
    "deep learning",
    "nlp",
    "computer vision",
    "data analysis",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "flask",
    "fastapi",
    "django",
    "react",
    "node.js",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "ci/cd",
    "terraform",
    "monitoring",
    "git",
    "mongodb",
    "postgresql",
    "mysql",
    "oracle",
    "query optimization",
    "spark",
    "hadoop",
    "hive",
    "scala",
    "big data",
    "networking",
    "network security",
    "security",
    "firewall",
    "vulnerability assessment",
    "siem",
    "tcp/ip",
    "windows",
    "support",
    "troubleshooting",
    "cloud",
    "html",
    "css",
    "bootstrap",
    "figma",
    "responsive design",
    "blockchain",
    "solidity",
    "smart contracts",
    "web3",
    "ethereum",
    "linux",
}


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF using pdfplumber first, then pypdf fallback."""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    except Exception:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as exc:
            raise RuntimeError(f"Unable to extract PDF text from {path}") from exc


def _extract_name(lines: list[str], email: str | None) -> str | None:
    for line in lines[:8]:
        candidate = line.strip()
        if not candidate or "resume" in candidate.lower() or "curriculum" in candidate.lower():
            continue
        if email and email in candidate:
            continue
        if len(candidate.split()) <= 5 and any(char.isalpha() for char in candidate):
            return candidate
    return None


def _extract_section(text: str, section_names: list[str]) -> list[str]:
    lines = [line.strip(" -*:\t") for line in text.splitlines() if line.strip()]
    section_hits: list[str] = []
    capture = False
    for line in lines:
        lower = line.lower()
        if any(name in lower for name in section_names):
            capture = True
            continue
        if capture and re.fullmatch(r"[A-Za-z ]{3,30}", line) and len(line.split()) <= 4:
            break
        if capture:
            section_hits.append(line)
    return section_hits[:20]


def extract_skills(text: str) -> list[str]:
    """Extract known skills using a compact, extensible skill dictionary."""

    lowered = f" {text.lower()} "
    found = [skill for skill in COMMON_SKILLS if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", lowered)]
    return sorted(found)


def parse_resume(resume_input: str | Path | dict[str, Any], is_pdf: bool = False) -> dict[str, Any]:
    """Parse resume input into structured fields and text variants."""

    if is_pdf:
        raw_input: str | dict[str, Any] = extract_text_from_pdf(resume_input)
    else:
        raw_input = resume_input if isinstance(resume_input, dict) else str(resume_input)

    normalized = preprocess_input(raw_input)
    raw = normalized["raw_text"]
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    email = next(iter(EMAIL_RE.findall(raw)), None)
    phones = [phone.strip() for phone in PHONE_RE.findall(raw)]
    years = [float(match) for match in YEARS_RE.findall(raw)]

    return {
        "name": _extract_name(lines, email),
        "email": email,
        "phone": phones[0] if phones else None,
        "linkedin": next(iter(LINKEDIN_RE.findall(raw)), None),
        "github": next(iter(GITHUB_RE.findall(raw)), None),
        "skills": extract_skills(raw),
        "education": _extract_section(raw, ["education", "academic"]),
        "experience": _extract_section(raw, ["experience", "employment", "work history"]),
        "projects": _extract_section(raw, ["projects", "portfolio"]),
        "certifications": _extract_section(raw, ["certifications", "certificates"]),
        "estimated_experience_years": max(years) if years else 0,
        "raw_text": raw,
        "clean_text": normalized["clean_text"],
    }
