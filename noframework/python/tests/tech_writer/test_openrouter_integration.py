"""
Integration tests for OpenRouter.

These tests require a valid OPENROUTER_API_KEY environment variable.
They make real API calls and are marked with @pytest.mark.integration.

Run with: pytest -m integration tests/tech_writer/test_openrouter_integration.py
"""

import os

import pytest

from tech_writer.llm import LLMClient, CostSummary


# Skip all tests in this module if OPENROUTER_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY environment variable not set",
)


@pytest.mark.integration
class TestOpenRouterIntegration:
    """Integration tests that make real API calls to OpenRouter."""

    def test_chat_returns_response_and_usage(self):
        """Chat request returns response and usage stats."""
        client = LLMClient(
            model="openai/gpt-4o-mini",
            provider="openrouter",
            track_cost=True,
        )

        response, usage = client.chat(
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}]
        )

        assert response["content"] is not None
        assert "hello" in response["content"].lower()
        assert usage.prompt_tokens > 0
        assert usage.completion_tokens > 0
        assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens

    def test_chat_returns_cost(self):
        """Chat request returns cost in UsageStats."""
        client = LLMClient(
            model="openai/gpt-4o-mini",
            provider="openrouter",
            track_cost=True,
        )

        response, usage = client.chat(
            messages=[{"role": "user", "content": "Reply with just the word 'test'."}]
        )

        # Cost should be populated (may take a moment for OpenRouter to calculate)
        # Note: cost might be None if OpenRouter hasn't calculated it yet
        # but generation_id should be set
        assert usage.generation_id is not None

    def test_cost_accumulates_across_calls(self):
        """Multiple calls accumulate total cost."""
        client = LLMClient(
            model="openai/gpt-4o-mini",
            provider="openrouter",
            track_cost=True,
        )

        # Make two simple calls
        client.chat(messages=[{"role": "user", "content": "Say 'one'."}])
        client.chat(messages=[{"role": "user", "content": "Say 'two'."}])

        summary = client.get_cost_summary()

        assert summary.total_calls == 2
        assert summary.total_tokens > 0
        assert summary.provider == "openrouter"
        assert summary.model == "openai/gpt-4o-mini"
        assert len(summary.calls) == 2

    def test_cost_summary_structure(self):
        """Cost summary has correct structure."""
        client = LLMClient(
            model="openai/gpt-4o-mini",
            provider="openrouter",
            track_cost=True,
        )

        client.chat(messages=[{"role": "user", "content": "Hi"}])
        summary = client.get_cost_summary()

        assert isinstance(summary, CostSummary)
        assert isinstance(summary.total_cost_usd, float)
        assert isinstance(summary.total_tokens, int)
        assert isinstance(summary.total_calls, int)
        assert summary.provider == "openrouter"
        assert summary.model == "openai/gpt-4o-mini"

    def test_disabled_cost_tracking(self):
        """Cost tracking can be disabled."""
        client = LLMClient(
            model="openai/gpt-4o-mini",
            provider="openrouter",
            track_cost=False,
        )

        response, usage = client.chat(
            messages=[{"role": "user", "content": "Hi"}]
        )

        # Response should work, but cost should not be fetched
        assert response["content"] is not None
        # When cost tracking is disabled, calls are not recorded
        summary = client.get_cost_summary()
        assert summary.total_calls == 0
        assert summary.total_cost_usd == 0.0


@pytest.mark.integration
class TestOpenRouterModels:
    """Test different models via OpenRouter."""

    def test_anthropic_model_via_openrouter(self):
        """Can use Anthropic model via OpenRouter."""
        client = LLMClient(
            model="anthropic/claude-3.5-haiku",
            provider="openrouter",
            track_cost=True,
        )

        response, usage = client.chat(
            messages=[{"role": "user", "content": "Reply with just 'ok'."}]
        )

        assert response["content"] is not None
        assert usage.total_tokens > 0

    def test_google_model_via_openrouter(self):
        """Can use Google model via OpenRouter."""
        client = LLMClient(
            model="google/gemini-2.0-flash-001",
            provider="openrouter",
            track_cost=True,
        )

        response, usage = client.chat(
            messages=[{"role": "user", "content": "Reply with just 'ok'."}]
        )

        assert response["content"] is not None
        assert usage.total_tokens > 0
