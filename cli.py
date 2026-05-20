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
    return parser


def scaffold_workspace(base_dir: Path) -> None:
    """Create a new .agent/ workspace with standard templates."""
    agent_dir = base_dir / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "skills").mkdir(exist_ok=True)
    (agent_dir / "prompts").mkdir(exist_ok=True)
    (agent_dir / "workflows").mkdir(exist_ok=True)
    (agent_dir / "memory").mkdir(exist_ok=True)
    
    agent_md = agent_dir / "agent.md"
    if not agent_md.exists():
        agent_md.write_text(
            "---\n"
            "protocol_version: \"1.0.0\"\n"
            "min_runtime_version: \"0.1.0\"\n"
            "name: new-agent\n"
            "version: 0.1.0\n"
            "purpose: Define the core purpose of this agent here.\n"
            "language: en-US\n"
            "authorization_level: interactive-approval\n"
            "use_case_tags: [default-agent]\n"
            "tools: []\n"
            "---\n\n"
            "# Agent Manifest\n"
        )
        print(f"Created {agent_md}")
    
    skill_template = agent_dir / "skills" / "_template.md"
    if not skill_template.exists():
        skill_template.write_text(
            "---\nname: \"{{skill_name}}\"\ndescription: \"\"\n---\n\n"
            "# {{skill_name}}\n\n"
            "## 1. Purpose\n\n## 2. Required Inputs\n\n## 3. Expected Outputs\n\n"
            "## 4. Execution Boundaries & Safety\n\n## 5. Fallback Mechanism\n"
        )
        print(f"Created {skill_template}")
        
    persona_template = agent_dir / "persona_template.md"
    if not persona_template.exists():
        persona_template.write_text(
            "# PAP Persona Definition Template\n\n"
            "## 1. Core Identity & Tone\n\n## 2. Prime Directives\n\n"
            "## 3. Avoidance Rules\n\n## 4. Default Workflow\n"
        )
        print(f"Created {persona_template}")
    
    print("PAP workspace scaffolded successfully!")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command and args.command[0] == "init":
        scaffold_workspace(Path.cwd())
        return 0

    config_path = Path(args.config)

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

    # 2. Handle skill listing
    if args.list_skills:
        from agent_runtime.engine import AgentEngine
        if not config_path.exists():
            print(f"Error: config file not found: {config_path}", file=sys.stderr)
            return 1
        engine = AgentEngine(config_path=config_path)
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
        engine = AgentEngine(config_path=config_path)
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
        engine = AgentEngine(config_path=config_path)
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
        engine = AgentEngine(config_path=config_path)
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
        engine = AgentEngine(config_path=config_path)
        try:
            params: dict = json.loads(args.params)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON for --params: {exc}", file=sys.stderr)
            return 1
        print(f"Executing workflow '{args.run_workflow}'...")
        try:
            result = engine.execute_workflow(args.run_workflow, params)
            print(json.dumps(result, indent=2))
            return 0
        except Exception as exc:
            print(f"Workflow execution failed: {exc}", file=sys.stderr)
            return 1

    # 7. Handle MCP synchronization
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

    # 8. Handle PAP Hub packaging and cloning
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

    # 9. Handle default execution logic
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

        engine = AgentEngine(config_path=config_path)
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
        engine = AgentEngine(config_path=config_path)
        config = engine.config
        print(
            f"Portable Agent '{config.get('name')}' v{config.get('version')} ready.\n"
            f"Registered tools: {', '.join(engine.router.available_tools)}\n"
            f"Use --tool <name> --params '{{...}}' to invoke a tool."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
