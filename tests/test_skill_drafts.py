"""Tests for skill contract auto-draft generation and interception logic."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any
import pytest
import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None

from agent_runtime.engine import AgentEngine, UnregisteredSkillError
from agent_runtime.router import Router


def _write_agent_md(tmp_path: Path, tools: list[str]) -> Path:
    tool_lines = "\n".join(f"  - {t}" for t in tools)
    content = textwrap.dedent(f"""\
        ---
        name: test-agent
        version: "0.1.0"
        tools:
        {tool_lines}
        protocol:
          directories:
            skills: ".agent/skills"
        ---
        # test
    """)
    p = tmp_path / "agent.md"
    p.write_text(content, encoding="utf-8")
    return p


class TestSkillDrafts:
    def test_interception_and_draft_generation(self, tmp_path: Path) -> None:
        """Verify that calling an unregistered skill intercepts the call, generates a draft, and raises UnregisteredSkillError."""
        # Use an empty tools list to bypass validate_agent_config_paths checking for contract file on startup
        agent_md = _write_agent_md(tmp_path, [])
        
        # We set skills_dir inside tmp_path to avoid writing to the global repo
        skills_dir = tmp_path / ".agent" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Instantiating the engine with bypass_onboarding=True
        engine = AgentEngine(config_path=agent_md, bypass_onboarding=True)
        
        # We need a registered dummy handler for my_custom_tool in python registry so it can be called (though contract is missing)
        def dummy_handler(params: dict[str, Any]) -> dict[str, Any]:
            return {"results": "success"}
        
        engine.router.register_tool("my_custom_tool", dummy_handler)
        
        # Docstring mock to test parameter description extraction
        dummy_handler.__doc__ = """My custom tool description.
        
        Parameters
        ----------
        query : str — The search query term.
        limit : int — Max results.
        """
        
        # Call unregistered skill with parameters
        with pytest.raises(UnregisteredSkillError) as exc_info:
            engine.run("my_custom_tool", {"query": "hello", "limit": 10, "flag": True})
            
        assert "is not registered in the active registry" in str(exc_info.value)
        
        # Verify draft was generated
        draft_path = skills_dir / "drafts" / "my_custom_tool.md"
        assert draft_path.exists()
        
        # Load and parse draft front-matter
        content = draft_path.read_text(encoding="utf-8")
        assert "---" in content
        
        parts = content.split("---")
        front_matter = yaml.safe_load(parts[1])
        
        assert front_matter["id"] == "my_custom_tool"
        assert front_matter["name"] == "my_custom_tool"
        assert front_matter["status"] == "draft"
        assert front_matter["author"] == "pap-auto-generator"
        
        # Verify input parameter types were correctly inferred
        inputs = front_matter["inputs"]
        assert inputs["query"]["type"] == "string"
        assert inputs["query"]["description"] == "The search query term."
        assert inputs["limit"]["type"] == "integer"
        assert inputs["limit"]["description"] == "Max results."
        assert inputs["flag"]["type"] == "boolean"
        
        # Validate against JSON schema if jsonschema is installed
        if jsonschema is not None:
            schema_path = Path("spec/skill-contract.schema.json")
            if schema_path.exists():
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                jsonschema.validate(instance=front_matter, schema=schema)

    def test_authorization_gates_block_drafts(self, tmp_path: Path) -> None:
        """Verify that draft contracts are not officially loaded and cannot be executed."""
        # Here we declare 'my_tool' in tools list because the contract file exists on startup
        agent_md = _write_agent_md(tmp_path, ["my_tool"])
        skills_dir = tmp_path / ".agent" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a draft contract directly under .agent/skills/ with status: draft
        (skills_dir / "my_tool.md").write_text(textwrap.dedent("""\
            ---
            id: my_tool
            name: my_tool
            description: Test draft tool
            version: 1.0.0
            status: draft
            inputs:
              param:
                type: string
                description: Inferred param
                required: true
            outputs:
              result:
                type: object
                description: Result description
            safety_notes:
              - Some constraint
            ---
            # Skill: my_tool
        """), encoding="utf-8")
        
        engine = AgentEngine(config_path=agent_md, bypass_onboarding=True)
        def dummy_handler(params: dict[str, Any]) -> dict[str, Any]:
            return {"result": "success"}
        engine.router.register_tool("my_tool", dummy_handler)
        
        # Verify it returns None when describing since it is blocked
        assert engine.router.describe_skill("my_tool") is None
        
        # Calling it should raise UnregisteredSkillError (and generate/regenerate draft in drafts/)
        with pytest.raises(UnregisteredSkillError):
            engine.run("my_tool", {"param": "val"})
            
        assert (skills_dir / "drafts" / "my_tool.md").exists()

    def test_promotion_flow_allows_execution(self, tmp_path: Path) -> None:
        """Verify that promoting a draft (moving it and updating status to stable) allows successful execution."""
        # Initial run: approved_tool contract does not exist yet, so declare empty tools list
        agent_md = _write_agent_md(tmp_path, [])
        skills_dir = tmp_path / ".agent" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        engine = AgentEngine(config_path=agent_md, bypass_onboarding=True)
        def dummy_handler(params: dict[str, Any]) -> dict[str, Any]:
            return {"result": "success"}
        engine.router.register_tool("approved_tool", dummy_handler)
        
        # 1. Calling raises UnregisteredSkillError and creates draft
        with pytest.raises(UnregisteredSkillError):
            engine.run("approved_tool", {"arg": 42})
            
        draft_path = skills_dir / "drafts" / "approved_tool.md"
        assert draft_path.exists()
        
        # 2. Promote the draft: move to active skills_dir and remove/update status: draft
        stable_path = skills_dir / "approved_tool.md"
        draft_content = draft_path.read_text(encoding="utf-8")
        stable_content = draft_content.replace("status: draft", "status: stable")
        stable_path.write_text(stable_content, encoding="utf-8")
        
        # Remove the draft file to ensure the runtime is loading from the stable path
        draft_path.unlink()
        
        # Re-initialize engine with approved_tool now that the stable contract exists
        agent_md_approved = _write_agent_md(tmp_path, ["approved_tool"])
        engine = AgentEngine(config_path=agent_md_approved, bypass_onboarding=True)
        engine.router.register_tool("approved_tool", dummy_handler)
        
        # Describe skill should now succeed
        contract = engine.router.describe_skill("approved_tool")
        assert contract is not None
        assert contract["status"] == "stable"
        
        # Execution should succeed without UnregisteredSkillError
        res = engine.run("approved_tool", {"arg": 42})
        assert res == {"result": "success"}
