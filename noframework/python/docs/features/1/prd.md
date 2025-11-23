# Feature 1: OpenRouter Integration

## Problem Statement

Currently, tech_writer only supports OpenAI as an LLM provider. This limits users to:
- A single vendor's models
- OpenAI's pricing structure
- No visibility into per-report costs

Users need flexibility to:
1. Choose from multiple LLM providers (OpenAI, Anthropic, Google, Meta, etc.)
2. Track actual costs of generating documentation
3. Compare cost/quality tradeoffs across models

## User Stories

### US-1.1: Multi-Provider Access
As a developer, I want to use models from different providers (Claude, Gemini, Llama) so that I can choose the best model for my documentation needs.

### US-1.2: Cost Visibility
As a team lead, I want to see the cost of each documentation run so that I can budget and optimize LLM spending.

### US-1.3: Cost Reporting
As a CI/CD pipeline operator, I want cost data in the JSON output so that I can aggregate costs across runs and report to stakeholders.

## Proposed Solution

Integrate OpenRouter as an LLM API gateway:

1. **Single API, Multiple Providers**: OpenRouter provides a unified API to 200+ models from all major providers
2. **Built-in Cost Tracking**: OpenRouter returns actual cost per request, eliminating manual calculation
3. **OpenAI-Compatible**: Uses the same API format, minimizing code changes
4. **Transparent Pricing**: 5% markup over provider costs with full visibility

## Success Criteria

- [ ] Users can specify `--provider openrouter` to use OpenRouter
- [ ] Users can specify any OpenRouter model (e.g., `anthropic/claude-sonnet-4`)
- [ ] Cost tracking is enabled by default for OpenRouter
- [ ] JSON output includes total cost in USD
- [ ] Cost is logged during execution for real-time visibility

## Out of Scope

- Automatic model selection/routing (use OpenRouter's auto-router manually if desired)
- Cost budgets/limits (future feature)
- Provider-specific features (reasoning tokens, etc.)

## Dependencies

- OpenRouter API key (user-provided)
- Network access to `https://openrouter.ai/api/v1`

## Risks

| Risk | Mitigation |
|------|------------|
| OpenRouter API changes | Use stable v1 API, monitor changelog |
| Cost tracking latency | Document ~200ms overhead in docs |
| API key security | Use environment variables, never log keys |
