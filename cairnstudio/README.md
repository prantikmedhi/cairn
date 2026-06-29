# CairnStudio

CairnStudio beta is now available as a hosted-ready Jinja-backed visual editor for non-developers.

Current beta scope:

- drag-and-drop canvas
- YAML import/export
- real-time validation
- live execution preview
- trace replay visualization
- shared-session collaboration
- live presence heartbeat
- shared comments and activity feed
- hosted shareable session URLs

Run:

```bash
python3 -m cairn.main studio --port 8787
```

Then open:

```text
http://127.0.0.1:8787
```

Still pending:

- conflict-free merge beyond last-write-wins
