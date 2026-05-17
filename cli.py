"""CLI entrypoint for the Portable Agent.

Usage
-----
    python cli.py                        # uses default .agent/agent.md
    python cli.py --config path/to/agent.md
    python cli.py --tool search_web --params '{"query": "hello world"}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_runtime.engine import AgentEngine, load_agent_config
from agent_runtime.logger import get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portable-agent",
        description="Portable Agent Protocol reference CLI",
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    if args.show_config:
        config = load_agent_config(config_path)
        print(json.dumps(config, indent=2))
        return 0

    engine = AgentEngine(config_path=config_path)

    if args.tool:
        try:
            params: dict = json.loads(args.params)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON for --params: {exc}", file=sys.stderr)
            return 1

        try:
            result = engine.run(args.tool, params)
            print(json.dumps(result, indent=2))
        except KeyError as exc:
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
