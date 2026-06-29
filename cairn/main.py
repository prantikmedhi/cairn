from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from cairnforge.executor import execute_loop
from cairnforge.parser import load_loop_file
from cairnforge.validator import CairnValidationError, validate_loop_definition

app = typer.Typer(help="Cairn CLI for loop validation and execution.")
console = Console()


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
) -> None:
    """Execute loop and print result JSON."""

    provided_inputs = _parse_key_values(input or [])
    if inputs_file is not None:
        provided_inputs.update(json.loads(inputs_file.read_text(encoding="utf-8")))

    loop = load_loop_file(path)
    result = execute_loop(loop, inputs=provided_inputs, target=target)
    console.print_json(
        data={
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
    )
    if not result.success:
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


if __name__ == "__main__":
    app()


def main() -> None:
    app()
