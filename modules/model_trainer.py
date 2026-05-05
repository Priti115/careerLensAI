"""Training utilities for CareerLensAI job-role prediction.

This module intentionally trains only from `dataset/finalData.csv`.
Expected columns:
    - Category
    - Resume_clean

The train/test split happens before TF-IDF fitting to prevent data leakage.
"""

from __future__ import annotations

import pickle
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from .data_preprocessing import cleanResume


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "dataset" / "finalData.csv"
MODEL_DIR = PROJECT_ROOT / "models"


def load_training_data(dataset_path: str | Path = DATASET_PATH) -> pd.DataFrame:
    """Load and validate `finalData.csv` for model training."""

    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found: {dataset_path}")

    data = pd.read_csv(dataset_path, encoding_errors="ignore")
    required_columns = {"Category", "Resume_clean"}
    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(f"finalData.csv is missing required columns: {sorted(missing)}")

    data = data[["Category", "Resume_clean"]].dropna()
    data["Category"] = data["Category"].astype(str).str.strip()
    data["Resume_clean"] = data["Resume_clean"].astype(str).map(cleanResume)
    data = data[data["Resume_clean"].str.len() > 30]
    data = data.drop_duplicates(subset=["Category", "Resume_clean"])

    if data.empty:
        raise ValueError("Training dataset is empty after cleaning.")

    return data


def train_model(
    dataset_path: str | Path = DATASET_PATH,
    model_dir: str | Path = MODEL_DIR,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train TF-IDF + balanced classifier and save local artifacts."""

    data = load_training_data(dataset_path)
    encoder = LabelEncoder()
    labels = encoder.fit_transform(data["Category"])

    class_counts = data["Category"].value_counts()
    stratify = labels if class_counts.min() >= 2 else None

    x_train, x_test, y_train, y_test = train_test_split(
        data["Resume_clean"],
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    tfidf = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    max_features=12000,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    sublinear_tf=True,
                ),
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    max_features=8000,
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                ),
            ),
        ]
    )
    x_train_vec = tfidf.fit_transform(x_train)
    x_test_vec = tfidf.transform(x_test)

    base_clf = LinearSVC(
        class_weight="balanced",
        random_state=random_state,
        C=1.2,
    )
    clf = CalibratedClassifierCV(base_clf, method="sigmoid", cv=3)
    clf.fit(x_train_vec, y_train)

    predictions = clf.predict(x_test_vec)
    probabilities = clf.predict_proba(x_test_vec)
    metrics: dict[str, Any] = {
        "dataset_path": str(Path(dataset_path).resolve()),
        "rows": int(len(data)),
        "classes": int(len(encoder.classes_)),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "classification_report": classification_report(
            y_test,
            predictions,
            target_names=encoder.classes_,
            zero_division=0,
        ),
    }
    if len(encoder.classes_) >= 3:
        metrics["top_3_accuracy"] = round(
            float(top_k_accuracy_score(y_test, probabilities, k=3, labels=range(len(encoder.classes_)))),
            4,
        )

    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    for filename, artifact in {
        "tfidf.pkl": tfidf,
        "clf.pkl": clf,
        "encoder.pkl": encoder,
    }.items():
        with (model_dir / filename).open("wb") as file:
            pickle.dump(artifact, file)

    with (model_dir / "model_metrics.json").open("w", encoding="utf-8") as file:
        json.dump({key: value for key, value in metrics.items() if key != "classification_report"}, file, indent=2)

    return metrics


if __name__ == "__main__":
    result = train_model()
    print(f"Trained from: {result['dataset_path']}")
    print(f"Rows: {result['rows']} | Classes: {result['classes']}")
    print(f"Accuracy: {result['accuracy']}")
    if "top_3_accuracy" in result:
        print(f"Top-3 accuracy: {result['top_3_accuracy']}")
    print(result["classification_report"])
