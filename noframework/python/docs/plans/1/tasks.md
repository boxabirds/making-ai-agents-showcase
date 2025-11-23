# Feature 1: OpenRouter Integration - Task Plan

## Overview

Implementation tasks for OpenRouter integration with cost tracking.

## Task Summary

| ID | Task | Status | Dependencies |
|----|------|--------|--------------|
| 1-1 | Add data types to llm.py | pending | - |
| 1-2 | Implement CostTracker class | pending | 1-1 |
| 1-3 | Implement ProviderConfig class | pending | 1-1 |
| 1-4 | Modify LLMClient for provider support | pending | 1-2, 1-3 |
| 1-5 | Add CLI arguments | pending | - |
| 1-6 | Integrate cost tracking in orchestrator | pending | 1-4, 1-5 |
| 1-7 | Add unit tests | pending | 1-4 |
| 1-8 | Add integration tests | pending | 1-6 |
| 1-9 | Add BDD feature tests | pending | 1-8 |
| 1-10 | Extend metadata output with cost | pending | 1-6, Feature 2 |

## Task Details

### 1-1: Add data types to llm.py

**Requirements:**
- Add `UsageStats` dataclass with fields: `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`, `cached_tokens`, `cache_discount`, `generation_id`
- Add `CostSummary` dataclass with fields: `total_cost_usd`, `total_tokens`, `total_calls`, `provider`, `model`, `calls`
- All fields with Optional types must have defaults

**Acceptance Criteria:**
- Dataclasses are importable from `tech_writer.llm`
- Type hints are complete and mypy-clean

---

### 1-2: Implement CostTracker class

**Requirements:**
- Implement `CostTracker` class with `OPENROUTER_GENERATION_URL` constant
- Constructor takes `api_key: str` and `enabled: bool = True`
- `record_call(generation_id, usage)` fetches cost and accumulates totals
- `_fetch_generation_cost(generation_id)` makes GET request to OpenRouter
- `get_summary(provider, model)` returns `CostSummary`
- Cost fetch errors are logged as warnings, not raised

**Acceptance Criteria:**
- Disabled tracker skips API calls entirely
- API errors don't crash the tracker
- Costs accumulate correctly across multiple calls

---

### 1-3: Implement ProviderConfig class

**Requirements:**
- Implement `ProviderConfig` dataclass with fields: `provider`, `base_url`, `api_key`, `default_headers`
- Implement `from_provider()` factory method
- OpenAI config: no base_url override, no extra headers, uses `OPENAI_API_KEY`
- OpenRouter config: base_url `https://openrouter.ai/api/v1`, headers `HTTP-Referer` and `X-Title`, uses `OPENROUTER_API_KEY`
- Raise `ValueError` for unknown providers

**Acceptance Criteria:**
- Factory method returns correct config for each provider
- Missing API key raises clear error message
- Unknown provider raises `ValueError`

---

### 1-4: Modify LLMClient for provider support

**Requirements:**
- Add constructor parameters: `provider`, `track_cost`, `app_name`, `app_url`
- Use `ProviderConfig.from_provider()` to configure client
- Initialize `CostTracker` with appropriate enabled state
- `track_cost` defaults to `True` for openrouter, `False` for openai
- Add `extra_body={"usage": {"include": True}}` for OpenRouter requests
- `chat()` returns `tuple[dict, UsageStats]` and tracks costs
- Add `get_cost_summary()` method

**Acceptance Criteria:**
- OpenRouter requests include required headers
- Cost tracking is on by default for OpenRouter
- UsageStats populated correctly for both providers

---

### 1-5: Add CLI arguments

**Requirements:**
- Add `--provider` argument with choices `["openai", "openrouter"]`, default `"openai"`
- Add `--no-track-cost` flag to disable cost tracking
- Pass `provider` and `track_cost` to `run_pipeline()`

**Acceptance Criteria:**
- `--help` shows new arguments with descriptions
- Arguments parsed correctly and passed to pipeline

---

### 1-6: Integrate cost tracking in orchestrator

**Requirements:**
- Add `provider` and `track_cost` parameters to `run_pipeline()`
- Pass parameters to `LLMClient` constructor
- Return `CostSummary` as third element of return tuple

**Acceptance Criteria:**
- Pipeline returns cost summary
- Cost summary available to CLI for metadata output

---

### 1-7: Add unit tests

**Requirements:**
- Test `ProviderConfig.from_provider()` for both providers
- Test `ProviderConfig` raises for unknown provider
- Test `CostTracker` disabled mode skips API calls
- Test `CostTracker` accumulates costs
- Test `CostTracker` handles API errors gracefully
- Test `LLMClient` default `track_cost` per provider
- Test `LLMClient` adds `extra_body` for OpenRouter

**Acceptance Criteria:**
- All tests pass with mocked HTTP responses
- No real API calls in unit tests

---

### 1-8: Add integration tests

**Requirements:**
- Test real OpenRouter API call returns cost
- Test cost accumulates over multiple calls
- Test CLI JSON output includes cost
- Mark tests with `@pytest.mark.integration`
- Skip if `OPENROUTER_API_KEY` not set

**Acceptance Criteria:**
- Tests pass against real OpenRouter API
- Tests gracefully skip when API key unavailable

---

### 1-9: Add BDD feature tests

**Requirements:**
- Create `tests/features/openrouter.feature` with scenarios from tech design
- Scenarios: basic generation, cost tracking default, disable cost tracking, non-OpenAI model
- Implement step definitions

**Acceptance Criteria:**
- Feature file follows Gherkin syntax
- All scenarios pass

---

### 1-10: Extend metadata output with cost

**Requirements:**
- Add `cost: Optional[CostSummary]` field to `RunMetadata` dataclass (Feature 2)
- Add `cost` parameter to `create_metadata()` function
- Pass `cost_summary` to `create_metadata()` in CLI when provider is openrouter
- Update metadata version to `"1.1"` when cost field is present

**Acceptance Criteria:**
- Metadata JSON includes `cost` field when OpenRouter is used
- Cost field is `null`/absent when tracking disabled or provider is openai
- Schema version reflects cost capability
