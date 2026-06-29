# CairnHub

This directory now contains both local registry foundation and hosted API foundation.

Current scope:

- publish loop files into local registry path
- publish raw loop YAML into hosted file-backed registry
- install loops from local registry path
- list, search, inspect, and fetch published manifests/source
- verified publisher registry and API-key gated publishing
- per-version loop ratings and review summaries
- remote peer index export/import for shared search
- remote source/version resolution from imported peer registries
- hosted CairnLens traces and observability UI
- FastAPI app for self-hosted CairnHub foundation

Run hosted API:

```bash
pip install -e ".[hub]"
uvicorn cairnhub.api:app --host 127.0.0.1 --port 8790
```

Open hosted observability UI:

```text
http://127.0.0.1:8790/lens
```

Optional verified publishers file:

```json
{
  "publishers": [
    {
      "id": "cairn-labs",
      "display_name": "Cairn Labs",
      "api_key": "change-me",
      "homepage": "https://example.com/cairn-labs",
      "verified": true
    }
  ]
}
```

Set path with `CAIRN_HUB_PUBLISHERS_PATH=/path/to/publishers.json`.

Still not built:

- direct peer-to-peer authenticated install without snapshot exchange
