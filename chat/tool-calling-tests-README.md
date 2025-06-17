# Gemini Tool Calling Test Suite

This directory contains incremental tests for debugging Gemini API tool calling functionality.

## Test Scripts

1. **test-1-basic.sh** - Basic tool calling test
   - Exact copy of working example
   - Simple prompt with "jump to that section instead"
   - Tests basic function call detection

2. **test-2-complex-prompt.sh** - Complex prompt with tone profile
   - Adds sophisticated tone instructions
   - Tests if additional prompt complexity affects tool detection

3. **test-3-hierarchy.sh** - Two-level section hierarchy
   - Tests navigation to both sections and subsections
   - More complex document structure

4. **test-4-cloudflare.sh** - Cloudflare Worker proxy test
   - Tests tool calling through the worker proxy
   - Verifies transparent proxying functionality

5. **test-5-full-prompt.sh** - Full production system prompt
   - Complete prompt matching the chat application
   - Includes tone profile and all navigation instructions

## Running the Tests

### Individual Tests
```bash
export GEMINI_API_KEY="your-api-key"
./test-1-basic.sh
```

### All Tests
```bash
export GEMINI_API_KEY="your-api-key"
./run-all-tests.sh
```

## Key Findings

The critical element for tool calling detection is the prompt phrasing:
- ✅ "jump to that section **instead**" - triggers tool calling
- ❌ "use the navigation function" - often ignored

The word "instead" appears to be crucial for Gemini to understand it should use a tool rather than provide a text response.

## Debugging Steps

1. Verify basic tool calling works (test-1)
2. Check if complexity affects detection (test-2)
3. Verify hierarchy handling (test-3)
4. Confirm proxy doesn't break functionality (test-4)
5. Test full production prompt (test-5)

## Common Issues

- **No function call detected**: Check prompt includes "instead" or similar decisive language
- **Invalid JSON error**: Verify tools array structure matches API expectations
- **503 errors**: Model overloaded, retry after a moment
- **Worker proxy issues**: Check API key is configured in worker environment