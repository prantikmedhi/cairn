# CLI Reference

Current Cairn CLI commands:

- `init`
- `validate`
- `run`
- `inspect`
- `trace`
- `publish`
- `install`
- `list`
- `search`
- `registry-inspect`
- `debug`
- `cost`
- `test`
- `watch`

## Examples

```bash
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --checkpoint-file /tmp/pipeline.json --max-steps 1
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --resume /tmp/pipeline.json
python3 -m cairn.main publish cairnlang/examples/hello-world.crn --registry .cairnhub
python3 -m cairn.main search hello --registry .cairnhub
python3 -m cairn.main debug cairnlang/examples/retry-recovery.crn
python3 -m cairn.main cost cairnlang/examples/parallel-fanout.crn
python3 -m cairn.main watch cairnlang/examples/hello-world.crn --cycles 2
```
