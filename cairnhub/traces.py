from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LoopTraceStore:
    def __init__(self, registry_root: str | Path) -> None:
        self.registry_root = Path(registry_root)
        self.trace_root = self.registry_root / "_traces"

    def publish_trace(self, payload: dict[str, Any]) -> dict[str, Any]:
        loop_id = str(payload.get("loop_id", "")).strip()
        if not loop_id:
            raise ValueError("loop_id required")
        trace_id = str(payload.get("trace_id") or self._trace_id(loop_id))
        summary = {
            "trace_id": trace_id,
            "loop_id": loop_id,
            "success": bool(payload.get("success", False)),
            "error": payload.get("error"),
            "final_outputs": payload.get("final_outputs", {}),
            "state_results": payload.get("state_results", []),
            "metadata": payload.get("metadata", {}),
            "source": payload.get("source") or "unknown",
            "tags": list(payload.get("tags", [])) if isinstance(payload.get("tags"), list) else [],
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self.trace_root.mkdir(parents=True, exist_ok=True)
        (self.trace_root / f"{trace_id}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    def list_traces(
        self,
        *,
        limit: int = 50,
        loop_id: str | None = None,
        success: bool | None = None,
    ) -> list[dict[str, Any]]:
        if not self.trace_root.exists():
            return []
        traces = []
        for path in sorted(self.trace_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if loop_id and payload.get("loop_id") != loop_id:
                continue
            if success is not None and bool(payload.get("success")) is not success:
                continue
            traces.append(payload)
        traces.sort(key=lambda item: str(item.get("published_at", "")), reverse=True)
        return traces[:limit]

    def get_trace(self, trace_id: str) -> dict[str, Any]:
        path = self.trace_root / f"{trace_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Trace '{trace_id}' not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def summarize(self) -> dict[str, Any]:
        traces = self.list_traces(limit=500)
        total = len(traces)
        successes = [trace for trace in traces if trace.get("success")]
        failures = [trace for trace in traces if not trace.get("success")]
        durations = [float(trace.get("metadata", {}).get("duration_ms", 0.0) or 0.0) for trace in traces]
        costs = [float(trace.get("metadata", {}).get("cost_usd", 0.0) or 0.0) for trace in traces]
        loop_counts: dict[str, int] = {}
        target_counts: dict[str, int] = {}
        for trace in traces:
            loop_counts[trace["loop_id"]] = loop_counts.get(trace["loop_id"], 0) + 1
            target = str(trace.get("metadata", {}).get("target", "unknown"))
            target_counts[target] = target_counts.get(target, 0) + 1

        return {
            "total_traces": total,
            "success_count": len(successes),
            "failure_count": len(failures),
            "success_rate": round((len(successes) / total) * 100, 2) if total else 0.0,
            "average_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0.0,
            "average_cost_usd": round(sum(costs) / len(costs), 4) if costs else 0.0,
            "top_loops": sorted(loop_counts.items(), key=lambda item: item[1], reverse=True)[:5],
            "target_counts": target_counts,
            "recent_failures": failures[:5],
        }

    def _trace_id(self, loop_id: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        safe_loop = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in loop_id)
        return f"{safe_loop}-{stamp}"
