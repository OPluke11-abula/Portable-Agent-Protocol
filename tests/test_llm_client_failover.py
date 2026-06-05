"""Unit and integration tests for LLMClient failover, token auditing, and quota limits."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agent_runtime.account_manager import AccountManager
from agent_runtime.llm_client import (
    LLMClient,
    MockLLMClient,
    NoAvailableAccountsError,
    QuotaExceededError,
)


@pytest.fixture
def temp_accounts_file():
    test_data = {
        "accounts": [
            {
                "id": "acc-mock-1",
                "provider": "mock",
                "api_key": "secret-1",
                "model": "model-1",
                "pricing": {
                    "prompt_price_per_million": 10.0,
                    "completion_price_per_million": 20.0
                },
                "limits": {
                    "max_cost_usd": 1.0
                },
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_cost_usd": 0.0
                },
                "status": "active"
            },
            {
                "id": "acc-mock-2",
                "provider": "mock",
                "api_key": "secret-2",
                "model": "model-2",
                "pricing": {
                    "prompt_price_per_million": 1.0,
                    "completion_price_per_million": 2.0
                },
                "limits": {
                    "max_cost_usd": 0.5
                },
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_cost_usd": 0.0
                },
                "status": "active"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp.write(json.dumps(test_data, indent=2).encode("utf-8"))
        tmp_path = Path(tmp.name)

    yield tmp_path

    # Cleanup
    try:
        tmp_path.unlink()
    except OSError:
        pass
    
    lock_path = tmp_path.with_suffix(".json.lock")
    try:
        lock_path.unlink()
    except OSError:
        pass


def test_llm_client_success(temp_accounts_file):
    """Verifies normal execution pathway without errors."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    # Define normal mock behavior callback
    def normal_behavior(account, prompt, system_prompt):
        return {
            "text": "Hello user!",
            "prompt_tokens": 10,
            "completion_tokens": 5
        }

    mock = MockLLMClient(normal_behavior)
    client = LLMClient(account_manager=mgr, mock_client=mock)
    
    res = client.call("Hi", "system instructions")
    
    assert res["text"] == "Hello user!"
    assert res["prompt_tokens"] == 10
    assert res["completion_tokens"] == 5
    assert res["account_id"] == "acc-mock-1"
    assert res["model"] == "model-1"
    
    # Verify pricing cost logged
    # prompt = 10 * 10 / 1_000_000 = 0.0001
    # completion = 5 * 20 / 1_000_000 = 0.0001
    # Total = 0.0002
    assert res["total_cost_usd"] == 0.0002


def test_llm_client_failover_mechanism(temp_accounts_file):
    """Verifies that if primary account raises an error, failover occurs and primary is suspended."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    def failover_behavior(account, prompt, system_prompt):
        if account["id"] == "acc-mock-1":
            raise RuntimeError("API Rate Limit Exceeded")
        return {
            "text": "Hello from account 2!",
            "prompt_tokens": 20,
            "completion_tokens": 10
        }

    mock = MockLLMClient(failover_behavior)
    client = LLMClient(account_manager=mgr, mock_client=mock)
    
    res = client.call("Hi")
    
    # Assert result comes from account 2
    assert res["text"] == "Hello from account 2!"
    assert res["account_id"] == "acc-mock-2"
    assert res["model"] == "model-2"
    
    # Assert account 1 is suspended
    accounts = mgr.get_accounts(expand_env=False)
    assert accounts[0]["status"] == "suspended"
    assert accounts[1]["status"] == "active"


def test_llm_client_exhaustion_errors(temp_accounts_file):
    """Verifies raising QuotaExceededError when accounts have reached budgets."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    # Artificially update usage to exceed budgets
    mgr.update_usage("acc-mock-1", 100_000, 0)  # max limit = 1.0, 100_000 * 10 = 1.0 -> exhausted
    mgr.update_usage("acc-mock-2", 500_000, 0)  # max limit = 0.5, 500_000 * 1 = 0.5 -> exhausted
    
    client = LLMClient(account_manager=mgr, mock_client=None)
    
    with pytest.raises(QuotaExceededError, match="exhausted their cost budget limit"):
        client.call("Hello")


def test_llm_client_no_active_available(temp_accounts_file):
    """Verifies raising NoAvailableAccountsError when all accounts are suspended."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    mgr.suspend_account("acc-mock-1")
    mgr.suspend_account("acc-mock-2")
    
    client = LLMClient(account_manager=mgr, mock_client=None)
    
    with pytest.raises(NoAvailableAccountsError, match="No active LLM accounts available"):
        client.call("Hello")


def test_heuristic_token_counting(temp_accounts_file):
    """Verifies backup token counting uses character-length heuristic."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    # Return dict missing prompt_tokens and completion_tokens
    def lack_tokens_behavior(account, prompt, system_prompt):
        return {
            "text": "This is a twelve word mock result text..."  # 42 chars
        }

    mock = MockLLMClient(lack_tokens_behavior)
    client = LLMClient(account_manager=mgr, mock_client=mock)
    
    # Prompt is "Hi" (2 chars)
    res = client.call("Hi", system_prompt=None)
    
    # Prompt tokens = ceil(2/4) = 1
    # Completion tokens = ceil(41/4) = 11
    assert res["prompt_tokens"] == 1
    assert res["completion_tokens"] == 11
