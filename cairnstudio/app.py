from __future__ import annotations

import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml

from cairnforge.executor import execute_loop
from cairnforge.models import LoopDefinition
from cairnforge.parser import parse_loop_document
from cairnforge.validator import CairnValidationError, validate_loop_definition


ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
SESSION_DIR = ROOT / "sessions"
PRESENCE_TTL_SECONDS = 15
STARTER_LOOP = """cairn: "1.0"

loop:
  id: visual-starter
  name: Visual Starter
  version: 0.1.0
  inputs:
    prompt:
      type: string
      default: hello
  outputs:
    result:
      value: ${{ states.finish.outputs.message }}
  budget:
    max_iterations: 3
    max_duration: 30s
  states:
    - id: draft
      handler: core.template
      inputs:
        message: "{{ inputs.prompt }} from CairnStudio"
    - id: finish
      handler: core.collect
      inputs:
        message: ${{ states.draft.outputs.message }}
  transitions:
    - from: draft
      to: finish
"""


def render_index_html() -> str:
    context = {
        "page_title": "CairnStudio Beta",
        "starter_yaml": STARTER_LOOP,
        "available_targets": ["langchain", "langgraph", "crewai", "autogen", "openai"],
        "phase_badge": "Phase 4 Beta",
        "collaboration_status": "Hosted collaboration ready: live presence, comments, activity feed, and shared session sync",
        "default_session_id": "default",
    }
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError as exc:  # pragma: no cover - explicit runtime guidance
        raise RuntimeError("CairnStudio requires Jinja2. Install project dependencies first.") from exc

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("index.html.j2")
    return template.render(context)


def parse_yaml_text(yaml_text: str) -> LoopDefinition:
    payload = yaml.safe_load(yaml_text)
    if not isinstance(payload, dict):
        raise ValueError("Loop document must parse to a mapping")
    loop = parse_loop_document(payload)
    validate_loop_definition(loop)
    return loop


def yaml_to_canvas_model(yaml_text: str) -> dict[str, Any]:
    loop = parse_yaml_text(yaml_text)
    states = []
    state_by_id = {state.id: state for state in loop.states}
    transition_map = {state.id: [] for state in loop.states}
    for transition in loop.transitions:
        transition_map.setdefault(transition.from_state, []).append(transition.to_state)

    for index, state in enumerate(loop.states):
        column = index % 3
        row = index // 3
        states.append(
            {
                "id": state.id,
                "label": state.name or state.id,
                "handler": state.handler,
                "loop": state.loop_ref,
                "condition": state.condition,
                "parallel": list(state.raw.get("parallel", [])) if isinstance(state.raw, dict) else [],
                "guard": dict(state.raw.get("guard", {})) if isinstance(state.raw, dict) else {},
                "inputs": dict(state.inputs),
                "transitions": transition_map.get(state.id, []),
                "x": 80 + column * 260,
                "y": 100 + row * 180,
                "kind": "subloop" if state.loop_ref else "state",
            }
        )

    return {
        "loop": {
            "id": loop.id,
            "name": loop.name,
            "version": loop.version,
            "description": loop.description,
            "imports": [{"name": item.name, "source": item.source} for item in loop.imports],
            "budget": {
                "max_cost_usd": loop.budget.max_cost_usd,
                "max_duration": loop.budget.max_duration,
                "max_iterations": loop.budget.max_iterations,
            },
            "states": states,
        }
    }


def canvas_model_to_yaml(model: dict[str, Any]) -> str:
    loop_model = dict(model.get("loop", {}))
    states = []
    transitions = []
    for state in loop_model.get("states", []):
        item = {"id": state["id"], "inputs": state.get("inputs", {})}
        if state.get("kind") == "subloop" or state.get("loop"):
            item["loop"] = state.get("loop") or state["id"]
        else:
            item["handler"] = state.get("handler", "core.collect")
        if state.get("label") and state["label"] != state["id"]:
            item["name"] = state["label"]
        if state.get("condition"):
            item["condition"] = state["condition"]
        if state.get("parallel"):
            item["parallel"] = state["parallel"]
        if state.get("guard"):
            item["guard"] = state["guard"]
        states.append(item)
        for to_state in state.get("transitions", []):
            transitions.append({"from": state["id"], "to": to_state})

    payload = {
        "cairn": "1.0",
        "loop": {
            "id": loop_model.get("id", "visual-loop"),
            "name": loop_model.get("name", "Visual Loop"),
            "version": loop_model.get("version", "0.1.0"),
            "description": loop_model.get("description", ""),
            "imports": loop_model.get("imports", []),
            "budget": {key: value for key, value in dict(loop_model.get("budget", {})).items() if value not in (None, "")},
            "states": states,
            "transitions": transitions,
        },
    }
    return yaml.safe_dump(payload, sort_keys=False)


