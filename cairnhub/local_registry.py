from __future__ import annotations

from pathlib import Path

from cairnhub.store import FileRegistryStore


def publish_loop(loop_path: str | Path, registry_path: str | Path) -> dict:
    return FileRegistryStore(registry_path).publish_path(loop_path)


def install_loop(ref: str, destination: str | Path, registry_path: str | Path, force: bool = False) -> Path:
    return FileRegistryStore(registry_path).install_loop(ref, destination, force=force)


def list_loops(registry_path: str | Path) -> list[dict]:
    return FileRegistryStore(registry_path).list_loops()


def search_loops(query: str, registry_path: str | Path) -> list[dict]:
    return FileRegistryStore(registry_path).search_loops(query)


def inspect_loop(ref: str, registry_path: str | Path) -> dict:
    return FileRegistryStore(registry_path).inspect_loop(ref)
