from pathlib import Path

import pytest

from cairnforge.parser import load_loop_file
from cairnforge.validator import CairnValidationError, validate_loop_definition


def test_validator_rejects_missing_transition_target() -> None:
    loop = load_loop_file(Path("tests/fixtures/invalid-transition.crn"))

    with pytest.raises(CairnValidationError, match="Transition target 'missing' does not exist"):
        validate_loop_definition(loop)
