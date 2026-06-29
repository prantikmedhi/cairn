from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LoopRatingsStore:
    def __init__(self, registry_root: str | Path) -> None:
        self.registry_root = Path(registry_root)

    def submit_rating(
        self,
        *,
        loop_id: str,
        version: str,
        score: int,
        reviewer: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        if score < 1 or score > 5:
            raise ValueError("score must be between 1 and 5")
        reviewer_name = reviewer.strip()
        if not reviewer_name:
            raise ValueError("reviewer required")

        ratings = self._load_entries(loop_id, version)
        ratings.append(
            {
                "score": score,
                "reviewer": reviewer_name,
                "comment": (comment or "").strip() or None,
                "rated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._write_entries(loop_id, version, ratings)
        return self.summarize(loop_id=loop_id, version=version)

    def summarize(self, *, loop_id: str, version: str) -> dict[str, Any]:
        ratings = self._load_entries(loop_id, version)
        count = len(ratings)
        average = round(sum(item["score"] for item in ratings) / count, 2) if count else None
        distribution = {str(score): 0 for score in range(1, 6)}
        for item in ratings:
            distribution[str(item["score"])] += 1
        return {
            "loop_id": loop_id,
            "version": version,
            "average_score": average,
            "ratings_count": count,
            "distribution": distribution,
            "ratings": ratings,
        }

    def compact_summary(self, *, loop_id: str, version: str) -> dict[str, Any]:
        summary = self.summarize(loop_id=loop_id, version=version)
        return {
            "average_score": summary["average_score"],
            "ratings_count": summary["ratings_count"],
            "rating_distribution": summary["distribution"],
        }

    def _load_entries(self, loop_id: str, version: str) -> list[dict[str, Any]]:
        path = self._ratings_path(loop_id, version)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload.get("ratings", [])
        if not isinstance(entries, list):
            raise ValueError("ratings payload invalid")
        cleaned: list[dict[str, Any]] = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            score = int(item.get("score", 0))
            if score < 1 or score > 5:
                continue
            cleaned.append(
                {
                    "score": score,
                    "reviewer": str(item.get("reviewer", "")).strip() or "unknown",
                    "comment": item.get("comment"),
                    "rated_at": item.get("rated_at"),
                }
            )
        return cleaned

    def _write_entries(self, loop_id: str, version: str, ratings: list[dict[str, Any]]) -> None:
        path = self._ratings_path(loop_id, version)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "loop_id": loop_id,
            "version": version,
            "ratings": ratings,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _ratings_path(self, loop_id: str, version: str) -> Path:
        return self.registry_root / "_ratings" / loop_id / f"{version}.json"
