from pathlib import Path

from typer.testing import CliRunner

from cairn.main import app

runner = CliRunner()


def test_validate_command() -> None:
    result = runner.invoke(app, ["validate", "cairnlang/examples/hello-world.crn"])

    assert result.exit_code == 0
    assert "Valid loop: hello-world" in result.stdout


def test_run_command() -> None:
    result = runner.invoke(app, ["run", "cairnlang/examples/hello-world.crn", "--input", "message=forge"])

    assert result.exit_code == 0
    assert '"greeting": "hello forge"' in result.stdout


def test_init_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / "starter.crn").exists()


def test_run_command_can_write_trace_and_checkpoint(tmp_path: Path) -> None:
    checkpoint_file = tmp_path / "checkpoint.json"
    trace_file = tmp_path / "trace.json"

    result = runner.invoke(
        app,
        [
            "run",
            "cairnlang/examples/data-pipeline.crn",
            "--checkpoint-file",
            str(checkpoint_file),
            "--trace-file",
            str(trace_file),
            "--max-steps",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert checkpoint_file.exists()
    assert trace_file.exists()
    assert '"paused": true' in trace_file.read_text()


def test_publish_install_list_and_registry_inspect_commands(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    install_dir = tmp_path / "installed"

    publish_result = runner.invoke(
        app,
        ["publish", "cairnlang/examples/hello-world.crn", "--registry", str(registry)],
    )
    assert publish_result.exit_code == 0
    assert '"id": "hello-world"' in publish_result.stdout

    list_result = runner.invoke(app, ["list", "--registry", str(registry)])
    assert list_result.exit_code == 0
    assert '"hello-world"' in list_result.stdout

    inspect_result = runner.invoke(app, ["registry-inspect", "hello-world@0.1.0", "--registry", str(registry)])
    assert inspect_result.exit_code == 0
    assert '"version": "0.1.0"' in inspect_result.stdout

    install_result = runner.invoke(
        app,
        ["install", "hello-world@0.1.0", str(install_dir), "--registry", str(registry)],
    )
    assert install_result.exit_code == 0
    assert (install_dir / "hello-world.crn").exists()


def test_inspect_command() -> None:
    result = runner.invoke(app, ["inspect", "cairnlang/examples/composed-hello.crn"])

    assert result.exit_code == 0
    assert '"loop_id": "composed-hello"' in result.stdout
