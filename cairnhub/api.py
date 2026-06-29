from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from cairnhub.store import FileRegistryStore


DEFAULT_REGISTRY_PATH = ".cairnhub-hosted"


class PublishLoopRequest(BaseModel):
    yaml: str = Field(..., description="Raw Cairn loop YAML text")
    source_file: str = Field("loop.crn", description="Original filename for stored artifact")
    publisher: str | None = Field(default=None, description="Publisher display name")
    topics: list[str] = Field(default_factory=list, description="Search topics")
    homepage: str | None = Field(default=None, description="Project homepage")


def create_app(registry_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(
        title="CairnHub API",
        version="0.1.0",
        description="Hosted CairnHub registry foundation for publishing, listing, search, inspect, and source fetch.",
    )
    store = FileRegistryStore(registry_path or os.environ.get("CAIRN_HUB_REGISTRY_PATH", DEFAULT_REGISTRY_PATH))

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True, "registry_path": str(store.registry_root.resolve())}

    @app.get("/api/v1/loops")
    def list_registry_loops(q: str | None = None, limit: int = 50) -> dict[str, object]:
        results = store.search_loops(q or "") if q is not None else store.list_loops()
        safe_limit = max(1, min(limit, 200))
        return {"loops": results[:safe_limit], "count": len(results[:safe_limit]), "total": len(results)}

    @app.post("/api/v1/loops", status_code=201)
    def publish_registry_loop(payload: PublishLoopRequest) -> dict[str, Any]:
        try:
            return store.publish_text(
                payload.yaml,
                source_file=payload.source_file,
                metadata={
                    "publisher": payload.publisher,
                    "topics": payload.topics,
                    "homepage": payload.homepage,
                },
            )
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/loops/{loop_id}")
    def inspect_latest_loop(loop_id: str, version: str | None = None) -> dict[str, Any]:
        ref = f"{loop_id}@{version}" if version else loop_id
        try:
            return store.inspect_loop(ref)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/loops/{loop_id}/versions/{version}")
    def inspect_versioned_loop(loop_id: str, version: str) -> dict[str, Any]:
        try:
            return store.inspect_loop(f"{loop_id}@{version}")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/loops/{loop_id}/versions/{version}/source", response_class=PlainTextResponse)
    def fetch_loop_source(loop_id: str, version: str) -> str:
        try:
            return store.load_source_text(f"{loop_id}@{version}")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()


def run_server(host: str = "127.0.0.1", port: int = 8790, registry_path: str | Path | None = None) -> None:
    import uvicorn

    uvicorn.run(create_app(registry_path=registry_path), host=host, port=port, reload=False)
