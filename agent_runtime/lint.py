"""Workspace linter implementation for the Portable Agent Protocol."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None

from agent_runtime.engine import _project_root_from_config


class LintIssue:
    def __init__(
        self,
        severity: str,
        file_path: Path | str,
        message: str,
        line: int | None = None,
        fixable: bool = False,
        suggestion: str | None = None,
        fix_type: str | None = None,
        fix_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.severity = severity  # 'error', 'warning', 'info'
        self.file_path = Path(file_path)
        self.message = message
        self.line = line
        self.fixable = fixable
        self.suggestion = suggestion
        self.fix_type = fix_type
        self.fix_metadata = fix_metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "file_path": str(self.file_path),
            "message": self.message,
            "line": self.line,
            "fixable": self.fixable,
            "suggestion": self.suggestion,
        }


def find_line_for_key(file_content: str, key: str) -> int | None:
    """Find the line number of a key in YAML/markdown content."""
    lines = file_content.splitlines()
    for idx, line in enumerate(lines):
        striped = line.strip()
        if striped.startswith(f"{key}:") or striped.startswith(f'"{key}":') or striped.startswith(f"'{key}':"):
            return idx + 1
        if striped.startswith("-") and key in striped:
            return idx + 1
    return None


def parse_front_matter(content: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse YAML front matter from a markdown file."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, "No YAML front-matter found."
    try:
        data = yaml.safe_load(match.group(1)) or {}
        return data, None
    except Exception as e:
        return None, f"Failed to parse YAML front-matter: {e}"


def check_semver(val: str) -> bool:
    """Verify that a string is a valid semver version."""
    if not isinstance(val, str):
        return False
    return bool(re.match(r"^v?\d+\.\d+\.\d+$", val))


def clean_version(version: str) -> str:
    """Clean and normalize a version to valid semver."""
    prefix = "v" if version.startswith("v") else ""
    cleaned = re.sub(r"[^\d.]", "", version)
    if not cleaned:
        return "0.1.0"
    parts = cleaned.split(".")
    while len(parts) < 3:
        parts.append("0")
    return prefix + ".".join(parts[:3])


class WorkspaceLinter:
    def __init__(self, config_path: str | Path = ".agent/agent.md") -> None:
        self.config_path = Path(config_path)
        self.project_root = _project_root_from_config(self.config_path)
        self.agent_dir = self.config_path.parent
        self.issues: list[LintIssue] = []

    def _load_schema(self, schema_filename: str) -> dict[str, Any] | None:
        """Locate and load JSON Schema file."""
        for folder in ("spec", "schemas"):
            path = self.project_root / folder / schema_filename
            if path.exists():
                try:
                    with path.open(encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return None

    def run_all_checks(self) -> list[LintIssue]:
        self.issues.clear()
        
        # 1. Schema Validation & Versions for agent.md
        self.check_agent_manifest()

        # 2. Check catalog entry files
        self.check_catalog_indexes()

        # 3. Check individual skill contracts
        self.check_skill_contracts()

        # 4. Check workflow files & DAG
        self.check_workflows()

        # 5. Decoupling Static Linter checks (Task 2-06)
        self.check_decoupling()

        return self.issues

    def check_agent_manifest(self) -> None:
        if not self.config_path.exists():
            self.issues.append(
                LintIssue(
                    severity="error",
                    file_path=self.config_path,
                    message="Manifest file not found.",
                )
            )
            return

        try:
            content = self.config_path.read_text(encoding="utf-8")
        except Exception as e:
            self.issues.append(
                LintIssue(
                    severity="error",
                    file_path=self.config_path,
                    message=f"Failed to read file: {e}",
                )
            )
            return

        data, err = parse_front_matter(content)
        if err:
            self.issues.append(
                LintIssue(
                    severity="error",
                    file_path=self.config_path,
                    message=err,
                )
            )
            return

        # Check version fields
        for vkey in ("protocol_version", "min_runtime_version", "version"):
            val = data.get(vkey)
            if val is not None and not check_semver(str(val)):
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=self.config_path,
                        message=f"Invalid version format in '{vkey}': '{val}'. Must be semver format.",
                        line=find_line_for_key(content, vkey),
                        fixable=True,
                        suggestion=f"Convert '{val}' to '{clean_version(str(val))}'",
                        fix_type="fix_version_format",
                        fix_metadata={"file_path": str(self.config_path), "key": vkey, "old_val": val},
                    )
                )

        # Validate Schema
        schema = self._load_schema("agent-schema.json")
        if schema and jsonschema:
            try:
                jsonschema.validate(instance=data, schema=schema)
            except jsonschema.ValidationError as ve:
                path_str = ".".join(str(p) for p in ve.path)
                message = f"Schema validation error at protocol.{path_str}: {ve.message}"
                key = ve.path[0] if ve.path else "protocol"
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=self.config_path,
                        message=message,
                        line=find_line_for_key(content, str(key)),
                    )
                )

    def check_catalog_indexes(self) -> None:
        catalog_files = ["skills.md", "prompts.md", "memory.md", "workflows.md"]
        for filename in catalog_files:
            file_path = self.agent_dir / filename
            if not file_path.exists():
                # Not strictly an error but warning
                self.issues.append(
                    LintIssue(
                        severity="warning",
                        file_path=file_path,
                        message=f"Catalog index file '{filename}' is missing.",
                    )
                )
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=f"Failed to read file: {e}",
                    )
                )
                continue

            data, err = parse_front_matter(content)
            if err:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=err,
                    )
                )
                continue

            # Verify schema_version is present and semver
            sv = data.get("schema_version")
            if sv is None:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message="Missing required field 'schema_version' in front-matter.",
                        line=1,
                    )
                )
            elif not check_semver(str(sv)):
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=f"Invalid 'schema_version' format: '{sv}'. Must be semver format.",
                        line=find_line_for_key(content, "schema_version"),
                        fixable=True,
                        suggestion=f"Convert '{sv}' to '{clean_version(str(sv))}'",
                        fix_type="fix_version_format",
                        fix_metadata={"file_path": str(file_path), "key": "schema_version", "old_val": sv},
                    )
                )

    def check_skill_contracts(self) -> None:
        # Load active tools listed in manifest
        tools_list = []
        if self.config_path.exists():
            try:
                content = self.config_path.read_text(encoding="utf-8")
                data, _ = parse_front_matter(content)
                if data:
                    tools_list = data.get("tools") or []
            except Exception:
                pass

        skills_dir = self.agent_dir / "skills"
        if not skills_dir.is_dir():
            self.issues.append(
                LintIssue(
                    severity="error",
                    file_path=skills_dir,
                    message="Skills directory '.agent/skills/' is missing.",
                )
            )
            return

        # 1. Warn on missing skill contract files for declared tools, masking global-only skills
        from agent_runtime.tool_manifest import ToolManifest
        manifest = ToolManifest(local_skills_dir=skills_dir)
        global_skills = manifest.list_global()

        for tool in tools_list:
            contract_path = skills_dir / f"{tool}.md"
            if not contract_path.exists():
                if tool in global_skills:
                    continue
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=contract_path,
                        message=f"Skill contract file for declared tool '{tool}' is missing.",
                        fixable=True,
                        suggestion=f"Create boilerplate contract for skill '{tool}'",
                        fix_type="create_skill_file",
                        fix_metadata={"skill_name": tool},
                    )
                )

        # 2. Check each skill contract file
        schema = self._load_schema("skill-contract.schema.json")
        for file_path in skills_dir.glob("*.md"):
            if file_path.name in ("_template.md", "__init__.md"):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=f"Failed to read file: {e}",
                    )
                )
                continue

            data, err = parse_front_matter(content)
            if err:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=err,
                    )
                )
                continue

            # Validate against schema
            if schema and jsonschema:
                try:
                    jsonschema.validate(instance=data, schema=schema)
                except jsonschema.ValidationError as ve:
                    path_str = ".".join(str(p) for p in ve.path)
                    message = f"Schema validation error at {path_str}: {ve.message}"
                    key = ve.path[0] if ve.path else "id"
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=message,
                            line=find_line_for_key(content, str(key)),
                        )
                    )

            skill_id = data.get("id")
            if skill_id:
                # Check version field
                ver = data.get("version")
                if ver is not None and not check_semver(str(ver)):
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Invalid version format in 'version': '{ver}'.",
                            line=find_line_for_key(content, "version"),
                            fixable=True,
                            suggestion=f"Convert '{ver}' to '{clean_version(str(ver))}'",
                            fix_type="fix_version_format",
                            fix_metadata={"file_path": str(file_path), "key": "version", "old_val": ver},
                        )
                    )

                # Warn if skill exists but not registered in agent.md tools list
                if skill_id not in tools_list:
                    self.issues.append(
                        LintIssue(
                            severity="warning",
                            file_path=file_path,
                            message=f"Skill '{skill_id}' is defined but not registered in agent.md 'tools'.",
                            fixable=True,
                            suggestion=f"Add skill '{skill_id}' to agent.md tools list",
                            fix_type="add_tool_to_manifest",
                            fix_metadata={"skill_name": skill_id},
                        )
                    )

    def check_workflows(self) -> None:
        workflows_dir = self.agent_dir / "workflows"
        if not workflows_dir.is_dir():
            return

        schema = self._load_schema("workflow.schema.json")
        for file_path in workflows_dir.glob("*.md"):
            if file_path.name == "__init__.md":
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=f"Failed to read file: {e}",
                    )
                )
                continue

            data, err = parse_front_matter(content)
            if err:
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=err,
                    )
                )
                continue

            if schema and jsonschema:
                try:
                    jsonschema.validate(instance=data, schema=schema)
                except jsonschema.ValidationError as ve:
                    path_str = ".".join(str(p) for p in ve.path)
                    message = f"Schema validation error at {path_str}: {ve.message}"
                    key = ve.path[0] if ve.path else "steps"
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=message,
                            line=find_line_for_key(content, str(key)),
                        )
                    )
                    continue

            # DAG steps checking
            steps = data.get("steps") or []
            if not steps:
                continue

            # Verify step ID uniqueness
            seen_ids = set()
            has_duplicates = False
            for step in steps:
                sid = step.get("id")
                if not sid:
                    continue
                if sid in seen_ids:
                    has_duplicates = True
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Duplicate step ID '{sid}' in workflow.",
                            line=find_line_for_key(content, sid),
                        )
                    )
                seen_ids.add(sid)

            if has_duplicates:
                continue

            # Verify dependencies exist
            adj: dict[str, list[str]] = {}
            for step in steps:
                sid = step["id"]
                deps = step.get("depends_on") or []
                adj[sid] = []
                for d in deps:
                    if d not in seen_ids:
                        self.issues.append(
                            LintIssue(
                                severity="error",
                                file_path=file_path,
                                message=f"Step '{sid}' depends on non-existent step '{d}'.",
                                line=find_line_for_key(content, sid),
                            )
                        )
                    else:
                        adj[sid].append(d)

            # Cycle detection (DFS coloring)
            visited = {sid: 0 for sid in seen_ids}  # 0=unvisited, 1=visiting, 2=visited
            cycle_found = []

            def dfs(node: str, path: list[str]) -> bool:
                visited[node] = 1
                path.append(node)
                for neighbor in adj.get(node, []):
                    if visited.get(neighbor, 0) == 1:
                        cycle_idx = path.index(neighbor)
                        cycle_found.extend(path[cycle_idx:])
                        cycle_found.append(neighbor)
                        return True
                    elif visited.get(neighbor, 0) == 0:
                        if dfs(neighbor, path):
                            return True
                path.pop()
                visited[node] = 2
                return False

            for sid in seen_ids:
                if visited[sid] == 0:
                    if dfs(sid, []):
                        break

            if cycle_found:
                cycle_str = " -> ".join(cycle_found)
                self.issues.append(
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        message=f"Circular dependency detected in workflow steps: {cycle_str}",
                        line=find_line_for_key(content, cycle_found[0]),
                    )
                )

            # Compute transitive ancestors
            ancestors: dict[str, set[str]] = {}
            for sid in seen_ids:
                nodes_to_visit = list(adj.get(sid, []))
                seen = set(nodes_to_visit)
                while nodes_to_visit:
                    curr = nodes_to_visit.pop(0)
                    for d in adj.get(curr, []):
                        if d not in seen:
                            seen.add(d)
                            nodes_to_visit.append(d)
                ancestors[sid] = seen

            # Check parameter inputs interpolation references
            def check_references(val: Any, step_id: str) -> None:
                if isinstance(val, str):
                    # Find all references to steps.XXX
                    matches = re.findall(r"steps\.([a-zA-Z0-9_-]+)", val)
                    for ref_step in matches:
                        if ref_step not in seen_ids:
                            self.issues.append(
                                LintIssue(
                                    severity="error",
                                    file_path=file_path,
                                    message=f"Step '{step_id}' references output of non-existent step '{ref_step}'.",
                                    line=find_line_for_key(content, step_id),
                                )
                            )
                        elif ref_step != step_id and ref_step not in ancestors.get(step_id, set()):
                            self.issues.append(
                                LintIssue(
                                    severity="warning",
                                    file_path=file_path,
                                    message=(
                                        f"Step '{step_id}' references output of step '{ref_step}' "
                                        "but does not declare a dependency on it in 'depends_on'."
                                    ),
                                    line=find_line_for_key(content, step_id),
                                )
                            )
                elif isinstance(val, dict):
                    for k, v in val.items():
                        check_references(v, step_id)
                elif isinstance(val, list):
                    for item in val:
                        check_references(item, step_id)

            for step in steps:
                sid = step["id"]
                params = step.get("params") or {}
                check_references(params, sid)

    def check_decoupling(self) -> None:
        """Enforce decoupling of Brain (knowledge base / skills) and Hands (runtime tools)."""
        # 1. Check knowledge_base
        kb_dir = self.agent_dir / "knowledge_base"
        if kb_dir.is_dir():
            for file_path in kb_dir.rglob("*"):
                if file_path.is_dir():
                    continue
                if file_path.name in (".gitkeep", "__init__.md"):
                    continue
                # Allowed extensions
                if file_path.suffix.lower() not in (".md", ".json", ".yaml", ".yml", ".txt", ".jsonl"):
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Decoupling violation: Non-declarative/executable file '{file_path.name}' found in knowledge base.",
                        )
                    )
                    continue

                if file_path.suffix.lower() == ".md":
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        self._check_markdown_code_blocks(file_path, content, is_knowledge_base=True)
                    except Exception as e:
                        self.issues.append(
                            LintIssue(
                                severity="error",
                                file_path=file_path,
                                message=f"Failed to read file: {e}",
                            )
                        )

        # 2. Check skills
        skills_dir = self.agent_dir / "skills"
        if skills_dir.is_dir():
            for file_path in skills_dir.glob("*"):
                if file_path.is_dir():
                    continue
                if file_path.name in ("_template.md", "__init__.md", ".gitkeep"):
                    continue
                # Skills must only contain .md files
                if file_path.suffix.lower() != ".md":
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Decoupling violation: Non-markdown file '{file_path.name}' found in skills directory.",
                        )
                    )
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")
                    self._check_markdown_code_blocks(file_path, content, is_knowledge_base=False)
                except Exception as e:
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Failed to read file: {e}",
                        )
                    )

        # 3. Check runtime tools
        tools_dir = self.project_root / "agent_runtime" / "tools"
        if tools_dir.is_dir():
            for file_path in tools_dir.glob("*"):
                if file_path.is_dir():
                    continue
                if file_path.name in ("__init__.py", ".gitkeep", "README.md"):
                    continue
                # Tools must only contain .py files
                if file_path.suffix.lower() != ".py":
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Decoupling violation: Non-python file '{file_path.name}' found in runtime tools directory.",
                        )
                    )
                    continue

                self._check_python_tool_decoupling(file_path)

    def _check_markdown_code_blocks(self, file_path: Path, content: str, is_knowledge_base: bool) -> None:
        pattern = r"```([a-zA-Z0-9_-]*)\n(.*?)\n```"
        loc_desc = "Knowledge base entry" if is_knowledge_base else "Skill contract"
        for match in re.finditer(pattern, content, re.DOTALL):
            lang = match.group(1).lower()
            code = match.group(2)
            if lang in ("python", "py", "javascript", "js", "typescript", "ts", "go", "bash", "sh"):
                # Ignore short illustrative snippet examples (<= 45 lines of code)
                lines = code.splitlines()
                if len(lines) <= 45:
                    continue

                has_impl = False
                reasons = []
                if "import " in code or "from " in code:
                    has_impl = True
                    reasons.append("imports")
                if "def " in code or "class " in code:
                    has_impl = True
                    reasons.append("python definitions (def/class)")
                if "function " in code or "const " in code or "let " in code:
                    has_impl = True
                    reasons.append("js/ts constructs (function/const/let)")

                if has_impl:
                    line_no = content[:match.start()].count("\n") + 1
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message=f"Decoupling violation: {loc_desc} contains a full/large implementation code block (>45 lines with {', '.join(reasons)}).",
                            line=line_no,
                        )
                    )

    def _extract_names(self, target: ast.AST) -> list[str]:
        if isinstance(target, ast.Name):
            return [target.id]
        elif isinstance(target, (ast.Tuple, ast.List)):
            names = []
            for elt in target.elts:
                names.extend(self._extract_names(elt))
            return names
        return []

    def _check_python_tool_decoupling(self, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            self.issues.append(
                LintIssue(
                    severity="error",
                    file_path=file_path,
                    message=f"Failed to parse python file: {e}",
                )
            )
            return

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    names = self._extract_names(target)
                    for name in names:
                        if not name.isupper() and name not in ("__all__", "__doc__", "__file__", "__name__", "__package__", "__path__"):
                            # Check if value is a mutable literal or calling list/dict/set
                            is_mutable = False
                            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                                is_mutable = True
                            elif isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Name) and node.value.func.id in ("list", "dict", "set"):
                                    is_mutable = True
                            
                            if is_mutable:
                                self.issues.append(
                                    LintIssue(
                                        severity="error",
                                        file_path=file_path,
                                        message=f"Decoupling violation: Tool contains mutable module-level state '{name}'.",
                                        line=node.lineno,
                                    )
                                )

                        # Check for potential hardcoded secrets
                        name_lower = name.lower()
                        if any(kw in name_lower for kw in ("key", "secret", "token", "password", "credential")):
                            val = None
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                val = node.value.value
                            elif hasattr(ast, "Str") and isinstance(node.value, ast.Str):
                                val = node.value.s
                                
                            if val and val.strip():
                                val = val.strip()
                                placeholders = ["placeholder", "your-", "env", "key_here", "dummy", "test", "<", ">"]
                                if not any(p in val.lower() for p in placeholders):
                                    self.issues.append(
                                        LintIssue(
                                            severity="warning",
                                            file_path=file_path,
                                            message=f"Potential hardcoded credential or secret in '{name}': '{val[:8]}...'",
                                            line=node.lineno,
                                        )
                                    )

            # Check for global statements
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Global):
                    self.issues.append(
                        LintIssue(
                            severity="error",
                            file_path=file_path,
                            message="Decoupling violation: Tool contains stateful 'global' statement.",
                            line=subnode.lineno,
                        )
                    )

    def apply_fixes(self) -> int:
        """Apply fixes for all fixable issues. Returns the count of issues fixed."""
        fixed_count = 0
        
        # We run the checks to get the list of issues, then apply fixes
        self.run_all_checks()
        
        # Filter fixable issues
        fixable_issues = [issue for issue in self.issues if issue.fixable]
        if not fixable_issues:
            return 0

        # We keep track of file edits to do them safely
        for issue in fixable_issues:
            if issue.fix_type == "create_skill_file":
                skill_name = issue.fix_metadata["skill_name"]
                skill_file = self.agent_dir / "skills" / f"{skill_name}.md"
                if not skill_file.exists():
                    skill_content = f"""---
