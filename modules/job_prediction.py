"""Top-k job role prediction using saved TF-IDF and classifier artifacts."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np

from .data_preprocessing import cleanResume
from .role_profiles import canonical_role, description_for_role, skills_for_role


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models"


class JobRolePredictor:
    """Load local model artifacts and return ranked job-role predictions."""

    def __init__(self, model_dir: str | Path = DEFAULT_MODEL_DIR) -> None:
        model_dir = Path(model_dir)
        self.tfidf = self._load_pickle(model_dir / "tfidf.pkl")
        self.clf = self._load_pickle(model_dir / "clf.pkl")
        self.encoder = self._load_pickle(model_dir / "encoder.pkl")

    @staticmethod
    def _load_pickle(path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Missing model artifact: {path}")
        try:
            with path.open("rb") as file:
                return pickle.load(file)
        except Exception:
            import joblib

            return joblib.load(path)

    def _scores(self, vector: Any) -> np.ndarray:
        if hasattr(self.clf, "predict_proba"):
            return self.clf.predict_proba(vector)[0]
        if hasattr(self.clf, "decision_function"):
            scores = np.asarray(self.clf.decision_function(vector), dtype=float).ravel()
            if scores.size == 1:
                scores = np.array([-scores[0], scores[0]], dtype=float)
            exp = np.exp(scores - np.max(scores))
            return exp / exp.sum()
        prediction = int(self.clf.predict(vector)[0])
        scores = np.zeros(len(self.encoder.classes_), dtype=float)
        scores[prediction] = 1.0
        return scores

    @staticmethod
    def _token_set(text: str) -> set[str]:
        return {token for token in cleanResume(text).lower().split() if len(token) > 2}

    def _profile_score(self, role: str, resume_text: str) -> float:
        resume_lower = resume_text.lower()
        resume_tokens = self._token_set(resume_text)
        role_skills = skills_for_role(role)
        if not role_skills:
            return 0.0

        matched_skills = sum(1 for skill in role_skills if skill in resume_lower)
        skill_score = matched_skills / len(role_skills)

        description_tokens = self._token_set(description_for_role(role))
        description_score = (
            len(description_tokens & resume_tokens) / len(description_tokens)
            if description_tokens
            else 0.0
        )
        return (0.75 * skill_score) + (0.25 * description_score)

    def predict_top_k(self, resume_text: str, k: int = 3) -> list[dict[str, float | str]]:
        """Return the top-k roles sorted by hybrid confidence.

        The trained classifier is still the base signal, but it is reranked with
        role profile skill overlap and compact role-description keyword overlap.
        This prevents unrelated categories from appearing when raw classifier
        probabilities are weak.
        """

        clean_text = cleanResume(resume_text)
        vector = self.tfidf.transform([clean_text])
        model_scores = self._scores(vector)
        labels = self.encoder.inverse_transform(np.arange(len(model_scores)))

        ranked: dict[str, dict[str, float | str]] = {}
        for index, raw_label in enumerate(labels):
            role = canonical_role(str(raw_label))
            model_score = float(model_scores[index])
            profile_score = self._profile_score(role, clean_text)
            hybrid_score = (0.6 * model_score) + (0.4 * profile_score)

            existing = ranked.get(role)
            if existing is None or hybrid_score > float(existing["confidence"]):
                ranked[role] = {
                    "role": role,
                    "confidence": hybrid_score,
                    "model_confidence": model_score,
                    "profile_match": profile_score,
                }

        ordered = sorted(ranked.values(), key=lambda item: float(item["confidence"]), reverse=True)
        top = ordered[: min(k, len(ordered))]
        return [
            {
                "role": str(item["role"]),
                "confidence": round(float(item["confidence"]), 4),
                "model_confidence": round(float(item["model_confidence"]), 4),
                "profile_match": round(float(item["profile_match"]), 4),
            }
            for item in top
        ]


_PREDICTOR: JobRolePredictor | None = None


def predict_top_roles(resume_text: str, k: int = 3) -> list[dict[str, float | str]]:
    """Convenience function with lazy model loading for API usage."""

    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = JobRolePredictor()
    return _PREDICTOR.predict_top_k(resume_text, k=k)
