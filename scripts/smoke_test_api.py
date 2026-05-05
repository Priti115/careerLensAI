"""Smoke test the running CareerLensAI API.

Usage:
    python scripts/smoke_test_api.py
"""

from __future__ import annotations

import json
import urllib.request


BASE_URL = "http://127.0.0.1:8000"
SAMPLE_RESUME = """
John Doe
Email john.doe@example.com
Phone +91 9876543210
Skills Python SQL Machine Learning Pandas Numpy Scikit-learn Tableau Flask Git Docker
Experience 3 years building dashboards, NLP models, classification systems, and FastAPI services.
Projects Built a customer churn model that improved reporting speed by 18 percent.
Education B.Tech Computer Science
"""


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as response:
        print("Health:", response.read().decode("utf-8"))

    result = post_json("/analyze/text", {"resume": SAMPLE_RESUME})
    print("Top predictions:")
    for item in result["top_predictions"]:
        print(f"  - {item['role']}: {item['confidence']}")
    print("Resume score:", result["resume_score"]["score"])
    print("Missing skills:", ", ".join(result["skill_gap"]["missing_skills"]))

    chat = post_json(
        "/chat",
        {
            "question": "What should I improve first?",
            "analysis": result,
        },
    )
    print("Chat answer:", chat["answer"])


if __name__ == "__main__":
    main()
