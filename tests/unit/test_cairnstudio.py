import sys
import types

from cairnstudio.app import (
    add_comment,
    canvas_model_to_yaml,
    heartbeat_presence,
    load_activity,
    load_presence,
    load_session,
    preview_yaml_text,
    render_index_html,
    save_session,
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


def test_session_save_and_load(tmp_path, monkeypatch) -> None:
    from cairnstudio import app as studio_app

    monkeypatch.setattr(studio_app, "SESSION_DIR", tmp_path / "sessions")
    model = yaml_to_canvas_model(studio_app.STARTER_LOOP)
    saved = save_session("team-room", studio_app.STARTER_LOOP, model)
    loaded = load_session("team-room")

    assert saved["version"] == 1
    assert loaded["session_id"] == "team-room"
    assert loaded["yaml"] == studio_app.STARTER_LOOP


def test_presence_comments_and_activity(tmp_path, monkeypatch) -> None:
    from cairnstudio import app as studio_app

    monkeypatch.setattr(studio_app, "SESSION_DIR", tmp_path / "sessions")
    model = yaml_to_canvas_model(studio_app.STARTER_LOOP)
    save_session("room-one", studio_app.STARTER_LOOP, model, actor_id="alpha", actor_name="Alpha")

    presence = heartbeat_presence("room-one", "alpha", "Alpha")
    comment = add_comment("room-one", "alpha", "Alpha", "Need review on finish state")
    loaded_presence = load_presence("room-one")
    activity = load_activity("room-one")

    assert presence["count"] == 1
    assert loaded_presence["presence"][0]["actor_name"] == "Alpha"
    assert comment["comment"]["message"] == "Need review on finish state"
    assert any(item["kind"] == "save" for item in activity["activity"])
    assert any(item["kind"] == "comment" for item in activity["activity"])
    assert activity["comments"][0]["message"] == "Need review on finish state"
