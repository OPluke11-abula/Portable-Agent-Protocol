"""Tests for the enhanced Router validation and discovery APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agent_runtime.router import Router


class TestRouterValidation:
    def setup_method(self) -> None:
        # Use default skills directory: .agent/skills
        self.router = Router(
            tools=["search_web", "query_db", "code_executor"],
            skills_dir=Path(".agent/skills")
        )

    def test_list_skills(self) -> None:
        skills = self.router.list_skills()
        assert len(skills) > 0
        
        # Verify shape of returned contracts
        for skill in skills:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
            assert "version" in skill
            assert "inputs" in skill
            assert "outputs" in skill
            assert "safety_notes" in skill

        # Verify specific active skills are listed
        skill_ids = {s["id"] for s in skills}
        assert "search_web" in skill_ids
        assert "query_db" in skill_ids
        assert "code_executor" in skill_ids

    def test_describe_skill(self) -> None:
        contract = self.router.describe_skill("search_web")
        assert contract is not None
        assert contract["id"] == "search_web"
        assert contract["name"] == "search_web"
        assert "query" in contract["inputs"]

        # Missing skill returns None
        assert self.router.describe_skill("nonexistent_skill") is None

    def test_validate_call_success(self) -> None:
        # Correct parameter types and required fields
        params = {
            "query": "test query",
            "time_scope": "24h",
            "must_cite": True,
            "preferred_sources": ["wikipedia.org"]
        }
        # Should not raise any exception
        self.router.validate_call("search_web", params)

    def test_validate_call_missing_required(self) -> None:
        # 'query' is required for 'search_web'
        params = {
            "time_scope": "24h"
        }
        with pytest.raises(ValueError) as exc_info:
            self.router.validate_call("search_web", params)
        
        assert "missing required input field 'query'" in str(exc_info.value)
        assert "search_web" in str(exc_info.value)

    def test_validate_call_type_mismatch_string(self) -> None:
        # 'query' must be string, but passing integer
        params = {
            "query": 12345
        }
        with pytest.raises(ValueError) as exc_info:
            self.router.validate_call("search_web", params)
        
        assert "parameter 'query' has invalid type" in str(exc_info.value)
        assert "Expected 'string', got 'int'" in str(exc_info.value)
        assert "search_web" in str(exc_info.value)

    def test_validate_call_type_mismatch_boolean(self) -> None:
        # 'must_cite' must be boolean, but passing string
        params = {
            "query": "hello",
            "must_cite": "true"
        }
        with pytest.raises(ValueError) as exc_info:
            self.router.validate_call("search_web", params)
        
        assert "parameter 'must_cite' has invalid type" in str(exc_info.value)
        assert "Expected 'boolean', got 'str'" in str(exc_info.value)
        assert "search_web" in str(exc_info.value)

    def test_validate_call_type_mismatch_array(self) -> None:
        # 'preferred_sources' must be array, but passing dict
        params = {
            "query": "hello",
            "preferred_sources": {"site": "wikipedia.org"}
        }
        with pytest.raises(ValueError) as exc_info:
            self.router.validate_call("search_web", params)
        
        assert "parameter 'preferred_sources' has invalid type" in str(exc_info.value)
        assert "Expected 'array', got 'dict'" in str(exc_info.value)
        assert "search_web" in str(exc_info.value)

    def test_graceful_fallback_no_contract(self) -> None:
        # Dynamically register an in-process tool that has no physical contract file
        def my_custom_handler(params: dict[str, Any]) -> dict[str, Any]:
            return {"status": "ok"}
            
        self.router.register_tool("dynamic_tool", my_custom_handler)
        
        # Validating call should log warning but NOT raise any error because it falls back gracefully
        self.router.validate_call("dynamic_tool", {"any_arg": 123})
        
        # Routing should also complete successfully without validation crash
        result = self.router.route("dynamic_tool", {"any_arg": 123})
        assert result == {"status": "ok"}
