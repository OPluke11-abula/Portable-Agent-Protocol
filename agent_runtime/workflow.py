"""Workflow DAG Execution Engine for Portable Agent Protocol.

This module provides the ability to parse workflow definitions from YAML front matter
and execute them as a Directed Acyclic Graph (DAG) with variable interpolation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .logger import get_logger

if TYPE_CHECKING:
    from .engine import AgentEngine

logger = get_logger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_INTERPOLATION_RE = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")


@dataclass
class Step:
    """Represents a single executable node in the Workflow DAG."""
    id: str
    tool: str | None = None
    action: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        return cls(
            id=data["id"],
            tool=data.get("tool"),
            action=data.get("action"),
            params=data.get("params", {}),
            depends_on=data.get("depends_on", []),
        )


class DAG:
    """Directed Acyclic Graph of Workflow Steps."""
    def __init__(self, steps: list[Step]):
        self.steps = {step.id: step for step in steps}
        self.adjacency: dict[str, list[str]] = {step.id: [] for step in steps}
        self.in_degree: dict[str, int] = {step.id: 0 for step in steps}

        # Build graph
        for step in steps:
            for dep in step.depends_on:
                if dep not in self.steps:
                    raise ValueError(f"Step '{step.id}' depends on unknown step '{dep}'")
                self.adjacency[dep].append(step.id)
                self.in_degree[step.id] += 1

    def topological_sort(self) -> list[Step]:
        """Return steps in executable order, raising ValueError on cycle."""
        queue = [step_id for step_id, degree in self.in_degree.items() if degree == 0]
        ordered_ids = []

        # We copy in_degree since we'll mutate it
        in_degree = self.in_degree.copy()

        while queue:
            current = queue.pop(0)
            ordered_ids.append(current)

            for neighbor in self.adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_ids) != len(self.steps):
            raise ValueError("Cycle detected in DAG or unresolved dependencies")

        return [self.steps[sid] for sid in ordered_ids]


class WorkflowExecutor:
    """Executes a parsed DAG using the AgentEngine capabilities."""

    def __init__(self, engine: AgentEngine):
        self.engine = engine

    def load(self, workflow_name: str) -> DAG:
        """Load and parse a DAG from a .agent/workflows/*.md file."""
        workflows_dir = self.engine.layout["directories"].get("workflows")
        if not workflows_dir:
            raise ValueError("Workflows directory not defined in agent layout")

        file_path = workflows_dir / f"{workflow_name}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        text = file_path.read_text(encoding="utf-8")
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise ValueError(f"No YAML front matter found in {file_path}")

        config = yaml.safe_load(match.group(1)) or {}
        steps_data = config.get("steps", [])
        
        steps = [Step.from_dict(s) for s in steps_data]
        return DAG(steps)

    def _interpolate(self, value: Any, context: dict[str, Any]) -> Any:
        """Recursively interpolate {{ var }} expressions in value using context."""
        if isinstance(value, str):
            def replacer(match: re.Match) -> str:
                path = match.group(1).split(".")
                curr = context
                try:
                    for key in path:
                        curr = curr[key]
                    return str(curr)
                except (KeyError, TypeError):
                    return match.group(0) # Unresolved
            
            # If the entire string is just one interpolation, preserve its type
            full_match = _INTERPOLATION_RE.fullmatch(value.strip())
            if full_match:
                path = full_match.group(1).split(".")
                curr = context
                try:
                    for key in path:
                        curr = curr[key]
                    return curr
                except (KeyError, TypeError):
                    return value

            return _INTERPOLATION_RE.sub(replacer, value)
            
        elif isinstance(value, dict):
            return {k: self._interpolate(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._interpolate(v, context) for v in value]
        else:
            return value

    def run_step(self, step: Step, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single step after interpolating parameters."""
        params = self._interpolate(step.params, context)
        logger.info("Executing workflow step: %s", step.id)
        
        if step.tool:
            # Route tool calls through the engine
            result = self.engine.run(step.tool, params)
            return {"output": result}
            
        elif step.action:
            # Handle built-in actions
            if step.action == "remember":
                key = params.get("key")
                val = params.get("value")
                if key:
                    self.engine.memory.write(key, val)
                return {"status": "success", "value": val}
                
            elif step.action == "respond":
                # For demo purposes, simply echo the constructed response
                return {"response": params}
                
            else:
                raise ValueError(f"Unknown action: {step.action}")
                
        else:
            raise ValueError(f"Step {step.id} has no tool or action defined")

    def run(self, dag: DAG, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute the DAG and return the final context."""
        execution_order = dag.topological_sort()
        context = {"inputs": inputs}

        logger.info("Starting workflow execution. Order: %s", [s.id for s in execution_order])

        for step in execution_order:
            result = self.run_step(step, context)
            context[step.id] = result

        logger.info("Workflow execution completed successfully.")
        return context
