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
