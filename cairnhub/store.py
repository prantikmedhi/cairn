from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cairnhub.ratings import LoopRatingsStore
from cairnforge.parser import load_loop_file, parse_loop_document
from cairnforge.validator import validate_loop_definition


class FileRegistryStore:
    def __init__(self, registry_path: str | Path) -> None:
        self.registry_root = Path(registry_path)
        self.ratings = LoopRatingsStore(self.registry_root)

    def publish_path(self, loop_path: str | Path, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        source = Path(loop_path)
        loop = load_loop_file(source)
        validate_loop_definition(loop)

        version_dir = self.registry_root / loop.id / loop.version
        version_dir.mkdir(parents=True, exist_ok=True)

        stored_loop_path = version_dir / source.name
        shutil.copy2(source, stored_loop_path)
        manifest = self._build_manifest(loop=loop, source_file=source.name, stored_loop_path=stored_loop_path, metadata=metadata)
        self._write_manifest(version_dir, manifest)
        return manifest

    def publish_text(
        self,
        yaml_text: str,
        *,
        source_file: str = "loop.crn",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            payload = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Loop document must parse to mapping")

        loop = parse_loop_document(payload)
        validate_loop_definition(loop)

        version_dir = self.registry_root / loop.id / loop.version
        version_dir.mkdir(parents=True, exist_ok=True)

        safe_name = _safe_source_name(source_file)
        stored_loop_path = version_dir / safe_name
        stored_loop_path.write_text(yaml_text, encoding="utf-8")
        manifest = self._build_manifest(loop=loop, source_file=safe_name, stored_loop_path=stored_loop_path, metadata=metadata)
        self._write_manifest(version_dir, manifest)
        return manifest

    def list_loops(self) -> list[dict[str, Any]]:
        if not self.registry_root.exists():
            return []
        manifests = sorted(self.registry_root.glob("*/*/manifest.json"))
        return [self._with_ratings(json.loads(path.read_text(encoding="utf-8"))) for path in manifests]

    def search_loops(self, query: str) -> list[dict[str, Any]]:
        query_text = query.strip().lower()
        if not query_text:
            return self.list_loops()
        matches = []
        for manifest in self.list_loops():
            haystack = " ".join(
                [
                    str(manifest.get("id", "")),
                    str(manifest.get("name", "")),
                    str(manifest.get("description", "")),
                    " ".join(str(topic) for topic in manifest.get("topics", [])),
                    str(manifest.get("publisher", "")),
                ]
            ).lower()
            if query_text in haystack:
                matches.append(manifest)
        return matches

    def inspect_loop(self, ref: str) -> dict[str, Any]:
        loop_id, version = _parse_ref(ref)
        loop_dir = self.registry_root / loop_id
        if not loop_dir.exists():
            raise FileNotFoundError(f"Loop '{loop_id}' not found in registry {self.registry_root}")

        if version is None:
            versions = [path.name for path in loop_dir.iterdir() if path.is_dir()]
            if not versions:
                raise FileNotFoundError(f"Loop '{loop_id}' has no published versions")
            version = _pick_latest_version(versions)

        manifest_path = loop_dir / version / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Loop '{loop_id}@{version}' not found in registry {self.registry_root}")
        return self._with_ratings(json.loads(manifest_path.read_text(encoding="utf-8")))

    def install_loop(self, ref: str, destination: str | Path, force: bool = False) -> Path:
        manifest = self.inspect_loop(ref)
        source = Path(manifest["stored_loop_path"])
        target_dir = Path(destination)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / source.name
        if target_path.exists() and not force:
            raise FileExistsError(f"{target_path} already exists")
        shutil.copy2(source, target_path)
        return target_path

    def load_source_text(self, ref: str) -> str:
        manifest = self.inspect_loop(ref)
        return Path(manifest["stored_loop_path"]).read_text(encoding="utf-8")

    def submit_rating(
        self,
        ref: str,
        *,
        score: int,
        reviewer: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        manifest = self.inspect_loop(ref)
        return self.ratings.submit_rating(
            loop_id=manifest["id"],
            version=manifest["version"],
            score=score,
            reviewer=reviewer,
            comment=comment,
        )

    def get_ratings(self, ref: str) -> dict[str, Any]:
        manifest = self.inspect_loop(ref)
        return self.ratings.summarize(loop_id=manifest["id"], version=manifest["version"])

    def _build_manifest(
        self,
        *,
        loop,
        source_file: str,
        stored_loop_path: Path,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        metadata = dict(metadata or {})
        topics = metadata.get("topics", [])
        return {
            "id": loop.id,
            "name": loop.name,
            "version": loop.version,
            "description": loop.description,
            "publisher_id": metadata.get("publisher_id"),
            "publisher": metadata.get("publisher"),
            "publisher_verified": bool(metadata.get("publisher_verified", False)),
            "publisher_homepage": metadata.get("publisher_homepage"),
            "topics": list(topics) if isinstance(topics, list) else [],
            "homepage": metadata.get("homepage"),
            "source_file": source_file,
            "stored_loop_path": str(stored_loop_path.resolve()),
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

    def _write_manifest(self, version_dir: Path, manifest: dict[str, Any]) -> None:
        (version_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _with_ratings(self, manifest: dict[str, Any]) -> dict[str, Any]:
        summary = self.ratings.compact_summary(loop_id=str(manifest.get("id", "")), version=str(manifest.get("version", "")))
        return {**manifest, **summary}


def _parse_ref(ref: str) -> tuple[str, str | None]:
    if "@" not in ref:
        return ref, None
    loop_id, version = ref.split("@", 1)
    return loop_id, version


def _pick_latest_version(versions: list[str]) -> str:
    def version_key(value: str) -> tuple[int, ...]:
        parts = []
        for chunk in value.split("."):
            try:
                parts.append(int(chunk))
            except ValueError:
                parts.append(0)
        return tuple(parts)

    return sorted(versions, key=version_key)[-1]


def _safe_source_name(name: str) -> str:
    candidate = Path(name).name or "loop.crn"
    if not candidate.endswith(".crn"):
        candidate = f"{candidate}.crn"
    return "".join(character if character.isalnum() or character in {"-", "_", "."} else "-" for character in candidate)