id: "{skill_name}"
name: "{skill_name}"
description: "A placeholder description for {skill_name}."
version: "1.0.0"
inputs:
  query:
    type: "string"
    description: "Search query or parameters."
    required: true
outputs:
  result:
    type: "string"
    description: "The execution result."
safety_notes: ["Safe to execute under interactive-approval."]
---

# {skill_name} Skill Contract

Define execution instructions for the agent here.
"""
                    skill_file.write_text(skill_content, encoding="utf-8")
                    print(f"Fixed: Created skill contract at {skill_file}")
                    fixed_count += 1

            elif issue.fix_type == "add_tool_to_manifest":
                skill_name = issue.fix_metadata["skill_name"]
                if self.config_path.exists():
                    content = self.config_path.read_text(encoding="utf-8")
                    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                    if match:
                        front_matter_str = match.group(1)
                        data = yaml.safe_load(front_matter_str) or {}
                        tools = data.get("tools") or []
                        if skill_name not in tools:
                            tools.append(skill_name)
                        data["tools"] = tools
                        new_front_matter = yaml.safe_dump(data, sort_keys=False)
                        new_content = f"---\n{new_front_matter}---\n" + content[match.end() :]
                        self.config_path.write_text(new_content, encoding="utf-8")
                        print(f"Fixed: Registered skill '{skill_name}' in {self.config_path}")
                        fixed_count += 1

            elif issue.fix_type == "fix_version_format":
                filepath = Path(issue.fix_metadata["file_path"])
                key = issue.fix_metadata["key"]
                old_val = issue.fix_metadata["old_val"]
                if filepath.exists():
                    content = filepath.read_text(encoding="utf-8")
                    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                    if match:
                        front_matter_str = match.group(1)
                        data = yaml.safe_load(front_matter_str) or {}
                        if data.get(key) == old_val:
                            new_val = clean_version(str(old_val))
                            data[key] = new_val
                            new_front_matter = yaml.safe_dump(data, sort_keys=False)
                            new_content = f"---\n{new_front_matter}---\n" + content[match.end() :]
                            filepath.write_text(new_content, encoding="utf-8")
                            print(f"Fixed: Normalized '{key}' version to '{new_val}' in {filepath}")
                            fixed_count += 1

        return fixed_count
