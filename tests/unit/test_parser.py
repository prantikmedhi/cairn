from pathlib import Path

from cairnforge.parser import load_loop_file


def test_load_example_loop() -> None:
    loop = load_loop_file(Path("cairnlang/examples/hello-world.crn"))

    assert loop.id == "hello-world"
    assert [state.id for state in loop.states] == ["prepare", "finish"]
    assert loop.budget.max_iterations == 3
