from __future__ import annotations

from app.models.schemas import SimilarIncident
from app.services.retrieval import retrieval_store


class RetrievalAgent:
    def run(self, symptoms: str) -> list[SimilarIncident]:
        rows = retrieval_store.similar(symptoms, top_k=3)
        output: list[SimilarIncident] = []
        for item, score in rows:
            output.append(
                SimilarIncident(
                    incident_id=item.incident_id,
                    class_label=item.class_label,
                    similarity=round(score, 4),
                    summary=item.resolution or item.symptoms[:160]
                )
            )
        return output
