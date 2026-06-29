from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RemoteIndexStore:
    def __init__(self, registry_root: str | Path) -> None:
        self.registry_root = Path(registry_root)
        self.index_root = self.registry_root / "_peer_indexes"

    def export_snapshot(self, loops: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "loops": [self._sanitize_loop(loop) for loop in loops],
        }

    def import_snapshot(self, peer_id: str, snapshot: dict[str, Any], peer_label: str | None = None) -> dict[str, Any]:
        if not peer_id.strip():
            raise ValueError("peer_id required")
        loops = snapshot.get("loops", [])
        if not isinstance(loops, list):
            raise ValueError("snapshot.loops must be list")

        payload = {
            "peer_id": peer_id,
            "peer_label": peer_label or peer_id,
            "generated_at": snapshot.get("generated_at"),
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "loops": [self._sanitize_loop(loop, remote_peer_id=peer_id, remote_peer_label=peer_label or peer_id) for loop in loops if isinstance(loop, dict)],
        }
        self.index_root.mkdir(parents=True, exist_ok=True)
        target = self.index_root / f"{_safe_name(peer_id)}.json"
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"peer_id": payload["peer_id"], "peer_label": payload["peer_label"], "loops_indexed": len(payload["loops"])}

    def list_peer_indexes(self) -> list[dict[str, Any]]:
        if not self.index_root.exists():
            return []
        peers = []
        for path in sorted(self.index_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            peers.append(
                {
                    "peer_id": payload.get("peer_id"),
                    "peer_label": payload.get("peer_label"),
                    "generated_at": payload.get("generated_at"),
                    "imported_at": payload.get("imported_at"),
                    "loops_indexed": len(payload.get("loops", [])),
                }
            )
        return peers

    def list_remote_loops(self) -> list[dict[str, Any]]:
        if not self.index_root.exists():
            return []
        loops: list[dict[str, Any]] = []
        for path in sorted(self.index_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            loops.extend(payload.get("loops", []))
        return loops

    def _sanitize_loop(
        self,
        loop: dict[str, Any],
        *,
        remote_peer_id: str | None = None,
        remote_peer_label: str | None = None,
    ) -> dict[str, Any]:
        allowed = {
            "id": loop.get("id"),
            "name": loop.get("name"),
            "version": loop.get("version"),
            "description": loop.get("description"),
            "publisher_id": loop.get("publisher_id"),
            "publisher": loop.get("publisher"),
            "publisher_verified": loop.get("publisher_verified"),
            "publisher_homepage": loop.get("publisher_homepage"),
            "topics": list(loop.get("topics", [])) if isinstance(loop.get("topics"), list) else [],
            "homepage": loop.get("homepage"),
            "published_at": loop.get("published_at"),
            "source_file": loop.get("source_file"),
            "source_text": loop.get("source_text"),
            "average_score": loop.get("average_score"),
            "ratings_count": loop.get("ratings_count"),
            "rating_distribution": loop.get("rating_distribution"),
            "source_kind": "remote" if remote_peer_id else "local",
        }
        if remote_peer_id:
            allowed["peer_id"] = remote_peer_id
            allowed["peer_label"] = remote_peer_label or remote_peer_id
        return allowed


def _safe_name(value: str) -> str:
    return "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in value)
