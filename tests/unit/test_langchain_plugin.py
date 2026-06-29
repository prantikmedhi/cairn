import sys
import types

from cairnforge.plugins.langchain import LangChainPlugin
from cairnforge.models import StateDefinition


def test_langchain_plugin_uses_runnable_lambda_when_available(monkeypatch) -> None:
    events: list[dict] = []

    class FakeRunnableLambda:
        def __init__(self, fn):
            self.fn = fn

        def invoke(self, payload):
            events.append(payload)
            return self.fn(payload)

    fake_module = types.ModuleType("langchain_core.runnables")
    fake_module.RunnableLambda = FakeRunnableLambda
    monkeypatch.setitem(sys.modules, "langchain_core.runnables", fake_module)

    plugin = LangChainPlugin()
    state = StateDefinition(id="prepare", handler="core.collect", inputs={"x": 1})

    result = plugin.execute_state(state, {"x": 1}, {"current_condition": None})

    assert result == {"x": 1}
    assert events[0]["state"] == "prepare"
    assert plugin.get_metadata()["runtime_mode"] == "langchain-core"


def test_langchain_plugin_falls_back_without_langchain(monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "langchain_core.runnables", raising=False)

    plugin = LangChainPlugin()
    state = StateDefinition(id="prepare", handler="core.collect", inputs={"x": 1})

    result = plugin.execute_state(state, {"x": 1}, {"current_condition": None})

    assert result == {"x": 1}
    assert plugin.get_metadata()["runtime_mode"] == "builtin-fallback"
