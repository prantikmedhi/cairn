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
