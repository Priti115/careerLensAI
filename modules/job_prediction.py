"""Top-k job role prediction using saved TF-IDF and classifier artifacts."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np

from .data_preprocessing import cleanResume
from .role_profiles import (
    canonical_role,
    description_for_role,
    skills_for_role,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models"


class JobRolePredictor:
    """
    Predict top matching job roles for a resume.
    """

    def __init__(
        self,
        model_dir: str | Path = DEFAULT_MODEL_DIR,
    ) -> None:

        model_dir = Path(model_dir)

        self.tfidf = self._load_pickle(
            model_dir / "tfidf.pkl"
        )

        self.clf = self._load_pickle(
            model_dir / "clf.pkl"
        )

        self.encoder = self._load_pickle(
            model_dir / "encoder.pkl"
        )

    @staticmethod
    def _load_pickle(path: Path) -> Any:

        if not path.exists():
            raise FileNotFoundError(
                f"Missing model artifact: {path}"
            )

        try:
            with path.open("rb") as file:
                return pickle.load(file)

        except Exception:
            import joblib

            return joblib.load(path)

    def _scores(self, vector: Any) -> np.ndarray:
        """
        Return classifier probabilities.
        """

        if hasattr(self.clf, "predict_proba"):
            return self.clf.predict_proba(vector)[0]

        if hasattr(self.clf, "decision_function"):

            scores = np.asarray(
                self.clf.decision_function(vector),
                dtype=float,
            ).ravel()

            if scores.size == 1:
                scores = np.array(
                    [-scores[0], scores[0]]
                )

            exp = np.exp(
                scores - np.max(scores)
            )

            return exp / exp.sum()

        prediction = int(
            self.clf.predict(vector)[0]
        )

        scores = np.zeros(
            len(self.encoder.classes_)
        )

        scores[prediction] = 1.0

        return scores

    @staticmethod
    def _token_set(text: str) -> set[str]:

        return {
            token
            for token in cleanResume(text)
            .lower()
            .split()
            if len(token) > 2
        }

    def _profile_score(
        self,
        role: str,
        resume_text: str,
    ) -> tuple[float, int, int]:

        resume_lower = resume_text.lower()

        resume_tokens = self._token_set(
            resume_text
        )

        role_skills = skills_for_role(role)

        if not role_skills:
            return 0.0, 0, 0

        # -----------------------------
        # Skill Match
        # -----------------------------

        matched_skills = sum(
            1
            for skill in role_skills
            if skill.lower() in resume_lower
        )

        skill_score = (
            matched_skills / len(role_skills)
        )

        # -----------------------------
        # Description Match
        # -----------------------------

        description_tokens = self._token_set(
            description_for_role(role)
        )

        description_score = (
            len(
                description_tokens
                & resume_tokens
            )
            / len(description_tokens)
            if description_tokens
            else 0.0
        )

        # -----------------------------
        # Final Profile Score
        # -----------------------------

        profile_score = (
            (0.8 * skill_score)
            + (0.2 * description_score)
        )

        return (
            profile_score,
            matched_skills,
            len(role_skills),
        )

    def predict_top_k(
        self,
        resume_text: str,
        k: int = 3,
    ) -> list[dict[str, Any]]:

        clean_text = cleanResume(
            resume_text
        )

        vector = self.tfidf.transform(
            [clean_text]
        )

        model_scores = self._scores(
            vector
        )

        labels = self.encoder.inverse_transform(
            np.arange(len(model_scores))
        )

        ranked = {}

        for idx, raw_label in enumerate(labels):

            role = canonical_role(
                str(raw_label)
            )

            # -----------------------------
            # Base Model Score
            # -----------------------------

            model_score = float(
                model_scores[idx]
            )

            (
                profile_score,
                matched_skills,
                total_skills,
            ) = self._profile_score(
                role,
                clean_text,
            )

            # -----------------------------
            # Skill Match %
            # -----------------------------

            skill_match_percent = (
                (
                    matched_skills
                    / total_skills
                )
                * 100
                if total_skills > 0
                else 0
            )

            # -----------------------------
            # FINAL SCORE
            # -----------------------------

            confidence = (
                (0.3 * model_score)
                + (0.7 * profile_score)
            ) * 100

            # -----------------------------
            # Smart Role Adjustments
            # -----------------------------

            role_lower = role.lower()

            # Boost analytics/data roles
            if (
                "analyst" in role_lower
                or "data" in role_lower
            ):
                confidence += 8

            # Penalize vague roles
            if role_lower in [
                "engineering",
                "developer",
            ]:
                confidence -= 15

            # Penalize weak skill overlap
            if skill_match_percent < 30:
                confidence -= 20

            # Clamp score
            confidence = max(
                5,
                min(confidence, 95)
            )

            ranked[role] = {
                "role": role,

                "confidence":
                    confidence,

                "model_confidence":
                    model_score * 100,

                "profile_match":
                    profile_score * 100,

                "skills_matched":
                    matched_skills,

                "total_skills":
                    total_skills,

                "skill_match_percent":
                    skill_match_percent,
            }

        ordered = sorted(
            ranked.values(),
            key=lambda x:
                x["confidence"],
            reverse=True,
        )

        top_roles = ordered[:k]

        return [
            {
                "role":
                    str(item["role"]),

                "confidence":
                    round(
                        item["confidence"],
                        1,
                    ),

                "model_confidence":
                    round(
                        item[
                            "model_confidence"
                        ],
                        1,
                    ),

                "profile_match":
                    round(
                        item[
                            "profile_match"
                        ],
                        1,
                    ),

                "skills_matched":
                    int(
                        item[
                            "skills_matched"
                        ]
                    ),

                "total_skills":
                    int(
                        item[
                            "total_skills"
                        ]
                    ),

                "skill_match_percent":
                    round(
                        item[
                            "skill_match_percent"
                        ],
                        1,
                    ),
            }
            for item in top_roles
        ]


# =====================================
# Lazy Singleton Predictor
# =====================================

_PREDICTOR: JobRolePredictor | None = None


def predict_top_roles(
    resume_text: str,
    k: int = 3,
) -> list[dict[str, Any]]:

    global _PREDICTOR

    if _PREDICTOR is None:
        _PREDICTOR = JobRolePredictor()

    return _PREDICTOR.predict_top_k(
        resume_text,
        k=k,
    )