from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import typer
from rich.console import Console

from cairnhub.api import run_server as run_hub_server
from cairnhub.local_registry import inspect_loop, install_loop, list_loops, publish_loop, search_loops
from cairnstudio.app import run_server as run_studio_server
from cairnforge.compiler import compile_loop
from cairnforge.executor import execute_loop, execute_loop_with_runtime_controls
from cairnforge.plugins import get_builtin_plugins
from cairnforge.parser import load_loop_file
from cairnforge.validator import CairnValidationError, validate_loop_definition

app = typer.Typer(help="Cairn CLI for loop validation and execution.")
console = Console()
DEFAULT_REGISTRY_PATH = Path(".cairnhub")


def _parse_key_values(items: list[str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for item in items:
        if "=" not in item:
            raise typer.BadParameter(f"Inputs must be key=value pairs, got '{item}'")
        key, raw_value = item.split("=", 1)
        values[key] = _coerce_value(raw_value)
    return values


def _coerce_value(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _result_payload(result) -> dict[str, object]:
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


def _publish_trace_payload(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - runtime guidance
        raise RuntimeError("Trace publishing requires httpx. Install with `pip install -e \".[hub]\"`.") from exc

    response = httpx.post(endpoint, json=payload, timeout=10.0)
    response.raise_for_status()
    return response.json()


def _load_inputs(items: list[str] | None, inputs_file: Path | None) -> dict[str, object]:
    provided_inputs = _parse_key_values(items or [])
    if inputs_file is not None:
        provided_inputs.update(json.loads(inputs_file.read_text(encoding="utf-8")))
    return provided_inputs


@app.command()
def validate(path: Path) -> None:
    """Validate .crn file against schema and semantic rules."""

    try:
        loop = load_loop_file(path)
        validate_loop_definition(loop)
    except (ValueError, CairnValidationError) as exc:
        console.print(f"[red]Validation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Valid loop:[/green] {loop.id}")


@app.command()
def run(
    path: Path,
    target: str = typer.Option("langchain", "--target", help="Execution target plugin"),
    input: list[str] = typer.Option(None, "--input", help="Loop input as key=value"),
    inputs_file: Path | None = typer.Option(None, "--inputs-file", help="JSON file with loop inputs"),
    checkpoint_file: Path | None = typer.Option(None, "--checkpoint-file", help="Write checkpoint state to JSON file"),
    resume: Path | None = typer.Option(None, "--resume", help="Resume execution from checkpoint JSON file"),
    max_steps: int | None = typer.Option(None, "--max-steps", help="Pause after N executed states"),
    trace_file: Path | None = typer.Option(None, "--trace-file", help="Write execution trace JSON file"),
    trace_endpoint: str | None = typer.Option(None, "--trace-endpoint", help="Publish execution trace JSON to hosted CairnLens endpoint"),
) -> None:
    """Execute loop and print result JSON."""

    provided_inputs = _load_inputs(input, inputs_file)

    loop = load_loop_file(path)
    result = execute_loop_with_runtime_controls(
        loop,
        inputs=provided_inputs,
        target=target,
        checkpoint_path=checkpoint_file,
        resume_from=resume,
        max_steps=max_steps,
    )
    payload = _result_payload(result)
    console.print_json(data=payload)
    if trace_file is not None:
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        trace_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if trace_endpoint is not None:
        published = _publish_trace_payload(trace_endpoint, payload)
        console.print_json(data={"trace_published": True, "trace_id": published.get("trace_id"), "endpoint": trace_endpoint})
    if not result.success and not result.metadata.get("paused"):
        raise typer.Exit(code=1)


@app.command()
def init(
    destination: Path = typer.Argument(..., help="Directory to create loop project in"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing starter file"),
) -> None:
    """Create starter Cairn loop project."""

    destination.mkdir(parents=True, exist_ok=True)
    starter_file = destination / "starter.crn"
    if starter_file.exists() and not force:
        console.print(f"[red]Refusing to overwrite[/red] {starter_file}. Use --force.")
        raise typer.Exit(code=1)

    starter = """cairn: 1.0

loop:
  id: starter-loop
  name: Starter Loop
  version: 0.1.0
  description: Minimal Cairn loop scaffold
  inputs:
    message:
      type: string
      default: world
  outputs:
    greeting:
      value: ${{ states.finish.outputs.greeting }}
  budget:
    max_iterations: 3
    max_duration: 30s
  states:
    - id: prepare
      handler: core.template
      inputs:
        greeting: "hello ${{ inputs.message }}"
    - id: finish
      handler: core.collect
      inputs:
        greeting: ${{ states.prepare.outputs.greeting }}
  transitions:
    - from: prepare
      to: finish
"""
    starter_file.write_text(starter, encoding="utf-8")
    console.print(f"[green]Created[/green] {starter_file}")


@app.command()
def inspect(path: Path) -> None:
    """Show loop structure summary."""

    loop = load_loop_file(path)
    validate_loop_definition(loop)
    compiled = compile_loop(loop, target="langchain")
    console.print_json(
        data={
            "loop_id": loop.id,
            "name": loop.name,
            "version": loop.version,
            "imports": [{"name": item.name, "source": item.source} for item in loop.imports],
            "states": [
                {
                    "id": state.id,
                    "handler": state.handler,
                    "loop": state.loop_ref,
                    "transitions": [transition.to_state for transition in state.transitions],
                }
                for state in loop.states
            ],
            "transition_count": compiled.transition_count,
            "available_targets": sorted(get_builtin_plugins().keys()),
        }
    )


@app.command(name="trace")
def trace_command(path: Path) -> None:
    """Print saved execution trace or checkpoint JSON."""

    console.print_json(data=json.loads(path.read_text(encoding="utf-8")))


@app.command()
def publish(
    path: Path,
    registry: Path = typer.Option(DEFAULT_REGISTRY_PATH, "--registry", help="Local registry path"),
) -> None:
    """Publish loop to local CairnHub-style registry."""

    manifest = publish_loop(path, registry)
    console.print_json(data=manifest)


@app.command()
def install(
    ref: str,
    destination: Path = typer.Argument(..., help="Directory to install loop into"),
    registry: Path = typer.Option(DEFAULT_REGISTRY_PATH, "--registry", help="Local registry path"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing installed file"),
) -> None:
    """Install loop from local registry."""

    installed_path = install_loop(ref, destination, registry, force=force)
    console.print(f"[green]Installed[/green] {installed_path}")


@app.command(name="list")
def list_command(
    registry: Path = typer.Option(DEFAULT_REGISTRY_PATH, "--registry", help="Local registry path"),
) -> None:
    """List loops in local registry."""

    console.print_json(data={"loops": list_loops(registry)})


@app.command()
def search(
    query: str = typer.Argument(..., help="Free-text search query"),
    registry: Path = typer.Option(DEFAULT_REGISTRY_PATH, "--registry", help="Local registry path"),
) -> None:
    """Search loops in local registry."""

    console.print_json(data={"loops": search_loops(query, registry)})


@app.command(name="registry-inspect")
def registry_inspect(
    ref: str,
    registry: Path = typer.Option(DEFAULT_REGISTRY_PATH, "--registry", help="Local registry path"),
) -> None:
    """Inspect published loop manifest from local registry."""

    console.print_json(data=inspect_loop(ref, registry))


@app.command()
def cost(path: Path) -> None:
    """Estimate static loop cost envelope."""

    loop = load_loop_file(path)
    validate_loop_definition(loop)
    per_state = []
    total_state_cost = 0.0
    for state in loop.states:
        state_cost = float(state.raw.get("cost_usd", 0.0) or 0.0)
        total_state_cost += state_cost
        per_state.append({"state_id": state.id, "estimated_cost_usd": state_cost})
    console.print_json(
        data={
            "loop_id": loop.id,
            "estimated_state_cost_usd": total_state_cost,
            "budget_max_cost_usd": loop.budget.max_cost_usd,
            "max_iterations": loop.budget.max_iterations,
            "per_state": per_state,
        }
    )


@app.command()
def debug(
    path: Path,
    target: str = typer.Option("langchain", "--target", help="Execution target plugin"),
    input: list[str] = typer.Option(None, "--input", help="Loop input as key=value"),
    inputs_file: Path | None = typer.Option(None, "--inputs-file", help="JSON file with loop inputs"),
) -> None:
    """Run loop and print condensed debug summary."""

    loop = load_loop_file(path)
    result = execute_loop(loop, inputs=_load_inputs(input, inputs_file), target=target)
    console.print_json(
        data={
            "loop_id": result.loop_id,
            "success": result.success,
            "error": result.error,
            "states": [
                {"state_id": item.state_id, "skipped": item.skipped, "outputs": item.outputs}
                for item in result.state_results
            ],
            "metadata": result.metadata,
        }
    )
    if not result.success:
        raise typer.Exit(code=1)


@app.command(name="test")
def test_command(pytest_args: list[str] = typer.Argument(None)) -> None:
    """Run repo test suite."""

    args = ["python3", "-m", "pytest", "-q", *list(pytest_args or [])]
    completed = subprocess.run(args, check=False)
    if completed.returncode != 0:
        raise typer.Exit(code=completed.returncode)


@app.command()
def watch(
    path: Path,
    target: str = typer.Option("langchain", "--target", help="Execution target plugin"),
    input: list[str] = typer.Option(None, "--input", help="Loop input as key=value"),
    inputs_file: Path | None = typer.Option(None, "--inputs-file", help="JSON file with loop inputs"),
    interval: float = typer.Option(1.0, "--interval", help="Polling interval in seconds"),
    cycles: int = typer.Option(2, "--cycles", help="Number of reruns before exit"),
) -> None:
    """Hot-reload style loop runner for local iteration."""

    provided_inputs = _load_inputs(input, inputs_file)
    last_mtime = None
    remaining = cycles
    while remaining > 0:
        current_mtime = path.stat().st_mtime
        if last_mtime is None or current_mtime != last_mtime:
            loop = load_loop_file(path)
            result = execute_loop(loop, inputs=provided_inputs, target=target)
            console.print_json(data=_result_payload(result))
            last_mtime = current_mtime
            remaining -= 1
        if remaining > 0:
            time.sleep(interval)


@app.command()
def studio(
    host: str = typer.Option("127.0.0.1", "--host", help="Studio bind host"),
    port: int = typer.Option(8787, "--port", help="Studio bind port"),
) -> None:
    """Launch CairnStudio beta visual editor."""

    run_studio_server(host=host, port=port)


@app.command()
def hub(
    host: str = typer.Option("127.0.0.1", "--host", help="Hub bind host"),
    port: int = typer.Option(8790, "--port", help="Hub bind port"),
    registry: Path = typer.Option(Path(".cairnhub-hosted"), "--registry", help="Hosted registry path"),
) -> None:
    """Launch hosted CairnHub API with Lens and federated index endpoints."""

    run_hub_server(host=host, port=port, registry_path=registry)


if __name__ == "__main__":
    app()


def main() -> None:
    app()
