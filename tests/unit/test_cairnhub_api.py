from fastapi.testclient import TestClient

from cairnhub.api import create_app


SAMPLE_LOOP = """
cairn: "1.0"
loop:
  id: hosted-hello
  name: Hosted Hello
  version: 0.2.0
  description: Hosted registry smoke test
  outputs:
    greeting:
      value: ${{ states.finish.outputs.message }}
  states:
    - id: finish
      handler: core.collect
      inputs:
        message: hello hub
"""


def test_cairnhub_publish_list_search_inspect_and_source(tmp_path) -> None:
    client = TestClient(create_app(registry_path=tmp_path / "hub"))

    publish = client.post(
        "/api/v1/loops",
        json={
            "yaml": SAMPLE_LOOP,
            "source_file": "hosted-hello.crn",
            "publisher": "Cairn Labs",
            "topics": ["registry", "hosted", "hello"],
            "homepage": "https://example.com/hosted-hello",
        },
    )
    assert publish.status_code == 201
    published_manifest = publish.json()
    assert published_manifest["id"] == "hosted-hello"
    assert published_manifest["publisher"] == "Cairn Labs"
    assert published_manifest["topics"] == ["registry", "hosted", "hello"]

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    listed = client.get("/api/v1/loops")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1

    searched = client.get("/api/v1/loops", params={"q": "hosted"})
    assert searched.status_code == 200
    assert searched.json()["loops"][0]["id"] == "hosted-hello"

    latest = client.get("/api/v1/loops/hosted-hello")
    assert latest.status_code == 200
    assert latest.json()["version"] == "0.2.0"

    versioned = client.get("/api/v1/loops/hosted-hello/versions/0.2.0")
    assert versioned.status_code == 200
    assert versioned.json()["homepage"] == "https://example.com/hosted-hello"

    source = client.get("/api/v1/loops/hosted-hello/versions/0.2.0/source")
    assert source.status_code == 200
    assert "hello hub" in source.text


def test_cairnhub_publish_rejects_invalid_loop(tmp_path) -> None:
    client = TestClient(create_app(registry_path=tmp_path / "hub"))

    response = client.post("/api/v1/loops", json={"yaml": "cairn: 1.0\nloop: []\n"})

    assert response.status_code == 400
    assert "Missing top-level 'loop' object" in response.json()["detail"]


