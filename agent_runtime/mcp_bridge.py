"""Bridge between Portable Agent Protocol and Model Context Protocol."""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .logger import get_logger

logger = get_logger(__name__)


async def _fetch_tools_from_server(server_name: str, config: dict[str, Any]) -> list[Any]:
    """Connect to an MCP server and fetch its tools."""
    command = config.get("command")
    if not command:
        logger.error("MCP server '%s' is missing 'command'", server_name)
        return []

    args = config.get("args", [])
    env = os.environ.copy()
    server_env = config.get("env", {})
    if server_env:
        for k, v in server_env.items():
            env[k] = str(v)

    logger.info("Connecting to MCP server '%s' (%s %s)", server_name, command, " ".join(args))
    server_params = StdioServerParameters(command=command, args=args, env=env)

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools
    except Exception as exc:
        logger.error("Failed to connect or fetch tools from MCP server '%s': %s", server_name, exc)
        return []


def _generate_skill_markdown(tool: Any, server_name: str, template_content: str) -> str:
    """Generate the markdown content for a single tool based on the template."""
    content = template_content

    # Prepare replacements
    skill_name = f"mcp_{server_name}_{tool.name}"
    description = tool.description or f"Tool {tool.name} from MCP server {server_name}"
    
    # Format inputs
    inputs_md = ""
    input_schema = tool.inputSchema or {}
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])
    
    if properties:
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "any")
            req_str = "**Required**" if prop_name in required else "Optional"
            prop_desc = prop_info.get("description", "")
            inputs_md += f"- `{prop_name}` ({prop_type}, {req_str}): {prop_desc}\n"
    else:
        inputs_md = "- No inputs required."

    # Replace placeholders
    content = content.replace("{{skill_name}}", skill_name)
    content = content.replace("{{short_description_under_50_chars}}", description[:50].replace("\n", " "))
    content = content.replace("{{author_or_ai_generator}}", f"pap-mcp-bridge ({server_name})")
    content = content.replace("{{purpose_description}}", description)
    
    # We replace the entire section for inputs using regex or simple replace
    # A simpler approach is to replace the example inputs with our generated inputs.
    # Since the template has specific placeholders, let's just do a rough substitution 
    # or recreate the inputs section if we can't find placeholders.
    
    # Let's just do a naive replacement if the placeholders exist
    content = content.replace("- `{{param_1_name}}` ({{type}}, **Required**): {{param_1_description}}\n- `{{param_2_name}}` ({{type}}, Optional): {{param_2_description}}", inputs_md)
    
    # Provide sensible defaults for others
    content = content.replace("{{success_format_description}}", "JSON response from MCP server")
    content = content.replace("{{error_format_description}}", "Error message string")
    content = content.replace("{{constraint_1}}", f"Must be executed via MCP bridge to `{server_name}`")
    content = content.replace("{{constraint_2}}", "Do not mock or hallucinate responses")
    content = content.replace("{{error_condition_1}}", "connection fails")
    content = content.replace("{{fallback_action_1}}", "Notify user that MCP server is unreachable")
    
    return content


async def sync_mcp_servers_async(agent_config: dict[str, Any], root_path: Path) -> None:
    """Async implementation of MCP sync."""
    mcp_servers = agent_config.get("mcp_servers", {})
    if not mcp_servers:
        logger.info("No mcp_servers defined in agent manifest.")
        return

    skills_dir = root_path / agent_config.get("protocol", {}).get("directories", {}).get("skills", ".agent/skills/")
    template_path = skills_dir / "_template.md"
    
    if not template_path.exists():
        logger.warning("Skill template %s not found. Cannot generate markdown contracts.", template_path)
        return
        
    template_content = template_path.read_text(encoding="utf-8")

    for server_name, server_config in mcp_servers.items():
        tools = await _fetch_tools_from_server(server_name, server_config)
        if not tools:
            continue
            
        logger.info("Found %d tools from MCP server '%s'", len(tools), server_name)
        for tool in tools:
            md_content = _generate_skill_markdown(tool, server_name, template_content)
            skill_name = f"mcp_{server_name}_{tool.name}"
            out_path = skills_dir / f"{skill_name}.md"
            out_path.write_text(md_content, encoding="utf-8")
            logger.info("Generated skill contract: %s", out_path)


def sync_mcp_servers(agent_config: dict[str, Any], root_path: Path) -> None:
    """Synchronize MCP server tools to PAP skill contracts."""
    asyncio.run(sync_mcp_servers_async(agent_config, root_path))


# Execution Bridge

async def execute_mcp_tool_async(server_config: dict[str, Any], tool_name: str, params: dict[str, Any]) -> Any:
    """Execute a specific tool on an MCP server."""
    command = server_config.get("command")
    args = server_config.get("args", [])
    env = os.environ.copy()
    if "env" in server_config:
        for k, v in server_config["env"].items():
            env[k] = str(v)

    server_params = StdioServerParameters(command=command, args=args, env=env)
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=params)
                
                # result is a CallToolResult which has 'content' list
                # We'll serialize it to dict for PAP runtime
                if hasattr(result, "content") and result.content:
                    return {"content": [c.model_dump() for c in result.content], "isError": result.isError}
                return {"result": str(result)}
    except Exception as exc:
        logger.error("Failed to execute MCP tool %s: %s", tool_name, exc)
        return {"error": str(exc), "isError": True}


def execute_mcp_tool(server_config: dict[str, Any], tool_name: str, params: dict[str, Any]) -> Any:
    """Synchronous wrapper for MCP tool execution."""
    return asyncio.run(execute_mcp_tool_async(server_config, tool_name, params))
