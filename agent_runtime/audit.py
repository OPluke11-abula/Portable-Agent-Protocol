"""Agent self-audit diagnostic workflow checking workspace health and schema integrity."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import yaml

from .engine import AgentEngine, _project_root_from_config
from .logger import get_logger

logger = get_logger(__name__)


def _parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
    """Parse YAML front-matter from a markdown file."""
    if not file_path.exists():
        return None
    try:
        text = file_path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
    except Exception as e:
        logger.warning("Failed to parse front-matter for %s: %s", file_path, e)
    return None


def _load_schema(project_root: Path, schema_name: str) -> dict[str, Any] | None:
    """Find and load JSON Schema by name."""
    for folder in ("spec", "schemas"):
        schema_path = project_root / folder / schema_name
        if schema_path.exists():
            try:
                return json.loads(schema_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to parse schema %s: %s", schema_path, e)
    return None


class AgentSelfAuditor:
    """Runs diagnostics checks over skill contracts, memory tiers, and active workflows."""

    def __init__(
        self,
        engine: AgentEngine,
        memory_size_threshold: int = 2 * 1024 * 1024,  # 2MB
        handoff_count_threshold: int = 10,
        workflow_abandoned_threshold_seconds: int = 86400,  # 24 hours
    ) -> None:
        self.engine = engine
        self.memory_size_threshold = memory_size_threshold
        self.handoff_count_threshold = handoff_count_threshold
        self.workflow_abandoned_threshold_seconds = workflow_abandoned_threshold_seconds

    def run_audit(self) -> dict[str, Any]:
        """Perform the self-audit diagnostic checks and return a structured report."""
        project_root = _project_root_from_config(self.engine.config_path)
        issues = []
        recommendations = []

        # -------------------------------------------------------------
        # 1. Skill Contract Checks
        # -------------------------------------------------------------
        tools = self.engine.config.get("tools", [])
        skills_dir = self.engine.layout.get("directories", {}).get("skills")

        # Load skill contract schema if available
        skill_schema = _load_schema(project_root, "skill-contract.schema.json")

        for tool_id in tools:
            if not skills_dir:
                issues.append({
                    "type": "missing_contract",
                    "id": tool_id,
                    "details": "Skills directory is not defined in agent layout config."
                })
                continue

            contract_path = Path(skills_dir) / f"{tool_id}.md"
            if not contract_path.exists():
                issues.append({
                    "type": "missing_contract",
                    "id": tool_id,
                    "details": f"Skill contract markdown file is missing under {skills_dir}."
                })
                recommendations.append({
                    "task_id": f"create_skill_contract_{tool_id}",
                    "description": f"Create a declarative skill contract for '{tool_id}' under {skills_dir}",
                    "priority": "HIGH"
                })
                continue

            contract_data = _parse_frontmatter(contract_path)
            if not contract_data:
                issues.append({
                    "type": "outdated_or_invalid_contract",
                    "id": tool_id,
                    "details": f"Failed to parse YAML front-matter inside skill contract '{tool_id}'."
                })
                recommendations.append({
                    "task_id": f"fix_skill_contract_{tool_id}",
                    "description": f"Fix malformed YAML front-matter in skill contract '{tool_id}'",
                    "priority": "HIGH"
                })
                continue

            # Validate against skill-contract schema if jsonschema is available
            if skill_schema:
                try:
                    import jsonschema
                    jsonschema.validate(instance=contract_data, schema=skill_schema)
                except ImportError:
                    pass
                except Exception as e:
                    issues.append({
                        "type": "outdated_or_invalid_contract",
                        "id": tool_id,
                        "details": f"Skill contract '{tool_id}' failed schema validation: {e}"
                    })
                    recommendations.append({
                        "task_id": f"align_skill_schema_{tool_id}",
                        "description": f"Fix schema validation errors in skill contract '{tool_id}'",
                        "priority": "MEDIUM"
                    })

            # Check for outdated versions (< 1.0.0 or invalid semver)
            version_str = str(contract_data.get("version", ""))
            if not version_str:
                issues.append({
                    "type": "outdated_or_invalid_contract",
                    "id": tool_id,
                    "details": f"Skill contract '{tool_id}' is missing a version identifier."
                })
            else:
                try:
                    parts = [int(p) for p in version_str.split(".")]
                    if len(parts) < 3 or parts[0] < 1:
                        issues.append({
                            "type": "outdated_or_invalid_contract",
                            "id": tool_id,
                            "details": f"Skill contract '{tool_id}' version '{version_str}' is outdated (must be >= 1.0.0)."
                        })
                        recommendations.append({
                            "task_id": f"upgrade_skill_version_{tool_id}",
                            "description": f"Upgrade skill contract '{tool_id}' version to 1.0.0+",
                            "priority": "MEDIUM"
                        })
                except ValueError:
                    issues.append({
                        "type": "outdated_or_invalid_contract",
                        "id": tool_id,
                        "details": f"Skill contract '{tool_id}' version '{version_str}' has invalid semver format."
                    })

        # -------------------------------------------------------------
        # 2. Memory Size Checks
        # -------------------------------------------------------------
        mem_file_size = 0
        mem_dir = self.engine.layout.get("directories", {}).get("memory")
        if mem_dir:
            mem_path = Path(mem_dir)
            # 1. Local JSON memory backend size check
            json_file = mem_path / "memory.json"
            if json_file.exists():
                mem_file_size = json_file.stat().st_size
                if mem_file_size > self.memory_size_threshold:
                    issues.append({
                        "type": "memory_size_exceeded",
                        "id": "memory.json",
                        "details": f"Episodic/session store memory.json size ({mem_file_size} bytes) exceeds threshold ({self.memory_size_threshold} bytes)."
                    })
                    recommendations.append({
                        "task_id": "cleanup_memory_store",
                        "description": "Compress, archive, or purge old entries in memory.json",
                        "priority": "HIGH"
                    })

            # 2. Handoff file count check
            handoff_dir = mem_path / "handoff"
            handoff_count = 0
            if handoff_dir.exists():
                handoff_files = list(handoff_dir.glob("*.json"))
                handoff_count = len(handoff_files)
                if handoff_count > self.handoff_count_threshold:
                    issues.append({
                        "type": "too_many_handoff_files",
                        "id": "handoff",
                        "details": f"Accumulated handoff files count ({handoff_count}) exceeds threshold ({self.handoff_count_threshold})."
                    })
                    recommendations.append({
                        "task_id": "cleanup_handoff_files",
                        "description": "Purge expired handoff context files under .agent/memory/handoff/",
                        "priority": "MEDIUM"
                    })
        else:
            handoff_count = 0

        # -------------------------------------------------------------
        # 3. Workflow Session Abandonment Checks
        # -------------------------------------------------------------
        runs_dir = project_root / "runs"
        abandoned_runs = []
        if runs_dir.exists():
            for run_file in runs_dir.glob("*.json"):
                try:
                    mtime = run_file.stat().st_mtime
                    age = time.time() - mtime
                    if age > self.workflow_abandoned_threshold_seconds:
                        # Load file to inspect status
                        data = json.loads(run_file.read_text(encoding="utf-8"))
                        status = data.get("status")
                        if status in ("running", "pending", "paused"):
                            session_id = run_file.stem
                            abandoned_runs.append(session_id)
                            issues.append({
                                "type": "abandoned_workflow_run",
                                "id": session_id,
                                "details": f"Workflow run session '{session_id}' status is '{status}' and was abandoned {age / 3600:.1f} hours ago."
                            })
                            recommendations.append({
                                "task_id": f"cleanup_workflow_session_{session_id}",
                                "description": f"Resume or clean up abandoned workflow run session '{session_id}' under runs/",
                                "priority": "LOW"
                            })
                except Exception as e:
                    logger.debug("Failed to inspect workflow run file %s: %s", run_file, e)

        # -------------------------------------------------------------
        # 4. Generate JSON Report
        # -------------------------------------------------------------
        report = {
            "semantic": {
                "key": "audit_log",
                "value": {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "summary": {
                        "skills_checked": len(tools),
                        "skills_issues": sum(1 for issue in issues if "contract" in issue["type"]),
                        "memory_size_bytes": mem_file_size,
                        "handoff_count": handoff_count,
                        "abandoned_workflows": len(abandoned_runs)
                    },
                    "issues": issues,
                    "recommendations": recommendations
                },
                "metadata": {
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "tags": ["audit", "system-health"]
                }
            }
        }

        # Write to semantic memory
        if mem_dir:
            semantic_dir = Path(mem_dir) / "semantic"
            semantic_dir.mkdir(parents=True, exist_ok=True)
            report_file = semantic_dir / "audit_log.json"
            try:
                report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
                logger.info("Saved self-audit diagnostic log to %s", report_file)
            except Exception as e:
                logger.warning("Failed to save self-audit report file: %s", e)

        # Validate against schema if jsonschema is available
        memory_schema = _load_schema(project_root, "memory.schema.json")
        if memory_schema:
            try:
                import jsonschema
                jsonschema.validate(instance=report, schema=memory_schema)
            except ImportError:
                pass
            except Exception as e:
                logger.warning("Generated audit report failed memory schema validation: %s", e)

        return report
