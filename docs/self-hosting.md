# Self-Hosting Cairn — Deploy Your Own Agent Loop Registry (Agent Loop Engineering)

Current self-hosting scope for the Cairn agent loop engineering platform is local-first.

## Runtime

```bash
pip install -e ".[dev]"
python3 -m cairn.main run cairnlang/examples/hello-world.crn
```

## Local Registry

```bash
python3 -m cairn.main publish cairnlang/examples/hello-world.crn --registry .cairnhub
python3 -m cairn.main list --registry .cairnhub
python3 -m cairn.main search hello --registry .cairnhub
python3 -m cairn.main install hello-world@0.1.0 ./installed-loops --registry .cairnhub
```

## Hosted CairnHub API Foundation

```bash
pip install -e ".[hub]"
uvicorn cairnhub.api:app --host 127.0.0.1 --port 8790
```

Optional verified publishers config:

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

```bash
export CAIRN_HUB_PUBLISHERS_PATH=/absolute/path/publishers.json
uvicorn cairnhub.api:app --host 127.0.0.1 --port 8790
```

Publish loop:

```bash
curl -X POST http://127.0.0.1:8790/api/v1/loops \
  -H "Content-Type: application/json" \
  -d '{
    "yaml": "cairn: \"1.0\"\nloop:\n  id: hosted-hello\n  name: Hosted Hello\n  version: 0.1.0\n  states:\n    - id: finish\n      handler: core.collect\n      inputs:\n        message: hello\n",
    "source_file": "hosted-hello.crn",
    "publisher": "Cairn Labs",
    "topics": ["hello", "registry"]
  }'
```

Publish as verified publisher:

```bash
curl -X POST http://127.0.0.1:8790/api/v1/loops \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me" \
  -d '{
    "yaml": "cairn: \"1.0\"\nloop:\n  id: verified-hello\n  name: Verified Hello\n  version: 0.1.0\n  states:\n    - id: finish\n      handler: core.collect\n      inputs:\n        message: hello\n",
    "source_file": "verified-hello.crn",
    "publisher_id": "cairn-labs",
    "topics": ["verified", "hello"]
  }'
```

Rate published loop:

```bash
curl -X POST http://127.0.0.1:8790/api/v1/loops/verified-hello/versions/0.1.0/ratings \
  -H "Content-Type: application/json" \
  -d '{
    "score": 5,
    "reviewer": "alice",
    "comment": "Clean starter loop"
  }'
```

Share remote registry snapshot into another CairnHub:

```bash
curl http://127.0.0.1:8790/api/v1/index/export > /tmp/peer-snapshot.json

curl -X POST http://127.0.0.1:8791/api/v1/index/import \
  -H "Content-Type: application/json" \
  -d "{
    \"peer_id\": \"hub-east\",
    \"peer_label\": \"Hub East\",
    \"snapshot\": $(cat /tmp/peer-snapshot.json)
  }"
```

Publish runtime trace into hosted CairnLens:

```bash
python3 -m cairn.main run cairnlang/examples/hello-world.crn \
  --trace-endpoint http://127.0.0.1:8790/api/v1/traces
```

Hosted observability UI:

```text
http://127.0.0.1:8790/lens
```

## Checkpointing

```bash
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --checkpoint-file /tmp/pipeline.json --max-steps 1
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --resume /tmp/pipeline.json
```

## Notes

- Hosted CairnHub file-backed API foundation now built
- API-key auth and verified publisher registry now built for self-hosting
- Ratings now built with per-version summaries and review entries
- Shared remote search/index snapshot flow now built
- Hosted CairnLens UI now built
