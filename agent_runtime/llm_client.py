"""LLM Client interface with built-in auto-failover, heuristic token auditing, and cost logging."""

from __future__ import annotations

import math
from typing import Any, Callable

from .account_manager import AccountManager
from .logger import get_logger

logger = get_logger(__name__)


class NoAvailableAccountsError(RuntimeError):
    """Raised when there are no accounts registered or none are currently active/budget-compliant."""
    pass


class QuotaExceededError(RuntimeError):
    """Raised when all active accounts have exceeded their maximum cost budget limit."""
    pass


class BaseLLMClient:
    """Base abstract class for LLM client providers."""

    def invoke(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        """Invokes LLM request and returns dict containing:

        - text: str
        - prompt_tokens: int
        - completion_tokens: int
        - model: str
        """
        raise NotImplementedError("Subclasses must implement invoke()")


class MockLLMClient(BaseLLMClient):
    """Mock LLM client useful for testing failover scenarios and token auditing behavior."""

    def __init__(self, behavior_callback: Callable[[dict[str, Any], str, str | None], dict[str, Any]]) -> None:
        """Args:

        behavior_callback: A function taking (account_dict, prompt,
        system_prompt) and returning a standard result dict or raising an
        exception.
        """
        self.behavior_callback = behavior_callback
        self.invoked_accounts: list[str] = []

    def invoke_with_account(self, account: dict[str, Any], prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        self.invoked_accounts.append(account["id"])
        return self.behavior_callback(account, prompt, system_prompt)


class LLMClient:
    """LLM client wrapper providing transparent multi-provider routing, failover retry loops, and token counting."""

    def __init__(self, account_manager: AccountManager, mock_client: MockLLMClient | None = None) -> None:
        self.account_manager = account_manager
        self.mock_client = mock_client

    def heuristic_token_count(self, text: str) -> int:
        """Estimate token count based on standard character heuristics (1 token approx.

        4 characters).
        """
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4.0))

    def _execute_api_call(self, account: dict[str, Any], prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        """Dispatches request to actual API provider or mock provider."""
        provider = account.get("provider")
        model = account.get("model")

        if provider == "mock" and self.mock_client:
            return self.mock_client.invoke_with_account(account, prompt, system_prompt)

        # In production, we'd dispatch to actual client libraries (gemini, openai, anthropic).
        # Since this is a reference local protocol and actual providers may not be set up/paid,
        # we raise NotImplementedError for non-mock providers unless they are mocked.
        # But we will simulate/stub simple responses to keep it runnable or raise standard errors.
        raise NotImplementedError(
            f"Provider '{provider}' integration is not implemented. Use 'mock' provider for reference runs and testing."
        )

    def call(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        """Executes LLM invocation in an auto-failover retry loop.

        Args:
            prompt: User message prompt.
            system_prompt: System context instructions.

        Returns:
            Dict containing result text and audited usage metrics.
        """
        attempt = 0
        max_attempts = 10  # Prevent infinite loops in unexpected states

        while attempt < max_attempts:
            attempt += 1

            # 1. Fetch active account
            account = self.account_manager.get_active_account()
            if not account:
                # Distinguish between having no accounts at all vs all exhausted
                all_accounts = self.account_manager.get_accounts(expand_env=False)
                if not all_accounts:
                    raise NoAvailableAccountsError("No LLM accounts registered in configuration.")
                
                # Check if all accounts are exhausted
                all_exhausted = True
                for acc in all_accounts:
                    if acc.get("status") != "exhausted":
                        all_exhausted = False
                        break
                
                if all_exhausted:
                    raise QuotaExceededError("All LLM accounts have exhausted their cost budget limit.")
                else:
                    raise NoAvailableAccountsError("No active LLM accounts available (all may be currently suspended).")

            account_id = account["id"]
            logger.info("Executing LLM call using account '%s' (model: %s)", account_id, account.get("model"))

            try:
                # 2. Invoke the model call
                result = self._execute_api_call(account, prompt, system_prompt)
                
                # 3. Parse tokens and cost
                prompt_tokens = result.get("prompt_tokens")
                completion_tokens = result.get("completion_tokens")
                text = result.get("text", "")

                # Heuristic counting fallbacks if missing
                if prompt_tokens is None:
                    prompt_tokens = self.heuristic_token_count(prompt) + (self.heuristic_token_count(system_prompt) if system_prompt else 0)
                if completion_tokens is None:
                    completion_tokens = self.heuristic_token_count(text)

                # 4. Atomically record usage and cost
                updated_acc = self.account_manager.update_usage(account_id, prompt_tokens, completion_tokens)
                
                # 5. Return structured result
                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "model": account.get("model"),
                    "account_id": account_id,
                    "total_cost_usd": updated_acc.get("usage", {}).get("total_cost_usd", 0.0),
                }

            except Exception as exc:
                # Mark as suspended and log failure
                logger.warning("LLM call failed on account '%s': %s. Initiating failover...", account_id, exc)
                self.account_manager.suspend_account(account_id)
                # Continue loop to fetch the next active account

        raise NoAvailableAccountsError("Maximum failover retry attempts exceeded. No functional accounts found.")
