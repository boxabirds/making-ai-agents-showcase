# OpenRouter Integration Design

## Overview

Integrate [OpenRouter](https://openrouter.ai) as an LLM API provider for tech_writer, enabling:
- Access to 200+ models from multiple providers via single API
- Automatic cost tracking per request
- Cost reporting in JSON output

## Why OpenRouter

1. **Model flexibility**: Access OpenAI, Anthropic, Google, Meta, Mistral, etc. with one API key
2. **Built-in cost tracking**: Returns actual cost in response (no manual calculation needed)
3. **OpenAI-compatible**: Uses same API format, minimal code changes
4. **Fallback routing**: Can auto-route to cheaper/faster models

## API Details

### Base URL
```
https://openrouter.ai/api/v1
```

### Authentication
- API key from [OpenRouter Dashboard](https://openrouter.ai/keys)
- Environment variable: `OPENROUTER_API_KEY`
- Header: `Authorization: Bearer <key>`

### Required Headers
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "https://github.com/your-repo",  # Required: identifies your app
    "X-Title": "tech_writer",                         # Optional: app name for dashboard
}
```

### Model Format
```
provider/model-name
```

Examples:
- `openai/gpt-4o`
- `openai/gpt-5.1`
- `anthropic/claude-sonnet-4`
- `google/gemini-2.0-flash`
- `meta-llama/llama-3.1-405b-instruct`

### Usage Tracking

Enable with `extra_body` parameter:
```python
response = client.chat.completions.create(
    model="openai/gpt-5.1",
    messages=[...],
    extra_body={
        "usage": {"include": True}
    }
)
```

### Response Format with Usage

```json
{
  "id": "gen-xxxxx",
  "model": "openai/gpt-5.1",
  "choices": [...],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 50,
    "total_tokens": 200,
    "prompt_tokens_details": {
      "cached_tokens": 0
    }
  }
}
```

### Getting Cost Data

Option 1: Query generation endpoint after request:
```
GET /api/v1/generation?id={generation_id}
```

Returns:
```json
{
  "id": "gen-xxxxx",
  "total_cost": 0.00234,
  "native_tokens_prompt": 145,
  "native_tokens_completion": 48,
  "cache_discount": 0
}
```

Option 2: Use `X-OpenRouter-Include-Cost: true` header (if available)

## CLI Design

### New Arguments

```
--provider {openai,openrouter}    LLM provider (default: openai)
--openrouter-key KEY              OpenRouter API key (or OPENROUTER_API_KEY env)
--no-track-cost                   Disable cost tracking (enabled by default for OpenRouter)
```

Cost tracking is **enabled by default** when using OpenRouter since it's a key benefit of the platform and adds minimal overhead.

### Model Specification

When using OpenRouter, models use `provider/model` format:
```bash
# OpenAI direct
python -m tech_writer --prompt foo.txt --repo . --model gpt-5.1

# OpenRouter
python -m tech_writer --prompt foo.txt --repo . \
    --provider openrouter \
    --model openai/gpt-5.1

# OpenRouter with different provider's model
python -m tech_writer --prompt foo.txt --repo . \
    --provider openrouter \
    --model anthropic/claude-sonnet-4
```

### Environment Variables

```bash
# OpenAI direct
export OPENAI_API_KEY=sk-...