def validate_yaml_text(yaml_text: str) -> dict[str, Any]:
    loop = parse_yaml_text(yaml_text)
    return {
        "valid": True,
        "loop_id": loop.id,
        "states": [state.id for state in loop.states],
        "imports": [item.name for item in loop.imports],
    }


def preview_yaml_text(yaml_text: str, inputs: dict[str, Any] | None = None, target: str = "langchain") -> dict[str, Any]:
    loop = parse_yaml_text(yaml_text)
    result = execute_loop(loop, inputs=inputs or {}, target=target)
    return {
        "loop_id": result.loop_id,
        "success": result.success,
        "final_outputs": result.final_outputs,
        "error": result.error,
        "state_results": [
            {"state_id": item.state_id, "outputs": item.outputs, "skipped": item.skipped}
            for item in result.state_results
        ],
        "metadata": result.metadata,
    }


def load_session(session_id: str) -> dict[str, Any]:
    session_path = _session_path(session_id)
    if not session_path.exists():
        return {
            "session_id": session_id,
            "version": 0,
            "updated_at": None,
            "yaml": STARTER_LOOP,
            "model": yaml_to_canvas_model(STARTER_LOOP),
        }
    return json.loads(session_path.read_text(encoding="utf-8"))


def save_session(
    session_id: str,
    yaml_text: str,
    model: dict[str, Any],
    client_version: int | None = None,
    actor_id: str | None = None,
    actor_name: str | None = None,
) -> dict[str, Any]:
    session_path = _session_path(session_id)
    current = load_session(session_id)
    current_version = int(current.get("version", 0))
    if client_version is not None and client_version < current_version:
        return current

    payload = {
        "session_id": session_id,
        "version": current_version + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "yaml": yaml_text,
        "model": model,
    }
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if actor_id or actor_name:
        _append_activity(
            session_id,
            {
                "kind": "save",
                "actor_id": actor_id or "unknown",
                "actor_name": actor_name or actor_id or "unknown",
                "message": "saved shared session",
                "at": datetime.now(timezone.utc).isoformat(),
            },
        )
    return payload


def heartbeat_presence(session_id: str, actor_id: str, actor_name: str) -> dict[str, Any]:
    if not actor_id.strip():
        raise ValueError("actor_id required")
    if not actor_name.strip():
        raise ValueError("actor_name required")

    metadata = _load_session_meta(session_id)
    now = datetime.now(timezone.utc)
    active_presence = []
    seen = False
    for item in metadata.get("presence", []):
        last_seen_text = item.get("last_seen")
        if not last_seen_text:
            continue
        last_seen = datetime.fromisoformat(last_seen_text)
        if (now - last_seen).total_seconds() > PRESENCE_TTL_SECONDS:
            continue
        if item.get("actor_id") == actor_id:
            item = {
                "actor_id": actor_id,
                "actor_name": actor_name,
                "last_seen": now.isoformat(),
            }
            seen = True
        active_presence.append(item)
    if not seen:
        active_presence.append({"actor_id": actor_id, "actor_name": actor_name, "last_seen": now.isoformat()})
    metadata["presence"] = active_presence
    if not seen:
        activity = list(metadata.get("activity", []))
        activity.append(
            {
                "kind": "join",
                "actor_id": actor_id,
                "actor_name": actor_name,
                "message": "joined shared room",
                "at": now.isoformat(),
            }
        )
        metadata["activity"] = activity[-50:]
    _write_session_meta(session_id, metadata)
    return {"session_id": session_id, "presence": active_presence, "count": len(active_presence)}


def load_presence(session_id: str) -> dict[str, Any]:
    metadata = _load_session_meta(session_id)
    now = datetime.now(timezone.utc)
    active_presence = [
        item
        for item in metadata.get("presence", [])
        if item.get("last_seen") and (now - datetime.fromisoformat(item["last_seen"])).total_seconds() <= PRESENCE_TTL_SECONDS
    ]
    metadata["presence"] = active_presence
    _write_session_meta(session_id, metadata)
    return {"session_id": session_id, "presence": active_presence, "count": len(active_presence)}


