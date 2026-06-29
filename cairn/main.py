from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from cairnhub.local_registry import inspect_loop, install_loop, list_loops, publish_loop
from cairnforge.compiler import compile_loop
from cairnforge.executor import execute_loop, execute_loop_with_runtime_controls
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
) -> None:
    """Execute loop and print result JSON."""

    provided_inputs = _parse_key_values(input or [])
    if inputs_file is not None:
        provided_inputs.update(json.loads(inputs_file.read_text(encoding="utf-8")))

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


@app.command(name="registry-inspect")
def registry_inspect(
    ref: str,
    registry: Path = typer.Option(DEFAULT_REGISTRY_PATH, "--registry", help="Local registry path"),
) -> None:
    """Inspect published loop manifest from local registry."""

    console.print_json(data=inspect_loop(ref, registry))


if __name__ == "__main__":
    app()


def main() -> None:
    app()
