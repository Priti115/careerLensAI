"""Optional local vector persistence for TF-IDF vectors."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any


def save_vectors(vectors: Any, path: str | Path) -> None:
    """Persist vectors locally as pickle."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as file:
        pickle.dump(vectors, file)


def load_vectors(path: str | Path) -> Any:
    """Load locally persisted vectors."""

    with Path(path).open("rb") as file:
        return pickle.load(file)

