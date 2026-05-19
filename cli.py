"""CLI entrypoint for the Portable Agent.

Usage
-----
    python cli.py init                   # scaffold a new .agent/ workspace
    python cli.py validate               # validate the .agent/ workspace
    python cli.py mcp sync               # sync MCP server tools to .agent/skills/
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
        help="JSON-encoded parameters for the tool (default: {})",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the parsed agent config and exit",
    )
    parser.add_argument(
        "--export-skills",
        action="store_true",
        help="Export PAP .agent/skills/*.md contracts as Anthropic SKILL.md folders",
    )
    parser.add_argument(
        "--output",
        default="./anthropic_skills/",
        metavar="PATH",
        help="Output directory for generated Anthropic skills",
    )
    parser.add_argument(
        "--sync-anthropic-skills",
        action="store_true",
        help="Sync Anthropic SKILL.md records into .agent/skills.md",
    )
    parser.add_argument(
        "--source",
        metavar="PATH_OR_GITHUB",
        help="Source for --sync-anthropic-skills, e.g. ./skills or github:anthropics/skills",
    )
    parser.add_argument(
        "--via-claude-api",
        action="store_true",
        help="Dispatch --tool through Claude API using an Anthropic-compatible skill",
    )
    parser.add_argument(
        "--anthropic-skill-id",
        metavar="ID",
        help="Uploaded custom skill id or Anthropic built-in skill id for --via-claude-api",
    )
    parser.add_argument(
        "--anthropic-skill-type",
        choices=["anthropic", "custom"],
        help="Skill source for --anthropic-skill-id",
    )
    parser.add_argument(
        "--anthropic-skill-version",
        metavar="VERSION",
        help="Skill version for --via-claude-api, defaulting to latest",
    )
    parser.add_argument(
        "--validate-compatibility",
        action="store_true",
        help="Validate PAP skills for Anthropic SKILL.md compatibility",
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

    if args.export_skills:
        from agent_runtime.bridges.anthropic_skill_bridge import export_all_skills

        config_path = Path(args.config)
        agent_dir = config_path.parent if config_path.parent.name == ".agent" else Path.cwd() / ".agent"
        try:
            exported = export_all_skills(agent_dir, Path(args.output))
        except Exception as exc:
            print(f"Export failed: {exc}", file=sys.stderr)
            return 1
        for path in exported:
            print(path)
        print(f"Exported {len(exported)} Anthropic-compatible skill(s).")
        return 0

    if args.sync_anthropic_skills:
        from agent_runtime.loaders.anthropic_skills_loader import (
            load_from_github,
            load_from_local,
            sync_to_registry,
        )

        source = args.source or "github:anthropics/skills"
        config_path = Path(args.config)
        agent_dir = config_path.parent if config_path.parent.name == ".agent" else Path.cwd() / ".agent"
        try:
            if source.startswith("github:"):
                repo_ref = source.removeprefix("github:")
                repo, _, ref = repo_ref.partition("@")
                records = load_from_github(repo or "anthropics/skills", ref or "main")
            else:
                records = load_from_local(Path(source))
            sync_to_registry(records, agent_dir)
        except Exception as exc:
            print(f"Sync failed: {exc}", file=sys.stderr)
            return 1
        print(f"Synchronized {len(records)} Anthropic skill(s) into {agent_dir / 'skills.md'}.")
        return 0

    if args.validate_compatibility:
        from agent_runtime.bridges.anthropic_skill_bridge import validate_compatibility

        config_path = Path(args.config)
        agent_dir = config_path.parent if config_path.parent.name == ".agent" else Path.cwd() / ".agent"
        try:
            reports = validate_compatibility(agent_dir)
        except Exception as exc:
            print(f"Compatibility validation failed: {exc}", file=sys.stderr)
            return 1

        error_count = 0
        for report in reports:
            status = "ok" if report["anthropic_compatible"] else "error"
            print(f"{status}: {report['name']} -> {report['anthropic_skill_path']}")
            for error in report["errors"]:
                error_count += 1
                print(f"  - {error}")
        print(f"Compatibility report: {len(reports)} skill(s), {error_count} error(s).")
        return 0 if error_count == 0 else 1
        
    if args.command and args.command[0] == "validate":
        from agent_runtime.engine import validate_agent_workspace
        config_path = Path(args.config)
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
    if args.command and args.command[0] == "mcp" and len(args.command) > 1 and args.command[1] == "sync":
        config_path = Path(args.config)
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
                    # Exclude memory and secrets
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

    config_path = Path(args.config)
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

        if args.anthropic_skill_id:
            params["anthropic_skill_id"] = args.anthropic_skill_id
        if args.anthropic_skill_type:
            params["anthropic_skill_type"] = args.anthropic_skill_type
        if args.anthropic_skill_version:
            params["anthropic_skill_version"] = args.anthropic_skill_version

    engine = AgentEngine(config_path=config_path)

    if args.tool:
        try:
            if args.via_claude_api:
                agent_dir = config_path.parent if config_path.parent.name == ".agent" else Path.cwd() / ".agent"
                pap_skill = agent_dir / "skills" / f"{args.tool}.md"
                project_root = agent_dir.parent if agent_dir.name == ".agent" else Path.cwd()
                anthropic_skill = project_root / "anthropic_skills" / args.tool.replace("_", "-") / "SKILL.md"
                skill_path = pap_skill if pap_skill.exists() else anthropic_skill
                result = engine.router.dispatch_via_claude_api(args.tool, params, skill_path)
            else:
                result = engine.run(args.tool, params)
            print(json.dumps(result, indent=2))
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        config = engine.config
        print(
            f"Portable Agent '{config.get('name')}' v{config.get('version')} ready.\n"
            f"Registered tools: {', '.join(engine.router.available_tools)}\n"
            f"Use --tool <name> --params '{{...}}' to invoke a tool."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