def add_comment(session_id: str, actor_id: str, actor_name: str, message: str) -> dict[str, Any]:
    comment_text = message.strip()
    if not comment_text:
        raise ValueError("comment message required")
    metadata = _load_session_meta(session_id)
    comment = {
        "actor_id": actor_id or "unknown",
        "actor_name": actor_name or actor_id or "unknown",
        "message": comment_text,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    comments = list(metadata.get("comments", []))
    comments.append(comment)
    metadata["comments"] = comments[-50:]
    _write_session_meta(session_id, metadata)
    _append_activity(
        session_id,
        {
            "kind": "comment",
            "actor_id": comment["actor_id"],
            "actor_name": comment["actor_name"],
            "message": comment["message"],
            "at": comment["at"],
        },
    )
    return {"session_id": session_id, "comment": comment}


def load_activity(session_id: str) -> dict[str, Any]:
    metadata = _load_session_meta(session_id)
    return {
        "session_id": session_id,
        "comments": list(metadata.get("comments", []))[-20:],
        "activity": list(metadata.get("activity", []))[-30:],
    }


def _session_path(session_id: str) -> Path:
    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in session_id) or "default"
    return SESSION_DIR / f"{safe}.json"


def _session_meta_path(session_id: str) -> Path:
    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in session_id) or "default"
    return SESSION_DIR / "_meta" / f"{safe}.json"


def _load_session_meta(session_id: str) -> dict[str, Any]:
    path = _session_meta_path(session_id)
    if not path.exists():
        return {"session_id": session_id, "presence": [], "comments": [], "activity": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_session_meta(session_id: str, metadata: dict[str, Any]) -> None:
    path = _session_meta_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _append_activity(session_id: str, event: dict[str, Any]) -> None:
    metadata = _load_session_meta(session_id)
    activity = list(metadata.get("activity", []))
    activity.append(event)
    metadata["activity"] = activity[-50:]
    _write_session_meta(session_id, metadata)


class CairnStudioHandler(BaseHTTPRequestHandler):
    server_version = "CairnStudio/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(render_index_html())
            return
        if parsed.path == "/api/session":
            query = parse_qs(parsed.query)
            session_id = query.get("id", ["default"])[0]
            self._send_json(load_session(session_id))
            return
        if parsed.path == "/api/session/presence":
            query = parse_qs(parsed.query)
            session_id = query.get("id", ["default"])[0]
            self._send_json(load_presence(session_id))
            return
        if parsed.path == "/api/session/activity":
            query = parse_qs(parsed.query)
            session_id = query.get("id", ["default"])[0]
            self._send_json(load_activity(session_id))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            self._send_json({"error": f"Invalid JSON: {exc}"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            if parsed.path == "/api/validate":
                self._send_json(validate_yaml_text(payload.get("yaml", "")))
                return
            if parsed.path == "/api/preview":
                self._send_json(preview_yaml_text(payload.get("yaml", ""), inputs=payload.get("inputs", {}), target=payload.get("target", "langchain")))
                return
            if parsed.path == "/api/model/from-yaml":
                self._send_json(yaml_to_canvas_model(payload.get("yaml", "")))
                return
            if parsed.path == "/api/model/to-yaml":
                self._send_json({"yaml": canvas_model_to_yaml(payload)})
                return
            if parsed.path == "/api/session/save":
                session_id = payload.get("session_id", "default")
                yaml_text = payload.get("yaml", STARTER_LOOP)
                model = payload.get("model") or yaml_to_canvas_model(yaml_text)
                self._send_json(
                    save_session(
                        session_id,
                        yaml_text,
                        model,
                        client_version=payload.get("version"),
                        actor_id=payload.get("actor_id"),
                        actor_name=payload.get("actor_name"),
                    )
                )
                return
            if parsed.path == "/api/session/presence":
                self._send_json(
                    heartbeat_presence(
                        payload.get("session_id", "default"),
                        payload.get("actor_id", ""),
                        payload.get("actor_name", ""),
                    )
                )
                return
            if parsed.path == "/api/session/comment":
                self._send_json(
                    add_comment(
                        payload.get("session_id", "default"),
                        payload.get("actor_id", ""),
                        payload.get("actor_name", ""),
                        payload.get("message", ""),
                    )
                )
                return
        except (ValueError, CairnValidationError, RuntimeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), CairnStudioHandler)
    print(f"CairnStudio running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
