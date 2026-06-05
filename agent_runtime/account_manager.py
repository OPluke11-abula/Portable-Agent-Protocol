"""Multi-account configuration manager for LLM auditing, locking, and auto-failover."""

from __future__ import annotations

import contextlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from agent_runtime.logger import get_logger

logger = get_logger(__name__)

try:
    import jsonschema
except ImportError:
    jsonschema = None


class AccountManager:
    """Thread-safe and process-safe manager for LLM account configurations and token usage auditing."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is not None:
            self.config_path = Path(config_path)
        else:
            # Standard resolution path
            candidates = [
                Path(".agent/memory/persistent/accounts.json"),
                Path(".agent/accounts.json"),
                Path("accounts.json"),
            ]
            self.config_path = candidates[0]
            for c in candidates:
                if c.exists():
                    self.config_path = c
                    break

        self._schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any] | None:
        """Find and load accounts-schema.json."""
        project_root = Path.cwd()
        for folder in ("spec", "schemas", ".agent/knowledge_base"):
            schema_path = project_root / folder / "accounts-schema.json"
            if schema_path.exists():
                try:
                    return json.loads(schema_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    logger.debug("Failed to parse schema at %s: %s", schema_path, exc)
        return None

    @contextlib.contextmanager
    def lock(self, timeout: float = 5.0):
        """Cross-platform and cross-process filesystem lock context manager."""
        lock_path = self.config_path.with_suffix(self.config_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        fd = None
        while True:
            try:
                # os.O_CREAT | os.O_EXCL | os.O_WRONLY is atomic on both Windows & POSIX systems
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Could not acquire lock on {self.config_path} within {timeout} seconds."
                    )
                time.sleep(0.02)
            except OSError as e:
                # In case the directory wasn't ready or some other system error
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"System error acquiring lock on {lock_path}: {e}")
                time.sleep(0.02)

        try:
            yield
        finally:
            if fd is not None:
                os.close(fd)
            try:
                os.unlink(lock_path)
            except OSError:
                pass

    def validate_data(self, data: dict[str, Any]) -> None:
        """Validate account manager data dict against JSON Schema."""
        if jsonschema is None:
            # Fallback basic schema validation
            if not isinstance(data, dict) or "accounts" not in data or not isinstance(data["accounts"], list):
                raise ValueError("Data must be an object with an 'accounts' list.")
            for idx, acc in enumerate(data["accounts"]):
                required = ["id", "provider", "api_key", "model", "pricing", "limits", "usage"]
                for req in required:
                    if req not in acc:
                        raise ValueError(f"Account at index {idx} is missing required field '{req}'.")
            return

        if self._schema is not None:
            try:
                jsonschema.validate(instance=data, schema=self._schema)
            except jsonschema.ValidationError as ve:
                raise ValueError(f"Accounts validation failed: {ve.message}") from ve

    def read_accounts(self) -> dict[str, Any]:
        """Loads raw accounts configuration with locking."""
        if not self.config_path.exists():
            return {"accounts": []}

        with self.lock():
            try:
                content = self.config_path.read_text(encoding="utf-8")
                data = json.loads(content)
                self.validate_data(data)
                return data
            except json.JSONDecodeError as exc:
                raise ValueError(f"Failed to parse accounts JSON: {exc}") from exc

    def _expand_value(self, val: str) -> str:
        """Helper to substitute environment variables in format ${VAR_NAME} or $VAR_NAME."""
        if not isinstance(val, str):
            return val
        # Matches ${VAR} or $VAR
        def repl(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))
        return re.sub(r"\${([A-Za-z0-9_]+)}|\$([A-Za-z0-9_]+)", repl, val)

    def get_accounts(self, expand_env: bool = True) -> list[dict[str, Any]]:
        """Returns the list of accounts with optional API key expansion."""
        data = self.read_accounts()
        accounts = data.get("accounts", [])
        if not expand_env:
            return accounts

        resolved_accounts = []
        for acc in accounts:
            copied = json.loads(json.dumps(acc))
            if "api_key" in copied and isinstance(copied["api_key"], str):
                copied["api_key"] = self._expand_value(copied["api_key"])
            resolved_accounts.append(copied)
        return resolved_accounts

    def get_active_account(self) -> dict[str, Any] | None:
        """Returns the first active account that has not exceeded its budget limit."""
        accounts = self.get_accounts(expand_env=True)
        for acc in accounts:
            status = acc.get("status", "active")
            max_cost = acc.get("limits", {}).get("max_cost_usd", float("inf"))
            current_cost = acc.get("usage", {}).get("total_cost_usd", 0.0)

            # Check if this account is active and has budget remaining
            if status == "active" and current_cost < max_cost:
                return acc
        return None

    def update_usage(self, account_id: str, prompt_tokens: int, completion_tokens: int) -> dict[str, Any]:
        """Atomically updates usage tokens and cost metrics for a given account ID."""
        with self.lock():
            if not self.config_path.exists():
                raise FileNotFoundError(f"Accounts config file not found: {self.config_path}")

            content = self.config_path.read_text(encoding="utf-8")
            data = json.loads(content)
            self.validate_data(data)

            target_acc = None
            for acc in data.get("accounts", []):
                if acc.get("id") == account_id:
                    target_acc = acc
                    break

            if not target_acc:
                raise ValueError(f"Account ID '{account_id}' not found in configuration.")

            # Retrieve pricing
            pricing = target_acc.get("pricing", {})
            prompt_price = pricing.get("prompt_price_per_million", 0.0)
            completion_price = pricing.get("completion_price_per_million", 0.0)

            # Calculate cost
            new_cost = (
                (prompt_tokens * prompt_price / 1_000_000.0) +
                (completion_tokens * completion_price / 1_000_000.0)
            )

            # Update usage metrics
            usage = target_acc.setdefault("usage", {})
            usage["prompt_tokens"] = usage.get("prompt_tokens", 0) + prompt_tokens
            usage["completion_tokens"] = usage.get("completion_tokens", 0) + completion_tokens
            
            new_total_cost = usage.get("total_cost_usd", 0.0) + new_cost
            usage["total_cost_usd"] = new_total_cost

            # Check budget limit and update status to exhausted if exceeded
            max_cost = target_acc.get("limits", {}).get("max_cost_usd", float("inf"))
            if new_total_cost >= max_cost:
                target_acc["status"] = "exhausted"

            # Flush write-through immediately
            self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return target_acc

    def suspend_account(self, account_id: str) -> dict[str, Any]:
        """Suspends an account due to provider API error or timeout."""
        with self.lock():
            if not self.config_path.exists():
                raise FileNotFoundError(f"Accounts config file not found: {self.config_path}")

            content = self.config_path.read_text(encoding="utf-8")
            data = json.loads(content)
            self.validate_data(data)

            target_acc = None
            for acc in data.get("accounts", []):
                if acc.get("id") == account_id:
                    target_acc = acc
                    break

            if not target_acc:
                raise ValueError(f"Account ID '{account_id}' not found in configuration.")

            # If it's already exhausted, keep it exhausted, otherwise mark as suspended
            if target_acc.get("status") != "exhausted":
                target_acc["status"] = "suspended"

            # Flush write-through immediately
            self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return target_acc

    def reset_suspended_accounts(self) -> int:
        """Resets all 'suspended' accounts back to 'active' state. Returns the reset count."""
        with self.lock():
            if not self.config_path.exists():
                return 0

            content = self.config_path.read_text(encoding="utf-8")
            data = json.loads(content)
            self.validate_data(data)

            reset_count = 0
            for acc in data.get("accounts", []):
                if acc.get("status") == "suspended":
                    acc["status"] = "active"
                    reset_count += 1

            if reset_count > 0:
                self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            
            return reset_count
