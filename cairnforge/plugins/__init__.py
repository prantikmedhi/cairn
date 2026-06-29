"""Built-in Cairn plugins."""

from .builtin_fallback import BuiltinFallbackPlugin
from .langchain import LangChainPlugin
from .langgraph import LangGraphPlugin


def get_builtin_plugins():
    return {
        "langchain": LangChainPlugin(),
        "langgraph": LangGraphPlugin(),
        "crewai": BuiltinFallbackPlugin("crewai"),
        "autogen": BuiltinFallbackPlugin("autogen"),
        "openai": BuiltinFallbackPlugin("openai"),
    }


__all__ = ["BuiltinFallbackPlugin", "LangChainPlugin", "LangGraphPlugin", "get_builtin_plugins"]
