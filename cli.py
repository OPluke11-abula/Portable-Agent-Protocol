"""CLI entrypoint for the Portable Agent.

Usage
-----
    python cli.py init                   # scaffold a new .agent/ workspace
    python cli.py validate               # validate the .agent/ workspace
    python cli.py mcp sync               # sync MCP server tools to .agent/skills/
    python cli.py --list-skills          # list all active skill contracts
    python cli.py --describe-skill <id>  # describe detailed contract of a skill
    python cli.py --memory-read <key>    # read value from persistent memory
    python cli.py --memory-write <k> <v> # write key-value to persistent memory
    python cli.py --run-workflow <id>    # execute a multi-step workflow
    python cli.py --resume-workflow <sid> # resume workflow from checkpoint file
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_runtime.logger import get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portable-agent",
        description="Portable Agent Protocol reference CLI",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Command to run (e.g. 'init', 'validate', or 'mcp sync')",
    )
    parser.add_argument(
        "--config",
        default=".agent/agent.md",
        metavar="PATH",
        help="Path to agent.md config file (default: .agent/agent.md)",
    )
    parser.add_argument(
        "--tool",
        metavar="TOOL",
        help="Tool to invoke (e.g. search_web, query_db, code_executor)",
    )
    parser.add_argument(
        "--params",
        metavar="JSON",
        default="{}",
        help="JSON-encoded parameters for the tool or workflow (default: {})",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the parsed agent config and exit",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List all active skill contracts and exit",
    )
    parser.add_argument(
        "--describe-skill",
        metavar="SKILL_ID",
        help="Print detailed contract of a single skill and exit",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the agent workspace and exit",
    )
    parser.add_argument(
        "--memory-read",
        metavar="KEY",
        help="Read value from persistent memory by key and exit",
    )
    parser.add_argument(
        "--memory-write",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Write key-value to persistent memory and exit",
    )
    parser.add_argument(
        "--run-workflow",
        metavar="WORKFLOW_ID",
        help="Execute a multi-step workflow by ID and exit",
    )
    parser.add_argument(
        "--resume-session",
        metavar="SESSION_ID",
        help="Session ID to resume workflow from a checkpoint",
    )
    parser.add_argument(
        "--resume-step",
        metavar="STEP_ID",
        help="Specific step ID to resume workflow from (optional, defaults to first failure/pending step)",
    )
    parser.add_argument(
        "--resume-workflow",
        metavar="SESSION_ID",
        help="Resume a workflow from a runs/<session_id>.json checkpoint file (standalone, does not require --run-workflow)",
    )
    parser.add_argument(
        "--self-audit",
        action="store_true",
        help="Run the agent self-audit diagnostic",
    )
    parser.add_argument(
        "--query-knowledge",
        metavar="KEYWORD",
        help="Search knowledge base entries by keyword and exit",
    )
    parser.add_argument(
        "--get-knowledge",
        metavar="ENTRY_ID",
        help="Retrieve a single knowledge base entry by ID and exit",
    )
    parser.add_argument(
        "--export-handoff",
        metavar="JSON",
        help="Export handoff state. Argument is a JSON string containing: task_state, pending_steps, context_summary, optionally memory_keys and handoff_id",
    )
    parser.add_argument(
        "--import-handoff",
        metavar="HANDOFF_ID",
        help="Import state from a handoff packet file and exit",
    )
    parser.add_argument(
        "--project-name",
        help="Project name for workspace initialization",
    )
    parser.add_argument(
        "--agent-name",
        help="Agent name for workspace initialization",
    )
    parser.add_argument(
        "--skills",
        help="Comma-separated list of initial skills to enable",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only simulate workspace creation, do not write files",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix fixable lint issues",
    )
    parser.add_argument(
        "--bypass-onboarding",
        action="store_true",
        help="Bypass strict onboarding guards for trusted host bootstrapping",
    )
    return parser



def scaffold_workspace(
    base_dir: Path,
    project_name: str | None = None,
    agent_name: str | None = None,
    skills_list: list[str] | None = None,
    dry_run: bool = False,
) -> None:
    """Create a new .agent/ workspace with standard templates."""
    import sys

    # Prompt if interactive and values not provided
    if not project_name:
        if sys.stdin.isatty():
            try:
                project_name = input("Enter project name [my-project]: ").strip() or "my-project"
            except (IOError, EOFError):
                project_name = "my-project"
        else:
            project_name = "my-project"

    if not agent_name:
        if sys.stdin.isatty():
            try:
                agent_name = input("Enter agent name [my-agent]: ").strip() or "my-agent"
            except (IOError, EOFError):
                agent_name = "my-agent"
        else:
            agent_name = "my-agent"

    if skills_list is None:
        if sys.stdin.isatty():
            try:
                skills_input = input("Enter comma-separated skills to enable (e.g. search_web, query_db) []: ").strip()
                skills_list = [s.strip() for s in skills_input.split(",") if s.strip()]
            except (IOError, EOFError):
                skills_list = []
        else:
            skills_list = []

    agent_dir = base_dir / ".agent"

    def _make_dir(d: Path) -> None:
        if dry_run:
            print(f"[Dry Run] Would create directory: {d}")
        else:
            d.mkdir(parents=True, exist_ok=True)
            print(f"Created directory {d}")

    def _write_file(f: Path, content: str) -> None:
        if dry_run:
            print(f"[Dry Run] Would create file: {f}")
        else:
            if not f.exists():
                f.write_text(content, encoding="utf-8")
                print(f"Created {f}")
            else:
                print(f"File already exists (skipped): {f}")

    _make_dir(agent_dir)
    _make_dir(agent_dir / "skills")
    _make_dir(agent_dir / "prompts")
    _make_dir(agent_dir / "workflows")
    _make_dir(agent_dir / "memory")
    _make_dir(agent_dir / "knowledge_base")

    # 1. agent.md
    agent_tools_yaml = ""
    if skills_list:
        agent_tools_yaml = "\ntools:\n" + "\n".join(f"  - {s}" for s in skills_list)
    else:
        agent_tools_yaml = "\ntools: []"

    agent_md_content = f"""---
