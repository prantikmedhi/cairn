from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_checkpoint(path: str | Path, payload: dict[str, Any]) -> Path:
    checkpoint_path = Path(path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return checkpoint_path


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    checkpoint_path = Path(path)
    return json.loads(checkpoint_path.read_text(encoding="utf-8"))
