"""Unit tests for AccountManager including schema validation, locks, key expansion, and quota exhaustion."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path

import pytest

from agent_runtime.account_manager import AccountManager


@pytest.fixture
def temp_accounts_file():
    """Fixture to create a temporary accounts.json file for isolated testing."""
    test_data = {
        "accounts": [
            {
                "id": "acc-gemini-primary",
                "provider": "gemini",
                "api_key": "${TEST_GEMINI_KEY}",
                "model": "gemini-1.5-pro",
                "pricing": {
                    "prompt_price_per_million": 7.0,
                    "completion_price_per_million": 21.0
                },
                "limits": {
                    "max_cost_usd": 10.0
                },
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_cost_usd": 0.0
                },
                "status": "active"
            },
            {
                "id": "acc-gemini-backup",
                "provider": "gemini",
                "api_key": "static-backup-key-abc",
                "model": "gemini-1.5-flash",
                "pricing": {
                    "prompt_price_per_million": 0.35,
                    "completion_price_per_million": 1.05
                },
                "limits": {
                    "max_cost_usd": 2.0
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

    os.environ["TEST_GEMINI_KEY"] = "gemini-env-key-secret-999"

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

    if "TEST_GEMINI_KEY" in os.environ:
        del os.environ["TEST_GEMINI_KEY"]


def test_account_manager_schema_validation(temp_accounts_file):
    """Verifies that the manager correctly loads and validates schema."""
    mgr = AccountManager(config_path=temp_accounts_file)
    accounts = mgr.get_accounts(expand_env=False)
    assert len(accounts) == 2
    assert accounts[0]["id"] == "acc-gemini-primary"
    
    # Test validation failure with bad data
    bad_data = {"accounts": [{"id": "acc-bad"}]}  # missing required fields
    with pytest.raises(ValueError, match="Accounts validation failed|missing required field"):
        mgr.validate_data(bad_data)


def test_credential_expansion(temp_accounts_file):
    """Verifies environment variables are expanded dynamically but not saved to disk."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    # Expanded read
    accounts = mgr.get_accounts(expand_env=True)
    assert accounts[0]["api_key"] == "gemini-env-key-secret-999"
    assert accounts[1]["api_key"] == "static-backup-key-abc"
    
    # Check that disk content still contains the placeholder template
    raw_content = temp_accounts_file.read_text(encoding="utf-8")
    assert "${TEST_GEMINI_KEY}" in raw_content
    assert "gemini-env-key-secret-999" not in raw_content


def test_active_account_selection(temp_accounts_file):
    """Verifies routing selects the correct first active, non-exhausted account."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    # At start, active is primary
    acc = mgr.get_active_account()
    assert acc is not None
    assert acc["id"] == "acc-gemini-primary"
    
    # Suspend primary
    mgr.suspend_account("acc-gemini-primary")
    
    # Active should now be backup
    acc = mgr.get_active_account()
    assert acc is not None
    assert acc["id"] == "acc-gemini-backup"


def test_usage_cost_updates_and_exhaustion(temp_accounts_file):
    """Verifies cost formulas, atomic flush updates, and budget exhaustion transition."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    # Prompt pricing: 7.0 per million, Completion: 21.0 per million
    # prompt = 1,000,000 tokens -> 7.0 USD
    # completion = 100,000 tokens -> 2.1 USD
    # Total cost = 9.1 USD
    mgr.update_usage("acc-gemini-primary", 1_000_000, 100_000)
    
    accounts = mgr.get_accounts(expand_env=False)
    primary = accounts[0]
    assert primary["usage"]["prompt_tokens"] == 1_000_000
    assert primary["usage"]["completion_tokens"] == 100_000
    assert primary["usage"]["total_cost_usd"] == 9.1
    assert primary["status"] == "active"
    
    # Add another 1,000,000 tokens of prompt -> cost goes over max limit of 10.0
    mgr.update_usage("acc-gemini-primary", 1_000_000, 0)
    
    accounts = mgr.get_accounts(expand_env=False)
    primary = accounts[0]
    assert primary["usage"]["total_cost_usd"] == 16.1
    assert primary["status"] == "exhausted"
    
    # Exhausted account should no longer be returned as active
    acc = mgr.get_active_account()
    assert acc is not None
    assert acc["id"] == "acc-gemini-backup"


def test_suspension_and_reset(temp_accounts_file):
    """Verifies accounts can be suspended and reset back to active."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    mgr.suspend_account("acc-gemini-primary")
    mgr.suspend_account("acc-gemini-backup")
    
    # Both suspended, no active account
    assert mgr.get_active_account() is None
    
    # Reset all suspended
    reset_count = mgr.reset_suspended_accounts()
    assert reset_count == 2
    
    # Active account is restored to primary
    acc = mgr.get_active_account()
    assert acc is not None
    assert acc["id"] == "acc-gemini-primary"


def test_concurrency_locking(temp_accounts_file):
    """Verifies that simultaneous calls serialize perfectly under filesystem locks."""
    mgr = AccountManager(config_path=temp_accounts_file)
    
    def worker():
        for _ in range(5):
            mgr.update_usage("acc-gemini-backup", 10_000, 10_000)
            time.sleep(0.01)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # Each update adds 10,000 prompt + 10,000 completion tokens
    # 5 threads * 5 runs = 25 total runs
    # Total tokens = 25 * 10,000 = 250,000
    accounts = mgr.get_accounts(expand_env=False)
    backup = accounts[1]
    assert backup["usage"]["prompt_tokens"] == 250_000
    assert backup["usage"]["completion_tokens"] == 250_000
