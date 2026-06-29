# CairnHub

This directory now contains both local registry foundation and hosted API foundation.

Current scope:

- publish loop files into local registry path
- publish raw loop YAML into hosted file-backed registry
- install loops from local registry path
- list, search, inspect, and fetch published manifests/source
- FastAPI app for self-hosted CairnHub foundation

Run hosted API:

```bash
pip install -e ".[hub]"
uvicorn cairnhub.api:app --host 127.0.0.1 --port 8790
```

Still not built:

- auth and publishers
- verified publishers
- ratings
- shared multi-node search/index
- version resolution across remote registry peers
