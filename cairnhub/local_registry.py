from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from cairnforge.parser import load_loop_file
from cairnforge.validator import validate_loop_definition


def publish_loop(loop_path: str | Path, registry_path: str | Path) -> dict:
    source = Path(loop_path)
    loop = load_loop_file(source)
    validate_loop_definition(loop)

    registry_root = Path(registry_path)
    version_dir = registry_root / loop.id / loop.version
    version_dir.mkdir(parents=True, exist_ok=True)

    stored_loop_path = version_dir / source.name
    shutil.copy2(source, stored_loop_path)

    manifest = {
        "id": loop.id,
        "name": loop.name,
        "version": loop.version,
        "description": loop.description,
        "source_file": source.name,
        "stored_loop_path": str(stored_loop_path.resolve()),
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    (version_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def install_loop(ref: str, destination: str | Path, registry_path: str | Path, force: bool = False) -> Path:
    manifest = inspect_loop(ref, registry_path)
    source = Path(manifest["stored_loop_path"])
    target_dir = Path(destination)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source.name
    if target_path.exists() and not force:
        raise FileExistsError(f"{target_path} already exists")
    shutil.copy2(source, target_path)
    return target_path


def list_loops(registry_path: str | Path) -> list[dict]:
    registry_root = Path(registry_path)
    if not registry_root.exists():
        return []
    manifests = sorted(registry_root.glob("*/*/manifest.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in manifests]


def inspect_loop(ref: str, registry_path: str | Path) -> dict:
    loop_id, version = _parse_ref(ref)
    registry_root = Path(registry_path)
    loop_dir = registry_root / loop_id
    if not loop_dir.exists():
        raise FileNotFoundError(f"Loop '{loop_id}' not found in registry {registry_root}")

    if version is None:
        versions = [path.name for path in loop_dir.iterdir() if path.is_dir()]
        if not versions:
            raise FileNotFoundError(f"Loop '{loop_id}' has no published versions")
        version = _pick_latest_version(versions)

    manifest_path = loop_dir / version / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Loop '{loop_id}@{version}' not found in registry {registry_root}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


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