protocol_version: "1.0.0"
min_runtime_version: "0.1.0"
name: "{agent_name}"
version: "0.1.0"
purpose: "Define the core purpose of this agent here."
language: "en-US"
authorization_level: "interactive-approval"
use_case_tags: ["default-agent"]{agent_tools_yaml}
protocol:
  root: ".agent/"
  manifest: ".agent/agent.md"
  directories:
    skills: ".agent/skills/"
    workflows: ".agent/workflows/"
memory:
  backend: "local"
  path: ".agent/memory/"
---

# Agent Manifest
"""
    _write_file(agent_dir / "agent.md", agent_md_content)

    # 2. skills.md
    skills_md_content = """---
schema_version: "1.0.0"
---

# Skills Entry Point

This file is the runtime-facing skill registry for the Portable Agent.
Enable tools by adding them to the tools list in `agent.md`.
"""
    _write_file(agent_dir / "skills.md", skills_md_content)

    # 3. prompts.md
    prompts_md_content = """---
schema_version: "1.0.0"
---

# Prompts Entry Point

This file is the runtime-facing prompt catalog for the Portable Agent.
"""
    _write_file(agent_dir / "prompts.md", prompts_md_content)

    # 4. memory.md
    memory_md_content = """---
schema_version: "1.0.0"
---

# Memory Contract

This file defines the runtime-facing memory schema used by the Portable Agent.
"""
    _write_file(agent_dir / "memory.md", memory_md_content)

    # 5. workflows.md
    workflows_md_content = """---
schema_version: "1.0.0"
---

# Workflow Registry

This file is the canonical runtime-facing workflow registry for the Portable Agent.
"""
    _write_file(agent_dir / "workflows.md", workflows_md_content)

    # 6. skill contracts for each declared skill
    for skill_name in skills_list:
        skill_file = agent_dir / "skills" / f"{skill_name}.md"
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
        _write_file(skill_file, skill_content)

    # 7. template files
    skill_template = agent_dir / "skills" / "_template.md"
    skill_template_content = """---
name: "{{skill_name}}"
description: ""
---

# {{skill_name}}

## 1. Purpose

## 2. Required Inputs

## 3. Expected Outputs

