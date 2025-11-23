"""
Unit tests for OpenRouter integration.

Tests for:
- ProviderConfig
- CostTracker
- LLMClient provider support
"""

import os
from unittest.mock import patch

import pytest

from tech_writer.llm import (
    CostSummary,
    CostTracker,
    LLMClient,
    ProviderConfig,
    UsageStats,
    OPENROUTER_BASE_URL,
)


class TestProviderConfig:
    """Tests for ProviderConfig class."""

    def test_openai_config_uses_defaults(self):
        """OpenAI config uses correct defaults."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = ProviderConfig.from_provider("openai")

        assert config.provider == "openai"
        assert config.base_url is None
        assert config.api_key == "test-key"
        assert config.default_headers == {}

    def test_openrouter_config_sets_base_url_and_headers(self):
        """OpenRouter config sets base_url and headers."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-test-key"}):
            config = ProviderConfig.from_provider(
                "openrouter",
                app_name="test_app",
                app_url="https://test.example.com",
            )

        assert config.provider == "openrouter"
        assert config.base_url == OPENROUTER_BASE_URL
        assert config.api_key == "or-test-key"
        assert config.default_headers["HTTP-Referer"] == "https://test.example.com"
        assert config.default_headers["X-Title"] == "test_app"

    def test_openrouter_requires_referer_header(self):
        """OpenRouter config includes HTTP-Referer header."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-test-key"}):
            config = ProviderConfig.from_provider("openrouter")

        assert "HTTP-Referer" in config.default_headers
        assert "X-Title" in config.default_headers

    def test_unknown_provider_raises_valueerror(self):
        """Unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderConfig.from_provider("unknown_provider")

    def test_missing_openai_key_raises_valueerror(self):
        """Missing OpenAI API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure OPENAI_API_KEY is not set
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ValueError, match="OpenAI API key required"):
                ProviderConfig.from_provider("openai")

    def test_missing_openrouter_key_raises_valueerror(self):
        """Missing OpenRouter API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure OPENROUTER_API_KEY is not set
            os.environ.pop("OPENROUTER_API_KEY", None)
            with pytest.raises(ValueError, match="OpenRouter API key required"):
                ProviderConfig.from_provider("openrouter")

    def test_explicit_api_key_overrides_env(self):
        """Explicit API key overrides environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            config = ProviderConfig.from_provider("openai", api_key="explicit-key")

        assert config.api_key == "explicit-key"


class TestCostTracker:
    """Tests for CostTracker class."""

    def test_disabled_tracker_does_not_record(self):
        """Disabled tracker doesn't record calls."""
        tracker = CostTracker(enabled=False)
        usage = UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.001)

        tracker.record_call(usage)

        # Should not record when disabled
        assert len(tracker.calls) == 0
        assert tracker.total_cost == 0.0

    def test_accumulates_costs(self):
        """Costs accumulate across calls."""
        tracker = CostTracker(enabled=True)

        usage1 = UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.001)
        tracker.record_call(usage1)

        usage2 = UsageStats(prompt_tokens=200, completion_tokens=100, total_tokens=300, cost_usd=0.002)
        tracker.record_call(usage2)

        assert tracker.total_cost == 0.003
        assert tracker.total_tokens == 450
        assert len(tracker.calls) == 2

    def test_handles_none_cost(self):
        """Tracker handles None cost gracefully."""
        tracker = CostTracker(enabled=True)
        usage = UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=None)

        tracker.record_call(usage)

        # Should record but not add to total_cost
        assert len(tracker.calls) == 1
        assert tracker.total_cost == 0.0
        assert tracker.total_tokens == 150

    def test_summary_includes_all_calls(self):
        """Summary includes all recorded calls."""
        tracker = CostTracker(enabled=True)

        for i in range(3):
            usage = UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.001)
            tracker.record_call(usage)

        summary = tracker.get_summary(provider="openrouter", model="test-model")

        assert summary.total_calls == 3
        assert summary.total_cost_usd == 0.003
        assert summary.provider == "openrouter"
        assert summary.model == "test-model"
        assert len(summary.calls) == 3


class TestLLMClientProvider:
    """Tests for LLMClient provider support."""

    def test_openai_provider_no_extra_headers(self):
        """OpenAI provider doesn't add extra headers."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="gpt-5.1", provider="openai")

        assert client.provider == "openai"
        assert client.config.default_headers == {}

    def test_openrouter_provider_sets_headers(self):
        """OpenRouter provider sets required headers."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-test-key"}):
            client = LLMClient(model="openai/gpt-5.1", provider="openrouter")

        assert client.provider == "openrouter"
        assert "HTTP-Referer" in client.config.default_headers
        assert "X-Title" in client.config.default_headers

    def test_track_cost_default_true_for_openrouter(self):
        """track_cost defaults to True for OpenRouter."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-test-key"}):
            client = LLMClient(model="openai/gpt-5.1", provider="openrouter")

        assert client.track_cost is True

    def test_track_cost_default_false_for_openai(self):
        """track_cost defaults to False for OpenAI."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="gpt-5.1", provider="openai")

        assert client.track_cost is False

    def test_track_cost_can_be_overridden(self):
        """track_cost can be explicitly set."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-test-key"}):
            client = LLMClient(
                model="openai/gpt-5.1",
                provider="openrouter",
                track_cost=False,
            )

        assert client.track_cost is False

    def test_get_cost_summary_returns_summary(self):
        """get_cost_summary returns CostSummary."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(model="gpt-5.1", provider="openai")

        summary = client.get_cost_summary()

        assert isinstance(summary, CostSummary)
        assert summary.provider == "openai"
        assert summary.model == "gpt-5.1"


class TestUsageStats:
    """Tests for UsageStats dataclass."""

    def test_default_values(self):
        """UsageStats has correct defaults."""
        stats = UsageStats()

        assert stats.prompt_tokens == 0
        assert stats.completion_tokens == 0
        assert stats.total_tokens == 0
        assert stats.cost_usd is None
        assert stats.cached_tokens == 0
        assert stats.cache_discount == 0.0
        assert stats.generation_id is None

    def test_all_fields_settable(self):
        """All UsageStats fields can be set."""
        stats = UsageStats(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.001,
            cached_tokens=20,
            cache_discount=0.5,
            generation_id="gen-123",
        )

        assert stats.prompt_tokens == 100
        assert stats.completion_tokens == 50
        assert stats.total_tokens == 150
        assert stats.cost_usd == 0.001
        assert stats.cached_tokens == 20
        assert stats.cache_discount == 0.5
        assert stats.generation_id == "gen-123"


class TestCostSummary:
    """Tests for CostSummary dataclass."""

    def test_default_values(self):
        """CostSummary has correct defaults."""
        summary = CostSummary()

        assert summary.total_cost_usd == 0.0
        assert summary.total_tokens == 0
        assert summary.total_calls == 0
        assert summary.provider == ""
        assert summary.model == ""
        assert summary.calls == []

    def test_all_fields_settable(self):
        """All CostSummary fields can be set."""
        calls = [UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150)]
        summary = CostSummary(
            total_cost_usd=0.05,
            total_tokens=1500,
            total_calls=10,
            provider="openrouter",
            model="openai/gpt-5.1",
            calls=calls,
        )

        assert summary.total_cost_usd == 0.05
        assert summary.total_tokens == 1500
        assert summary.total_calls == 10
        assert summary.provider == "openrouter"
        assert summary.model == "openai/gpt-5.1"
        assert len(summary.calls) == 1