def test_cairnhub_verified_publishers_require_api_key_and_mark_manifest(tmp_path) -> None:
    publishers_file = tmp_path / "publishers.json"
    publishers_file.write_text(
        """
{
  "publishers": [
    {
      "id": "cairn-labs",
      "display_name": "Cairn Labs",
      "api_key": "secret-key",
      "homepage": "https://example.com/cairn-labs",
      "verified": true
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    client = TestClient(create_app(registry_path=tmp_path / "hub", publishers_path=publishers_file))

    missing_key = client.post(
        "/api/v1/loops",
        json={"yaml": SAMPLE_LOOP, "source_file": "verified.crn", "publisher_id": "cairn-labs"},
    )
    assert missing_key.status_code == 401
    assert "Missing API key" in missing_key.json()["detail"]

    wrong_key = client.post(
        "/api/v1/loops",
        headers={"X-API-Key": "wrong-key"},
        json={"yaml": SAMPLE_LOOP, "source_file": "verified.crn", "publisher_id": "cairn-labs"},
    )
    assert wrong_key.status_code == 401
    assert "Invalid API key" in wrong_key.json()["detail"]

    publish = client.post(
        "/api/v1/loops",
        headers={"X-API-Key": "secret-key"},
        json={"yaml": SAMPLE_LOOP, "source_file": "verified.crn", "publisher_id": "cairn-labs"},
    )
    assert publish.status_code == 201
    manifest = publish.json()
    assert manifest["publisher_id"] == "cairn-labs"
    assert manifest["publisher"] == "Cairn Labs"
    assert manifest["publisher_verified"] is True
    assert manifest["publisher_homepage"] == "https://example.com/cairn-labs"

    publishers = client.get("/api/v1/publishers")
    assert publishers.status_code == 200
    assert publishers.json()["count"] == 1
    assert publishers.json()["publishers"][0] == {
        "id": "cairn-labs",
        "display_name": "Cairn Labs",
        "homepage": "https://example.com/cairn-labs",
        "verified": True,
    }

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["auth_enabled"] is True
    assert health.json()["publishers_count"] == 1

    verified_only = client.get("/api/v1/loops", params={"verified_only": "true"})
    assert verified_only.status_code == 200
    assert verified_only.json()["count"] == 1


def test_cairnhub_ratings_summary_and_filtering(tmp_path) -> None:
    client = TestClient(create_app(registry_path=tmp_path / "hub"))

    publish = client.post(
        "/api/v1/loops",
        json={"yaml": SAMPLE_LOOP, "source_file": "rated.crn", "publisher": "Cairn Labs"},
    )
    assert publish.status_code == 201

    first = client.post(
        "/api/v1/loops/hosted-hello/versions/0.2.0/ratings",
        json={"score": 5, "reviewer": "alice", "comment": "Great loop"},
    )
    assert first.status_code == 201
    assert first.json()["average_score"] == 5.0
    assert first.json()["ratings_count"] == 1

    second = client.post(
        "/api/v1/loops/hosted-hello/versions/0.2.0/ratings",
        json={"score": 3, "reviewer": "bob", "comment": "Solid base"},
    )
    assert second.status_code == 201
    assert second.json()["average_score"] == 4.0
    assert second.json()["ratings_count"] == 2
    assert second.json()["distribution"] == {"1": 0, "2": 0, "3": 1, "4": 0, "5": 1}

    summary = client.get("/api/v1/loops/hosted-hello/versions/0.2.0/ratings")
    assert summary.status_code == 200
    assert summary.json()["average_score"] == 4.0
    assert len(summary.json()["ratings"]) == 2

    latest = client.get("/api/v1/loops/hosted-hello")
    assert latest.status_code == 200
    assert latest.json()["average_score"] == 4.0
    assert latest.json()["ratings_count"] == 2

    filtered = client.get("/api/v1/loops", params={"min_rating": "4"})
    assert filtered.status_code == 200
    assert filtered.json()["count"] == 1

    rejected = client.post(
        "/api/v1/loops/hosted-hello/versions/0.2.0/ratings",
        json={"score": 0, "reviewer": "eve"},
    )
    assert rejected.status_code == 422


def test_cairnhub_remote_index_import_and_search(tmp_path) -> None:
    primary = TestClient(create_app(registry_path=tmp_path / "primary"))
    peer = TestClient(create_app(registry_path=tmp_path / "peer"))

    published = peer.post(
        "/api/v1/loops",
        json={
            "yaml": SAMPLE_LOOP.replace("hosted-hello", "peer-loop"),
            "source_file": "peer-loop.crn",
            "publisher": "Peer Labs",
            "topics": ["shared", "remote"],
        },
    )
    assert published.status_code == 201

    snapshot = peer.get("/api/v1/index/export")
    assert snapshot.status_code == 200

    imported = primary.post(
        "/api/v1/index/import",
        json={"peer_id": "peer-east", "peer_label": "Peer East", "snapshot": snapshot.json()},
    )
    assert imported.status_code == 201
    assert imported.json()["loops_indexed"] == 1

    peers = primary.get("/api/v1/index/peers")
    assert peers.status_code == 200
    assert peers.json()["count"] == 1

    remote_search = primary.get("/api/v1/loops", params={"q": "remote", "include_remote": "true"})
    assert remote_search.status_code == 200
    assert remote_search.json()["loops"][0]["source_kind"] == "remote"
    assert remote_search.json()["loops"][0]["peer_id"] == "peer-east"

    inspected = primary.get("/api/v1/remote/loops/peer-east/peer-loop")
    assert inspected.status_code == 200
    assert inspected.json()["version"] == "0.2.0"

    remote_source = primary.get("/api/v1/remote/loops/peer-east/peer-loop/versions/0.2.0/source")
    assert remote_source.status_code == 200
    assert "hello hub" in remote_source.text


def test_cairnhub_traces_and_lens_ui(tmp_path) -> None:
    client = TestClient(create_app(registry_path=tmp_path / "hub"))

    trace = client.post(
        "/api/v1/traces",
        json={
            "loop_id": "hello-world",
            "success": True,
            "final_outputs": {"greeting": "hello"},
            "state_results": [{"state_id": "finish", "outputs": {"greeting": "hello"}, "skipped": False}],
            "metadata": {"target": "langchain", "duration_ms": 18.5, "cost_usd": 0.02, "retry_events": 0},
            "source": "cli",
            "tags": ["smoke"],
        },
    )
    assert trace.status_code == 201
    trace_id = trace.json()["trace_id"]

    traces = client.get("/api/v1/traces")
    assert traces.status_code == 200
    assert traces.json()["count"] == 1

    summary = client.get("/api/v1/lens/summary")
    assert summary.status_code == 200
    assert summary.json()["total_traces"] == 1
    assert summary.json()["success_rate"] == 100.0

    fetched = client.get(f"/api/v1/traces/{trace_id}")
    assert fetched.status_code == 200
    assert fetched.json()["source"] == "cli"

    lens = client.get("/lens")
    assert lens.status_code == 200
    assert "CairnLens" in lens.text
    assert "hello-world" in lens.text
