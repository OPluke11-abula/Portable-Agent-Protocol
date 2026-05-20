"""State-machine-driven Workflow Execution Engine for Portable Agent Protocol.

This module provides the WorkflowEngine that parses workflow definitions, executes them
as Directed Acyclic Graphs (DAG) with variable interpolation, manages Turn-by-Turn state
transitions, maintains session checkpoints in persistent memory, and allows resumption
from failure checkpoints.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .logger import get_logger
from .workflow import DAG, Step, _FRONTMATTER_RE, _INTERPOLATION_RE

if TYPE_CHECKING:
    from .engine import AgentEngine

logger = get_logger(__name__)


@dataclass
class WorkflowSession:
    """Tracks state and context for a specific workflow execution session."""
    workflow_id: str
    session_id: str
    status: str  # "pending", "running", "success", "failed"
    inputs: dict[str, Any] = field(default_factory=dict)
    step_states: dict[str, dict[str, Any]] = field(default_factory=dict)  # step_id -> {"status": ..., "output": ..., "error": ...}
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowSession:
        return cls(
            workflow_id=data["workflow_id"],
            session_id=data["session_id"],
            status=data["status"],
            inputs=data.get("inputs", {}),
            step_states=data.get("step_states", {}),
            context=data.get("context", {}),
        )


class WorkflowEngine:
    """Manages stateful execution, persistence, failure writeback, and resumption of workflow DAGs."""

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
                    return match.group(0)  # Unresolved
            
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

    def _save_session(self, session: WorkflowSession) -> None:
        """Persist workflow session state to the engine memory backend."""
        key = f"workflow:{session.workflow_id}:session:{session.session_id}"
        self.engine.memory.write(key, session.to_dict())

    def _load_session(self, workflow_id: str, session_id: str) -> WorkflowSession | None:
        """Load workflow session state from the engine memory backend."""
        key = f"workflow:{workflow_id}:session:{session_id}"
        data = self.engine.memory.read(key)
        if not data:
            return None
        return WorkflowSession.from_dict(data)

    def run_step(self, step: Step, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single step after interpolating parameters."""
        params = self._interpolate(step.params, context)
        logger.info("Executing workflow step: %s", step.id)
        
        if step.tool:
            result = self.engine.run(step.tool, params)
            return {"output": result}
            
        elif step.action:
            if step.action == "remember":
                key = params.get("key")
                val = params.get("value")
                if key:
                    self.engine.memory.write(key, val)
                return {"status": "success", "value": val}
                
            elif step.action == "respond":
                return {"response": params}
                
            else:
                raise ValueError(f"Unknown action: {step.action}")
        else:
            raise ValueError(f"Step {step.id} has no tool or action defined")

    def run(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute the DAG and maintain persistent states."""
        dag = self.load(workflow_id)
        execution_order = dag.topological_sort()

        if not session_id:
            session_id = f"wf_session_{uuid.uuid4().hex[:12]}"

        # Initialize session state
        session = WorkflowSession(
            workflow_id=workflow_id,
            session_id=session_id,
            status="running",
            inputs=inputs,
            context={"inputs": inputs},
        )

        for step in execution_order:
            session.step_states[step.id] = {"status": "pending"}

        self._save_session(session)
        logger.info("Starting workflow execution. Session ID: %s", session_id)

        return self._execute_remaining_steps(dag, session, execution_order)

    def _execute_remaining_steps(
        self,
        dag: DAG,
        session: WorkflowSession,
        execution_order: list[Step],
    ) -> dict[str, Any]:
        """Executes outstanding steps in the topological execution list."""
        for step in execution_order:
            state = session.step_states[step.id]
            
            # Skip steps that already successfully executed (for resume)
            if state.get("status") == "success":
                continue

            # Verify if parent dependencies succeeded
            parent_failed = False
            for dep in step.depends_on:
                dep_state = session.step_states.get(dep, {})
                if dep_state.get("status") in ("failed", "skipped"):
                    parent_failed = True
                    break

            if parent_failed:
                state["status"] = "skipped"
                self._save_session(session)
                continue

            # Run step
            state["status"] = "running"
            self._save_session(session)

            try:
                result = self.run_step(step, session.context)
                state["status"] = "success"
                state["output"] = result
                session.context[step.id] = result
                self._save_session(session)
            except Exception as exc:
                state["status"] = "failed"
                state["error"] = str(exc)
                session.status = "failed"
                
                # Automatically transition transitive downstream dependents to skipped
                self._skip_downstream(dag, step.id, session.step_states)
                self._save_session(session)

                # Write failure logs to persistent memory
                err_key = f"workflow_error:{session.workflow_id}:{step.id}"
                self.engine.memory.write(
                    err_key,
                    {
                        "workflow_id": session.workflow_id,
                        "session_id": session.session_id,
                        "step_id": step.id,
                        "error": str(exc),
                    },
                )

                logger.error("Workflow step %s failed: %s", step.id, exc)
                raise ValueError(f"Workflow execution failed at step '{step.id}': {exc}")

        # Finalize success state if no steps failed
        has_failures = any(s["status"] == "failed" for s in session.step_states.values())
        session.status = "failed" if has_failures else "success"
        self._save_session(session)

        return session.context

    def _skip_downstream(self, dag: DAG, failed_step_id: str, step_states: dict[str, dict[str, Any]]) -> None:
        """Transitively mark all downstream dependent steps as skipped."""
        queue = [failed_step_id]
        visited = set()
        
        while queue:
            curr = queue.pop(0)
            visited.add(curr)
            
            # Find steps depending on current step
            for sid, step in dag.steps.items():
                if curr in step.depends_on and sid not in visited:
                    step_states[sid] = {"status": "skipped"}
                    queue.append(sid)

    def resume(
        self,
        workflow_id: str,
        session_id: str,
        step_id: str | None = None,
    ) -> dict[str, Any]:
        """Resumes workflow execution from a failed or specific step checkpoint."""
        session = self._load_session(workflow_id, session_id)
        if not session:
            raise ValueError(f"Workflow session '{session_id}' not found in persistent memory.")

        dag = self.load(workflow_id)
        execution_order = dag.topological_sort()

        # Find the checkpoint start step
        if step_id:
            if step_id not in session.step_states:
                raise ValueError(f"Resumption step '{step_id}' not defined in workflow '{workflow_id}'")
            start_step_id = step_id
        else:
            # Default to first failed or pending step
            start_step_id = None
            for step in execution_order:
                state = session.step_states.get(step.id, {})
                if state.get("status") in ("failed", "pending", "skipped"):
                    start_step_id = step.id
                    break

        if not start_step_id:
            logger.info("All workflow steps already succeeded. Nothing to resume.")
            return session.context

        logger.info("Resuming workflow session '%s' starting from step '%s'...", session_id, start_step_id)

        # Clear outputs of the start step and all downstream dependent steps to re-execute them
        downstream_to_reset = set()
        queue = [start_step_id]
        while queue:
            curr = queue.pop(0)
            downstream_to_reset.add(curr)
            for sid, step in dag.steps.items():
                if curr in step.depends_on and sid not in downstream_to_reset:
                    queue.append(sid)

        for sid in downstream_to_reset:
            session.step_states[sid] = {"status": "pending"}
            if sid in session.context:
                del session.context[sid]

        session.status = "running"
        self._save_session(session)

        return self._execute_remaining_steps(dag, session, execution_order)
