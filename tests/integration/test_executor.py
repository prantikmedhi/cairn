from pathlib import Path

from cairnforge.executor import execute_loop, execute_loop_with_runtime_controls
from cairnforge.parser import load_loop_file


def test_executor_runs_happy_path() -> None:
    loop = load_loop_file(Path("cairnlang/examples/hello-world.crn"))

    result = execute_loop(loop, inputs={"message": "builder"})

    assert result.success is True
    assert result.final_outputs == {"greeting": "hello builder"}
    assert [state.state_id for state in result.state_results] == ["prepare", "finish"]
    assert result.metadata["runtime_mode"] == "builtin-fallback"


def test_executor_runs_branching_path() -> None:
    loop = load_loop_file(Path("cairnlang/examples/branching-review.crn"))

    result = execute_loop(loop, inputs={"approved": False, "score": 0.11})

    assert result.success is True
    assert result.final_outputs == {"status": "rejected", "score": 0.11}
    assert [state.state_id for state in result.state_results] == ["analyze", "route", "rejected", "finish"]


def test_executor_runs_budget_hook() -> None:
    loop = load_loop_file(Path("cairnlang/examples/budget-guard.crn"))

    result = execute_loop(loop)

    assert result.success is False
    assert result.error == "Loop exceeded max_iterations budget"
    assert result.final_outputs == {"status": "budget_exceeded"}


def test_executor_runs_error_hook() -> None:
    loop = load_loop_file(Path("cairnlang/examples/failure-hook.crn"))

    result = execute_loop(loop)

    assert result.success is False
    assert result.error == "forced failure"
    assert result.final_outputs == {"status": "recovered"}


def test_executor_runs_local_subloop() -> None:
    loop = load_loop_file(Path("cairnlang/examples/composed-hello.crn"))

    result = execute_loop(loop, inputs={"name": "phase-two"})

    assert result.success is True
    assert result.final_outputs == {"greeting": "hello phase-two"}
    assert [state.state_id for state in result.state_results] == ["greet"]


def test_executor_can_checkpoint_and_resume(tmp_path: Path) -> None:
    loop = load_loop_file(Path("cairnlang/examples/data-pipeline.crn"))
    checkpoint_file = tmp_path / "pipeline-checkpoint.json"

    paused = execute_loop_with_runtime_controls(
        loop,
        checkpoint_path=checkpoint_file,
        max_steps=1,
    )

    assert paused.success is False
    assert paused.metadata["paused"] is True
    assert checkpoint_file.exists()

    resumed = execute_loop_with_runtime_controls(
        loop,
        resume_from=checkpoint_file,
    )

    assert resumed.success is True
    assert resumed.final_outputs["destination"] == "warehouse://normalized:orders.csv"