# OpenRouter
export OPENROUTER_API_KEY=sk-or-...
```

## Implementation

### 1. LLMClient Changes

```python
# tech_writer/llm.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class UsageStats:
    """Token and cost statistics for an LLM call."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None  # Only with OpenRouter
    cached_tokens: int = 0
    cache_discount: float = 0.0


class LLMClient:
    def __init__(
        self,
        model: str = "gpt-5.1",
        provider: str = "openai",  # or "openrouter"
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        track_cost: Optional[bool] = None,  # Default: True for openrouter, False for openai
        app_name: str = "tech_writer",
        app_url: str = "https://github.com/user/tech_writer",
    ):
        self.model = model
        self.provider = provider
        # Cost tracking on by default for OpenRouter
        self.track_cost = track_cost if track_cost is not None else (provider == "openrouter")
        self.total_cost = 0.0
        self.total_tokens = 0

        # Configure based on provider
        if provider == "openrouter":
            self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            self.default_headers = {
                "HTTP-Referer": app_url,
                "X-Title": app_name,
            }
        else:
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            self.base_url = base_url
            self.default_headers = {}

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.default_headers,
        )

    def chat(self, messages, tools=None, **kwargs) -> tuple[dict, UsageStats]:
        """Send chat request, return response and usage stats."""

        request_kwargs = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            request_kwargs["tools"] = tools

        # Enable usage tracking for OpenRouter
        if self.provider == "openrouter" and self.track_cost:
            request_kwargs["extra_body"] = {"usage": {"include": True}}

        response = self._client.chat.completions.create(**request_kwargs)

        # Extract usage stats
        usage = UsageStats(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        # Get cost from OpenRouter response
        if self.provider == "openrouter" and self.track_cost:
            usage.cost_usd = self._get_generation_cost(response.id)
            self.total_cost += usage.cost_usd or 0

        self.total_tokens += usage.total_tokens

        return self._parse_response(response), usage

    def _get_generation_cost(self, generation_id: str) -> Optional[float]:
        """Query OpenRouter for generation cost."""
        try:
            import httpx
            resp = httpx.get(
                f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if resp.status_code == 200:
                return resp.json().get("total_cost")
        except Exception:
            pass
        return None

    def get_cost_summary(self) -> dict:
        """Return cumulative cost statistics."""
        return {
            "total_cost_usd": self.total_cost,
            "total_tokens": self.total_tokens,
            "provider": self.provider,
            "model": self.model,
        }
```

### 2. Pipeline Integration

```python
# tech_writer/orchestrator.py

def run_pipeline(..., track_cost: bool = False) -> tuple[str, CacheStore, dict]:
    """
    Returns:
        Tuple of (report_markdown, cache_store, cost_stats)
    """
    llm = LLMClient(
        model=model,
        provider=provider,
        track_cost=track_cost,
    )

    # ... run pipeline ...

    cost_stats = llm.get_cost_summary()
    return report, store, cost_stats
```

### 3. CLI Integration

```python
# tech_writer/cli.py

parser.add_argument(
    "--provider",
    choices=["openai", "openrouter"],
    default="openai",
    help="LLM provider",
)
parser.add_argument(
    "--no-track-cost",
    action="store_true",
    help="Disable cost tracking (enabled by default for OpenRouter)",
)
```

### 4. JSON Output with Cost

```python
if args.eval_json:
    output = {
        "report": report,
        "citations": citation_results,
        "cost": cost_stats if args.track_cost else None,
    }
    print(json.dumps(output, indent=2))
```

Example output:
```json
{
  "report": "# Architecture Overview\n...",
  "citations": {
    "total": 45,
    "valid": 42,
    "invalid": 3
  },
  "cost": {
    "total_cost_usd": 0.0234,
    "total_tokens": 15420,
    "provider": "openrouter",
    "model": "openai/gpt-5.1"
  }
}
```

## Cost Tracking Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        tech_writer CLI                          │
│                                                                 │
│  --provider openrouter --track-cost --eval-json                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         LLMClient                               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Phase 1    │    │  Phase 2    │    │  Phase 3    │        │
│  │ Exploration │───▶│  Outline    │───▶│  Sections   │        │
│  │             │    │             │    │             │        │
│  │ cost: $0.01 │    │ cost: $0.002│    │ cost: $0.02 │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                              │                                  │
│                              ▼                                  │
│                    total_cost += each call                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OpenRouter API                              │
│                                                                 │
│  POST /api/v1/chat/completions                                 │
│    ← usage: {prompt_tokens, completion_tokens}                 │
│                                                                 │
│  GET /api/v1/generation?id=xxx                                 │
│    ← total_cost: 0.00234                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Migration Path

### Phase 1: Add Provider Support
- Add `--provider` flag
- Support OpenRouter base URL and headers
- Models work with `provider/model` format

### Phase 2: Add Cost Tracking
- Query generation endpoint after each call
- Accumulate costs in LLMClient
- Add `--track-cost` flag

### Phase 3: JSON Output Integration
- Include cost in `--eval-json` output
- Add cost to logging output

## Testing

```bash
# Test OpenRouter connection (cost tracking enabled by default)
python -m tech_writer --prompt test.txt --repo . \
    --provider openrouter \
    --model openai/gpt-4o-mini \
    --log-level DEBUG

# Verify cost in JSON output
python -m tech_writer --prompt test.txt --repo . \
    --provider openrouter \
    --model openai/gpt-5.1 \
    --eval-json

# Disable cost tracking if needed
python -m tech_writer --prompt test.txt --repo . \
    --provider openrouter \
    --model openai/gpt-5.1 \
    --no-track-cost
```

## References

- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart)
- [OpenRouter Usage Accounting](https://openrouter.ai/docs/use-cases/usage-accounting)
- [OpenRouter API Parameters](https://openrouter.ai/docs/api-reference/parameters)
- [OpenRouter Models](https://openrouter.ai/models)
