from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from cairnhub.publishers import PublisherRegistry
from cairnhub.store import FileRegistryStore


DEFAULT_REGISTRY_PATH = ".cairnhub-hosted"
DEFAULT_PUBLISHERS_PATH = ".cairnhub-publishers.json"


class PublishLoopRequest(BaseModel):
    yaml: str = Field(..., description="Raw Cairn loop YAML text")
    source_file: str = Field("loop.crn", description="Original filename for stored artifact")
    publisher_id: str | None = Field(default=None, description="Publisher id for authenticated publish")
    publisher: str | None = Field(default=None, description="Publisher display name")
    topics: list[str] = Field(default_factory=list, description="Search topics")
    homepage: str | None = Field(default=None, description="Project homepage")


class RateLoopRequest(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Integer rating from 1 to 5")
    reviewer: str = Field(..., min_length=1, description="Reviewer name or handle")
    comment: str | None = Field(default=None, description="Optional short review text")


def create_app(
    registry_path: str | Path | None = None,
    publishers_path: str | Path | None = None,
) -> FastAPI:
    app = FastAPI(
        title="CairnHub API",
        version="0.1.0",
        description="Hosted CairnHub registry foundation for publishing, listing, search, inspect, source fetch, and verified publisher auth.",
    )
    store = FileRegistryStore(registry_path or os.environ.get("CAIRN_HUB_REGISTRY_PATH", DEFAULT_REGISTRY_PATH))
    publisher_registry = PublisherRegistry(
        publishers_path or os.environ.get("CAIRN_HUB_PUBLISHERS_PATH", DEFAULT_PUBLISHERS_PATH)
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "registry_path": str(store.registry_root.resolve()),
            "auth_enabled": publisher_registry.enabled(),
            "publishers_count": publisher_registry.count(),
        }

    @app.get("/api/v1/publishers")
    def list_publishers() -> dict[str, object]:
        return {"publishers": publisher_registry.list_public(), "count": publisher_registry.count()}

    @app.get("/api/v1/loops")
    def list_registry_loops(
        q: str | None = None,
        limit: int = 50,
        verified_only: bool = False,
        min_rating: float | None = None,
    ) -> dict[str, object]:
        results = store.search_loops(q or "") if q is not None else store.list_loops()
        if verified_only:
            results = [item for item in results if item.get("publisher_verified") is True]
        if min_rating is not None:
            results = [item for item in results if (item.get("average_score") or 0) >= min_rating]
        safe_limit = max(1, min(limit, 200))
        return {"loops": results[:safe_limit], "count": len(results[:safe_limit]), "total": len(results)}

    @app.post("/api/v1/loops", status_code=201)
    def publish_registry_loop(payload: PublishLoopRequest, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
        metadata = {
            "publisher_id": payload.publisher_id,
            "publisher": payload.publisher,
            "publisher_verified": False,
            "homepage": payload.homepage,
            "topics": payload.topics,
        }
        if publisher_registry.enabled():
            if not payload.publisher_id:
                raise HTTPException(status_code=400, detail="publisher_id required when publisher auth enabled")
            try:
                publisher = publisher_registry.authenticate(payload.publisher_id, x_api_key)
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except PermissionError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            metadata.update(publisher_registry.publisher_metadata(publisher))
            if not metadata.get("homepage"):
                metadata["homepage"] = publisher.get("homepage")
        try:
            return store.publish_text(
                payload.yaml,
                source_file=payload.source_file,
                metadata=metadata,
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

    @app.get("/api/v1/loops/{loop_id}/versions/{version}/ratings")
    def get_loop_ratings(loop_id: str, version: str) -> dict[str, Any]:
        try:
            return store.get_ratings(f"{loop_id}@{version}")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/loops/{loop_id}/versions/{version}/ratings", status_code=201)
    def rate_loop(loop_id: str, version: str, payload: RateLoopRequest) -> dict[str, Any]:
        try:
            return store.submit_rating(
                f"{loop_id}@{version}",
                score=payload.score,
                reviewer=payload.reviewer,
                comment=payload.comment,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


def run_server(host: str = "127.0.0.1", port: int = 8790, registry_path: str | Path | None = None) -> None:
    import uvicorn

    uvicorn.run(create_app(registry_path=registry_path), host=host, port=port, reload=False)
