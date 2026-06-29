import sys
import types

from cairnforge.expression import render_value


def test_render_value_uses_jinja_when_available(monkeypatch) -> None:
    class FakeTemplate:
        def __init__(self, source: str):
            self.source = source

        def render(self, context):
            return self.source.replace("{{ inputs.name }}", str(context["inputs"]["name"]))

    class FakeEnvironment:
        def __init__(self, autoescape: bool):
            self.autoescape = autoescape

        def from_string(self, source: str):
            return FakeTemplate(source)

    fake_module = types.ModuleType("jinja2")
    fake_module.Environment = FakeEnvironment
    monkeypatch.setitem(sys.modules, "jinja2", fake_module)

    rendered = render_value("hello {{ inputs.name }}", {"inputs": {"name": "builder"}})

    assert rendered == "hello builder"
