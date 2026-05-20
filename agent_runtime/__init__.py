"""Portable Agent Runtime top-level package."""

__all__ = [
    "AgentEngine",
    "Router",
    "get_logger",
    "load_agent_config",
    "load_agent_layout",
    "MemoryBackend",
    "InMemoryBackend",
    "JSONFileBackend",
    "SQLiteBackend",
    "VectorDBBackend",
    "create_memory_backend",
    "WorkflowExecutor",
    "WorkflowEngine",
    "DAG",
    "Step",
    "KnowledgeBase",
    "PromptComposer",
    "SafePromptString",
    "validate_prompt_string",
]
__version__ = "0.1.0"


def __getattr__(name: str):
    """Lazily expose runtime symbols without forcing optional imports."""
    if name in {"AgentEngine", "load_agent_config", "load_agent_layout"}:
        from .engine import AgentEngine, load_agent_config, load_agent_layout

        values = {
            "AgentEngine": AgentEngine,
            "load_agent_config": load_agent_config,
            "load_agent_layout": load_agent_layout,
        }
        return values[name]

    if name == "Router":
        from .router import Router

        return Router

    if name == "get_logger":
        from .logger import get_logger

        return get_logger

    if name in {
        "MemoryBackend",
        "InMemoryBackend",
        "JSONFileBackend",
        "SQLiteBackend",
        "VectorDBBackend",
        "create_memory_backend",
    }:
        from . import memory

        return getattr(memory, name)

    if name in {"WorkflowExecutor", "DAG", "Step", "WorkflowEngine"}:
        if name == "WorkflowEngine":
            from .workflow_engine import WorkflowEngine
            return WorkflowEngine
        from .workflow import DAG, Step, WorkflowExecutor

        values = {"WorkflowExecutor": WorkflowExecutor, "DAG": DAG, "Step": Step}
        return values[name]

    if name == "KnowledgeBase":
        from .knowledge import KnowledgeBase

        return KnowledgeBase

    if name in {"PromptComposer", "SafePromptString", "validate_prompt_string"}:
        from .prompt_composer import PromptComposer, SafePromptString, validate_prompt_string

        values = {
            "PromptComposer": PromptComposer,
            "SafePromptString": SafePromptString,
            "validate_prompt_string": validate_prompt_string,
        }
        return values[name]

    raise AttributeError(f"module 'agent_runtime' has no attribute {name!r}")
