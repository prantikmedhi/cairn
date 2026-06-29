import sys
import types

from cairnforge.models import StateDefinition
from cairnforge.plugins.langgraph import LangGraphPlugin


def test_langgraph_plugin_uses_native_graph_when_available(monkeypatch) -> None:
    class FakeCompiledGraph:
        def __init__(self, fn):
            self.fn = fn

        def invoke(self, payload):
            return self.fn(payload)

    class FakeStateGraph:
        def __init__(self, _schema):
            self.fn = None

        def add_node(self, _name, fn):
            self.fn = fn

        def add_edge(self, _from, _to):
            return None

        def compile(self):
            return FakeCompiledGraph(self.fn)

    fake_module = types.ModuleType("langgraph.graph")
    fake_module.StateGraph = FakeStateGraph
    fake_module.START = "START"
    fake_module.END = "END"
    monkeypatch.setitem(sys.modules, "langgraph.graph", fake_module)

    plugin = LangGraphPlugin()
    state = StateDefinition(id="prepare", handler="core.collect", inputs={"x": 1})

    result = plugin.execute_state(state, {"x": 1}, {"current_condition": None})

    assert result == {"x": 1}
    assert plugin.get_metadata()["runtime_mode"] == "langgraph-native"


def test_langgraph_plugin_falls_back_without_langgraph(monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "langgraph.graph", raising=False)

    plugin = LangGraphPlugin()
    state = StateDefinition(id="prepare", handler="core.collect", inputs={"x": 1})

    result = plugin.execute_state(state, {"x": 1}, {"current_condition": None})

    assert result == {"x": 1}
    assert plugin.get_metadata()["runtime_mode"] == "builtin-fallback"
