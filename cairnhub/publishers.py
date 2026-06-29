from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PublisherRegistry:
    def __init__(self, publishers_path: str | Path | None) -> None:
        self.publishers_path = Path(publishers_path) if publishers_path else None
        self._publishers = self._load_publishers()

    def enabled(self) -> bool:
        return bool(self._publishers)

    def count(self) -> int:
        return len(self._publishers)

    def list_public(self) -> list[dict[str, Any]]:
        return [self._public_payload(publisher) for publisher in self._publishers]

    def authenticate(self, publisher_id: str, api_key: str | None) -> dict[str, Any]:
        publisher = self.find_by_id(publisher_id)
        if publisher is None:
            raise LookupError(f"Publisher '{publisher_id}' not registered")
        expected_key = str(publisher.get("api_key", "") or "")
        if not api_key:
            raise PermissionError("Missing API key")
        if expected_key != api_key:
            raise PermissionError("Invalid API key for publisher")
        return publisher

    def find_by_id(self, publisher_id: str) -> dict[str, Any] | None:
        for publisher in self._publishers:
            if publisher.get("id") == publisher_id:
                return publisher
        return None

    def publisher_metadata(self, publisher: dict[str, Any]) -> dict[str, Any]:
        return {
            "publisher_id": publisher.get("id"),
            "publisher": publisher.get("display_name") or publisher.get("id"),
            "publisher_verified": bool(publisher.get("verified", False)),
            "publisher_homepage": publisher.get("homepage"),
        }

    def _load_publishers(self) -> list[dict[str, Any]]:
        if self.publishers_path is None or not self.publishers_path.exists():
            return []
        payload = json.loads(self.publishers_path.read_text(encoding="utf-8"))
        entries = payload.get("publishers", [])
        if not isinstance(entries, list):
            raise ValueError("Publisher registry must contain 'publishers' list")
        publishers = []
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError("Each publisher entry must be object")
            publisher_id = str(item.get("id", "")).strip()
            if not publisher_id:
                raise ValueError("Each publisher entry requires id")
            publishers.append(
                {
                    "id": publisher_id,
                    "display_name": str(item.get("display_name") or publisher_id),
                    "api_key": str(item.get("api_key", "")),
                    "homepage": item.get("homepage"),
                    "verified": bool(item.get("verified", False)),
                }
            )
        return publishers

    def _public_payload(self, publisher: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": publisher.get("id"),
            "display_name": publisher.get("display_name"),
            "homepage": publisher.get("homepage"),
            "verified": bool(publisher.get("verified", False)),
        }
