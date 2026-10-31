from __future__ import annotations

import math
import os
import re
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = ROOT / "models" / "resume_model"


def _tokens(text: str) -> list[str]:
    return [token.strip(".-") for token in re.findall(r"[a-zA-Z][a-zA-Z+#.\-]{1,}", text.lower()) if token.strip(".-")]


def _cosine_from_counts(a: Counter, b: Counter) -> float:
    shared = set(a) & set(b)
    numerator = sum(a[token] * b[token] for token in shared)
    left = math.sqrt(sum(value * value for value in a.values()))
    right = math.sqrt(sum(value * value for value in b.values()))
    if not left or not right:
        return 0.0
    return numerator / (left * right)


class LocalModelAdapter:
    """Loads an optional local trained model, with a deterministic fallback."""

    def __init__(self) -> None:
        self.model_path = Path(os.environ.get("RESUME_MODEL_PATH", str(DEFAULT_MODEL_DIR)))
        self.backend = "keyword-vector"
        self.status = "Using built-in local keyword vector model."
        self._model: Any | None = None
        self._idf: dict[str, float] = {}

        if (self.model_path / "model.json").exists():
            self._try_local_tfidf()
        elif self.model_path.exists():
            self._try_sentence_transformer()
        else:
            self.status = f"No trained model found at {self.model_path}. Using built-in local scorer."

    def _try_local_tfidf(self) -> None:
        try:
            model_file = self.model_path / "model.json"
            payload = json.loads(model_file.read_text(encoding="utf-8"))
            if payload.get("model_type") != "local-tfidf":
                raise ValueError("unsupported model_type")
            self._idf = {str(key): float(value) for key, value in payload["idf"].items()}
            self.backend = "local-tfidf"
            self.status = f"Loaded trained local TF-IDF model from {model_file}."
        except Exception as exc:
            self.status = f"Found local model files at {self.model_path}, but could not load them ({exc}). Using built-in scorer."

    def _try_sentence_transformer(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(str(self.model_path))
            self.backend = "sentence-transformer"
            self.status = f"Loaded local trained model from {self.model_path}."
        except Exception as exc:
            self.status = f"Found {self.model_path}, but could not load it ({exc}). Using built-in scorer."

    def similarity(self, resume_text: str, job_description: str) -> float | None:
        if not job_description.strip():
            return None

        if self.backend == "local-tfidf" and self._idf:
            return _cosine_from_counts(self._tfidf(resume_text), self._tfidf(job_description))

        if self._model is not None:
            try:
                embeddings = self._model.encode([resume_text, job_description], normalize_embeddings=True)
                score = float(embeddings[0] @ embeddings[1])
                return max(0.0, min(1.0, score))
            except Exception:
                pass

        return _cosine_from_counts(Counter(_tokens(resume_text)), Counter(_tokens(job_description)))

    def _tfidf(self, text: str) -> Counter:
        counts = Counter(_tokens(text))
        weighted = Counter()
        default_idf = self._idf.get("__default__", 1.0)
        for token, count in counts.items():
            weighted[token] = count * self._idf.get(token, default_idf)
        return weighted


MODEL = LocalModelAdapter()
