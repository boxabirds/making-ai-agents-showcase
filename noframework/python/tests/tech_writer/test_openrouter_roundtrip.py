"""
Simple round-trip test for OpenRouter cost tracking.

This test makes a real API call and verifies that cost is returned
in the response. It should be part of the standard test suite.
"""

import os

import pytest

from tech_writer.llm import LLMClient


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)
class TestOpenRouterRoundTrip:
    """Round-trip test for OpenRouter with cost tracking."""

    def test_cost_returned_in_response(self):
        """
        Make a simple call to OpenRouter and verify cost is returned.

        This is the canonical test that cost tracking works end-to-end.
        """
        client = LLMClient(
            model="openai/gpt-4o-mini",
            provider="openrouter",
            track_cost=True,
        )

        # Make a minimal call
        response, usage = client.chat(
            messages=[{"role": "user", "content": "Say 'test'."}]
        )

        # Verify response is valid
        assert response["content"] is not None
        assert len(response["content"]) > 0

        # Verify usage stats are populated
        assert usage.prompt_tokens > 0
        assert usage.completion_tokens > 0
        assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens

        # THIS IS THE KEY ASSERTION: cost should be in the response
        assert usage.cost_usd is not None, (
            "Cost not returned in response. "
            "OpenRouter should include cost in response.usage.cost "
            "when extra_body={'usage': {'include': True}} is set."
        )
        assert usage.cost_usd > 0, f"Cost should be positive, got {usage.cost_usd}"

        # Verify cost tracker accumulated the cost
        summary = client.get_cost_summary()
        assert summary.total_calls == 1
        assert summary.total_cost_usd == usage.cost_usd
        assert summary.total_tokens == usage.total_tokens
        assert summary.provider == "openrouter"
        assert summary.model == "openai/gpt-4o-mini"

        print(f"\n✓ Round-trip test passed:")
        print(f"  Response: {response['content'][:50]}...")
        print(f"  Tokens: {usage.total_tokens}")
        print(f"  Cost: ${usage.cost_usd:.8f}")