## 4. Execution Boundaries & Safety

## 5. Fallback Mechanism
"""
    _write_file(skill_template, skill_template_content)

    persona_template = agent_dir / "persona_template.md"
    persona_template_content = """# PAP Persona Definition Template

## 1. Core Identity & Tone

## 2. Prime Directives

## 3. Avoidance Rules

## 4. Default Workflow
"""
    _write_file(persona_template, persona_template_content)

    print("PAP workspace scaffolded successfully!")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command and args.command[0] == "init":
        skills_list = None
        if args.skills:
            skills_list = [s.strip() for s in args.skills.split(",") if s.strip()]
        scaffold_workspace(
            base_dir=Path.cwd(),
            project_name=args.project_name,
            agent_name=args.agent_name,
            skills_list=skills_list,
            dry_run=args.dry_run,
        )
        return 0

    config_path = Path(args.config)

    # Handle lint subcommand
    if args.command and args.command[0] == "lint":
        from agent_runtime.lint import WorkspaceLinter
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1

        linter = WorkspaceLinter(config_path)

        if args.fix:
            print("Applying automatic fixes...")
            fixed_count = linter.apply_fixes()
            print(f"Successfully applied {fixed_count} fixes.")
            # Re-run checks to verify and display remaining issues
            issues = linter.run_all_checks()
        else:
            issues = linter.run_all_checks()

        if not issues:
            print("No lint issues found. Your workspace is perfectly compliant!")
            return 0

        errors_count = 0
        warnings_count = 0
        info_count = 0

        print(f"Linting results for {config_path.parent}:")
        for issue in issues:
            sev = issue.severity.upper()
            line_info = f":{issue.line}" if issue.line is not None else ""
            try:
                rel_path = issue.file_path.relative_to(Path.cwd()) if issue.file_path.is_absolute() else issue.file_path
            except ValueError:
                rel_path = issue.file_path
            sugg = f" (Suggestion: {issue.suggestion})" if issue.suggestion else ""
            print(f"  [{sev}] {rel_path}{line_info} - {issue.message}{sugg}")
            if issue.severity == "error":
                errors_count += 1
            elif issue.severity == "warning":
                warnings_count += 1
            else:
                info_count += 1

        print(f"\nSummary: found {errors_count} error(s), {warnings_count} warning(s), {info_count} info(s).")
        return 1 if errors_count > 0 else 0

    # 1. Handle validation option or subcommand
    if args.validate or (args.command and args.command[0] == "validate"):
        from agent_runtime.engine import validate_agent_workspace
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        try:
            validate_agent_workspace(config_path)
            print(f"Success: {config_path} passes all schema and layout validations.")
            return 0
        except Exception as e:
            print(f"Validation failed: {e}", file=sys.stderr)
            return 1

    # 1.5 Handle self-audit
    if args.self_audit or (args.command and args.command[0] == "self-audit"):
        from agent_runtime.engine import AgentEngine
        from agent_runtime import AgentSelfAuditor
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        try:
            engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
            auditor = AgentSelfAuditor(engine)
            print("Running agent self-audit diagnostic...")
            report = auditor.run_audit()
            
            value = report["semantic"]["value"]
            summary = value["summary"]
            issues = value["issues"]
            recommendations = value["recommendations"]

            print("\n==========================================")
            print("        PAP SELF-AUDIT REPORT")
            print("==========================================")
            print(f" Timestamp      : {value['timestamp']}")
            print(f" Skills Checked : {summary['skills_checked']}")
            print(f" Skills Issues  : {summary['skills_issues']}")
            print(f" Memory Size    : {summary['memory_size_bytes']} bytes")
            print(f" Handoff Files  : {summary['handoff_count']}")
            print(f" Abandoned Runs : {summary['abandoned_workflows']}")
            print("------------------------------------------")
            
            if issues:
                print(f"\n[WARNING] Detected {len(issues)} Issue(s):")
                for idx, issue in enumerate(issues, 1):
                    print(f"  {idx}. [{issue['type'].upper()}] (ID: {issue['id']})")
                    print(f"     Details: {issue['details']}")
            else:
                print("\n[OK] No workspace health issues detected.")

            if recommendations:
                print(f"\n[REC] Actionable Recommendation(s):")
                for r, rec in enumerate(recommendations, 1):
                    print(f"  {r}. [{rec['priority']}] (Task: {rec['task_id']})")
                    print(f"     {rec['description']}")
            print("==========================================\n")
            
            return 0
        except Exception as e:
            print(f"Self-audit execution failed: {e}", file=sys.stderr)
            return 1

    # 2. Handle skill listing
    if args.list_skills:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        skills = engine.router.list_skills()
        if not skills:
            print("No active skill contracts found.")
        else:
            print(f"Active skill contracts in {engine.router._skills_dir}:")
            for s in skills:
                print(f"  - {s['id']} (v{s.get('version', '1.0.0')}): {s.get('description', '')}")
        return 0

    # 3. Handle skill description
    if args.describe_skill:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        contract = engine.router.describe_skill(args.describe_skill)
        if not contract:
            print(f"Skill '{args.describe_skill}' not found in skills directory.", file=sys.stderr)
            return 1
        print(json.dumps(contract, indent=2))
        return 0

    # 4. Handle memory read
    if args.memory_read:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        value = engine.memory.read(args.memory_read)
        if value is None:
            print(f"Key '{args.memory_read}' not found in persistent memory.")
            return 0
        print(json.dumps(value, indent=2))
        return 0

    # 5. Handle memory write
    if args.memory_write:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        key, value = args.memory_write
        try:
            parsed_val = json.loads(value)
        except json.JSONDecodeError:
            parsed_val = value
        engine.memory.write(key, parsed_val)
        print(f"Successfully wrote '{key}' to persistent memory.")
        return 0

    # 6. Handle workflow execution
    if args.run_workflow:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        try:
            params: dict = json.loads(args.params)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON for --params: {exc}", file=sys.stderr)
            return 1
        try:
            if args.resume_session:
                print(f"Resuming workflow '{args.run_workflow}' for session '{args.resume_session}'...")
                result = engine.resume_workflow(args.run_workflow, args.resume_session, args.resume_step)
            else:
                print(f"Executing workflow '{args.run_workflow}'...")
                result = engine.execute_workflow(args.run_workflow, params)
            print(json.dumps(result, indent=2))
            return 0
        except Exception as exc:
            print(f"Workflow execution failed: {exc}", file=sys.stderr)
            return 1

    # 6b. Handle standalone workflow resume from checkpoint file
    if args.resume_workflow:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        try:
            print(f"Resuming workflow from checkpoint '{args.resume_workflow}'...")
            result = engine.resume_workflow_from_file(
                session_id=args.resume_workflow,
                step_id=args.resume_step,
            )
            print(json.dumps(result, indent=2))
            return 0
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Workflow resume failed: {exc}", file=sys.stderr)
            return 1

    # 7. Handle knowledge base queries
    if args.query_knowledge:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        results = engine.knowledge_base.query(args.query_knowledge)
        if not results:
            print(f"No knowledge entries found matching '{args.query_knowledge}'.")
        else:
            print(f"Found {len(results)} matching knowledge entries:")
            for entry in results:
                print(f"  - [{entry.get('id', '?')}] {entry.get('title', 'Untitled')}")
                tags = entry.get('tags', [])
                if tags:
                    print(f"    Tags: {', '.join(tags)}")
        return 0

    # 8. Handle knowledge base get
    if args.get_knowledge:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        entry = engine.knowledge_base.get(args.get_knowledge)
        if entry is None:
            print(f"Knowledge entry '{args.get_knowledge}' not found.", file=sys.stderr)
            return 1
        print(json.dumps({k: v for k, v in entry.items()}, indent=2))
        return 0

    # 9. Handle MCP synchronization
    if args.command and args.command[0] == "mcp" and len(args.command) > 1 and args.command[1] == "sync":
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        from agent_runtime.engine import load_agent_config

        config = load_agent_config(config_path)
        
        from agent_runtime.mcp_bridge import sync_mcp_servers
        root_path = Path.cwd()
        if config_path.parent.name == ".agent":
            root_path = config_path.parent.parent
            
        print("Synchronizing MCP servers...")
        sync_mcp_servers(config, root_path)
        print("Done!")
        return 0

    # 10. Handle PAP Hub packaging and cloning
    if args.command and args.command[0] == "hub":
        if len(args.command) < 2:
            print("Error: 'hub' requires a subcommand ('pack' or 'clone').", file=sys.stderr)
            return 1
            
        subcmd = args.command[1]
        
        if subcmd == "pack":
            import tarfile
            agent_dir = Path(".agent")
            if not agent_dir.exists():
                print("Error: .agent/ directory not found.", file=sys.stderr)
                return 1
            out_file = ".agent-profile.tar.gz"
            print(f"Packing {agent_dir} to {out_file} (excluding 'memory' and secrets)...")
            with tarfile.open(out_file, "w:gz") as tar:
                for path in agent_dir.rglob("*"):
                    if "memory" in path.parts or path.suffix == ".env" or path.suffix == ".sqlite":
                        continue
                    tar.add(path, arcname=path.relative_to(agent_dir.parent))
            print(f"Successfully packed to {out_file}")
            return 0
            
        elif subcmd == "clone":
            if len(args.command) < 3:
                print("Error: 'hub clone' requires a repository name (e.g. username/repo).", file=sys.stderr)
                return 1
            repo_name = args.command[2]
            print(f"Cloning {repo_name} from PAP Hub...")
            import subprocess
            import shutil
            import tempfile
            git_url = f"https://github.com/{repo_name}.git"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    subprocess.run(["git", "clone", "--depth", "1", git_url, tmpdir], check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error cloning repository: {e.stderr.decode()}", file=sys.stderr)
                    return 1
                
                src_agent = Path(tmpdir) / ".agent"
                dest_agent = Path(".agent")
                if not src_agent.exists():
                    print("Error: Repository does not contain an .agent/ directory.", file=sys.stderr)
                    return 1
                    
                if dest_agent.exists():
                    print("Warning: Local .agent/ directory already exists. Overwriting...", file=sys.stderr)
                    shutil.rmtree(dest_agent)
                
                shutil.copytree(src_agent, dest_agent)
            
            print(f"Successfully cloned {repo_name} into .agent/")
            return 0

    # 11. Handle handoff export
    if args.export_handoff:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        try:
            payload = json.loads(args.export_handoff)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON for --export-handoff: {exc}", file=sys.stderr)
            return 1

        task_state = payload.get("task_state", "")
        pending_steps = payload.get("pending_steps", [])
        context_summary = payload.get("context_summary", "")
        memory_keys = payload.get("memory_keys")
        handoff_id = payload.get("handoff_id")

        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        try:
            hid = engine.export_handoff(
                task_state=task_state,
                pending_steps=pending_steps,
                context_summary=context_summary,
                memory_keys=memory_keys,
                handoff_id=handoff_id,
            )
            print(json.dumps({"success": True, "handoff_id": hid}))
            return 0
        except Exception as exc:
            print(f"Handoff export failed: {exc}", file=sys.stderr)
            return 1

    # 12. Handle handoff import
    if args.import_handoff:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        try:
            packet = engine.import_handoff(args.import_handoff)
            print(json.dumps({"success": True, "packet": packet}, indent=2))
            return 0
        except Exception as exc:
            print(f"Handoff import failed: {exc}", file=sys.stderr)
            return 1

    # 13. Handle default execution logic
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    if args.show_config:
        from agent_runtime.engine import load_agent_config

        config = load_agent_config(config_path)
        print(json.dumps(config, indent=2))
        return 0

    from agent_runtime.engine import AgentEngine

    if args.tool:
        try:
            params: dict = json.loads(args.params)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON for --params: {exc}", file=sys.stderr)
            return 1

        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        try:
            result = engine.run(args.tool, params)
            print(json.dumps(result, indent=2))
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        engine = AgentEngine(config_path=config_path, bypass_onboarding=args.bypass_onboarding)
        config = engine.config
        print(
            f"Portable Agent '{config.get('name')}' v{config.get('version')} ready.\n"
            f"Registered tools: {', '.join(engine.router.available_tools)}\n"
            f"Use --tool <name> --params '{{...}}' to invoke a tool."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
