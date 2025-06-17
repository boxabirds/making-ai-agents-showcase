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

6. **test-6-hierarchical-nav.sh** - New hierarchical navigation protocol
   - Tests separate section/subsection parameters
   - Validates complex queries like "how agno handles tools"
   - Ensures proper fallback behavior

7. **test-7-subsection-validation.sh** - Subsection enum validation
   - Tests that only valid subsections are chosen for each section
   - Validates enum constraints prevent invalid combinations
   - Ensures LLM respects section/subsection hierarchy

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

## Navigation Protocol Update

The navigation system has been redesigned to better handle hierarchical document structures:

### Old Design
- Single `sectionId` parameter forced LLM to guess section vs subsection
- Complex ID mapping between slugified IDs and display names
- Unclear hierarchy in tool descriptions

### New Design
- **Separate parameters**: `section` (required) and `subsection` (optional)
- **Natural language**: Uses actual titles instead of IDs
- **Enum validation**: Both sections AND subsections use enum constraints
- **Clear hierarchy**: Tool description shows "Section (subsections: A, B, C)"
- **Prevents invalid combinations**: While subsection enum includes all possible subsections, the description guides proper matching

### Example

Query: "tell me about how agno handles tools"

Response:
```json
{
  "functionCall": {
    "name": "navigate_to_section",
    "args": {
      "section": "Agno",
      "subsection": "Tools"
    }
  }
}
```

This design significantly improves the LLM's ability to correctly navigate complex documents.

### Implementation Note

The subsection enum includes ALL subsections from ALL sections (e.g., ["Architecture", "Tools", "Performance", "Getting Started", "Advanced Features", "Examples"]). While this theoretically allows invalid combinations like section="Agno" with subsection="Getting Started", in practice:

1. The tool description clearly states the hierarchy: "Agno (subsections: Architecture, Tools, Performance)"
2. The LLM respects this hierarchy when making selections
3. The client-side validation in `handleToolCall()` provides an additional safety net

Test-7 validates that this approach works correctly in practice.