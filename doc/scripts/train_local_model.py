from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "resume_model"
MODEL_FILE = MODEL_DIR / "model.json"


TRAINING_DOCUMENTS = [
    "AI engineer resume with Python machine learning NLP model deployment FastAPI Docker AWS SQL experiment tracking and data pipelines.",
    "Data analyst resume with SQL Excel Power BI Tableau statistics dashboards reporting stakeholder communication and business insights.",
    "Frontend developer resume with React TypeScript JavaScript accessibility responsive design state management APIs testing and performance.",
    "Backend developer resume with Python Java REST APIs databases PostgreSQL Redis Docker Kubernetes cloud architecture and observability.",
    "DevOps engineer resume with AWS Azure CI/CD Terraform Kubernetes Docker Linux monitoring automation security and release management.",
    "Product manager resume with roadmap planning user research analytics stakeholder management launch strategy prioritization and communication.",
    "Cybersecurity analyst resume with network security vulnerability assessment SIEM incident response risk analysis compliance and cloud security.",
    "Machine learning job description requiring Python PyTorch TensorFlow scikit-learn NLP computer vision data preprocessing model evaluation and deployment.",
    "Software engineer job description requiring scalable systems APIs databases Git testing code review Agile collaboration and problem solving.",
    "Business analyst job description requiring requirements gathering process mapping SQL dashboards documentation communication and stakeholder workshops.",
    "Resume bullets should use action verbs built led optimized automated delivered improved reduced increased deployed migrated and quantified impact.",
    "ATS friendly resumes include summary experience skills education projects certifications contact details measurable achievements and relevant keywords.",
]


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z+#.\-]{1,}", text.lower()))


def build_idf(documents: list[str]) -> dict[str, float]:
    document_count = len(documents)
    document_frequency: Counter[str] = Counter()
    for document in documents:
        document_frequency.update(tokens(document))

    idf = {
        token: round(math.log((1 + document_count) / (1 + frequency)) + 1, 6)
        for token, frequency in sorted(document_frequency.items())
    }
    idf["__default__"] = round(math.log((1 + document_count) / 1) + 1, 6)
    return idf


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_type": "local-tfidf",
        "version": 1,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_document_count": len(TRAINING_DOCUMENTS),
        "description": "Dependency-free local TF-IDF model trained for resume-to-job-description similarity.",
        "idf": build_idf(TRAINING_DOCUMENTS),
    }
    MODEL_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Saved trained local model to {MODEL_FILE}")


if __name__ == "__main__":
    main()
