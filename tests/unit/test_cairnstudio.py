import sys
import types

from cairnstudio.app import (
    canvas_model_to_yaml,
    preview_yaml_text,
    render_index_html,
    validate_yaml_text,
    yaml_to_canvas_model,
)


def _install_fake_jinja(monkeypatch) -> None:
    class FakeTemplate:
        def render(self, context):
            return f"<html><title>{context['page_title']}</title><body>{context['phase_badge']}</body></html>"

    class FakeEnvironment:
        def __init__(self, **_kwargs):
            pass

        def get_template(self, _name):
            return FakeTemplate()

    fake_module = types.ModuleType("jinja2")
    fake_module.Environment = FakeEnvironment
    fake_module.FileSystemLoader = lambda *_args, **_kwargs: None
    fake_module.select_autoescape = lambda *_args, **_kwargs: None
    monkeypatch.setitem(sys.modules, "jinja2", fake_module)


def test_render_index_html(monkeypatch) -> None:
    _install_fake_jinja(monkeypatch)

    html = render_index_html()

    assert "CairnStudio Beta" in html
    assert "Phase 4 Beta" in html


def test_yaml_to_canvas_model_and_back() -> None:
    yaml_text = """
cairn: "1.0"
loop:
  id: sample-loop
  name: Sample Loop
  version: 0.1.0
  states:
    - id: alpha
      handler: core.collect
      inputs:
        value: one
"""
    model = yaml_to_canvas_model(yaml_text)
    rebuilt_yaml = canvas_model_to_yaml(model)

    assert model["loop"]["states"][0]["id"] == "alpha"
    assert "sample-loop" in rebuilt_yaml


def test_validate_and_preview_yaml_text() -> None:
    yaml_text = """
cairn: "1.0"
loop:
  id: preview-loop
  name: Preview Loop
  version: 0.1.0
  outputs:
    result:
      value: ${{ states.finish.outputs.value }}
  states:
    - id: finish
      handler: core.collect
      inputs:
        value: ok
"""
    validated = validate_yaml_text(yaml_text)
    preview = preview_yaml_text(yaml_text)

    assert validated["valid"] is True
    assert preview["success"] is True
    assert preview["final_outputs"] == {"result": "ok"}
