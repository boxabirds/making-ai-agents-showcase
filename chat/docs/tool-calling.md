# Tool Calling Implementation Guide

This guide documents the implementation of tool calling (function calling) for the Gemini API in a document navigation system.

## Table of Contents
- [Overview](#overview)
- [Key Discoveries](#key-discoveries)
- [Architecture](#architecture)
- [Implementation Details](#implementation-details)
- [Testing Strategy](#testing-strategy)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Best Practices](#best-practices)

## Overview

Tool calling allows the LLM to trigger specific functions instead of generating text responses. In our document navigation system, this enables the AI to navigate to specific sections when users ask about them, rather than describing the content.

### Example Flow
1. User: "Tell me about how Agno handles tools"
2. LLM: Calls `navigate_to_section` with `section="Agno"`, `subsection="Tools"`
3. System: Navigates to the Tools subsection under Agno
4. UI: Shows the relevant content

## Key Discoveries

### 1. The "Instead" Keyword is Critical

The most important discovery: prompt phrasing dramatically affects tool calling success.

✅ **Works**: "jump to that section **instead** of responding with a message"  
❌ **Fails**: "use the navigation function to take them there"

The word "instead" signals to the model that it should take an action rather than provide a description.

### 2. Google API Version Requirements

- The `v1` endpoint doesn't support the `tools` and `responseMimeType` fields
- Must use `v1beta` endpoint for tool calling: `https://generativelanguage.googleapis.com/v1beta/...`
- This is a Google Gemini API versioning issue, not a Cloudflare limitation
- Cloudflare AI Gateway can proxy to v1beta if configured correctly

### 3. API Version Matters

- Tool calling requires the `v1beta` endpoint
- The `v1` endpoint doesn't support tools
- Always use: `/v1beta/models/{model}:generateContent`

## Architecture

### Navigation Protocol Design

```javascript
{
  name: "navigate_to_section",
  description: "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features)",
  parameters: {
    type: "object",
    properties: {
      section: {
        type: "string",
        description: "The main section name",
        enum: ["Agno", "Autogen", "Deployment Guide"]
      },
      subsection: {
        type: "string",
        description: "The subsection name within the main section (optional). Only provide if user asks about specific subsection content.",
        enum: ["Architecture", "Tools", "Performance", "Getting Started", "Advanced Features", "Examples"]
      }
    },
    required: ["section"]
  }
}
```

### Key Design Decisions

1. **Separate Section/Subsection Parameters**
   - Clear intent and hierarchy
   - Easier for LLM to understand
   - Simplifies client-side handling

2. **Natural Language Values**
   - Use "Agno" not "agno" or "section-agno"
   - Matches how users refer to sections
   - No complex ID mapping needed

3. **Enum Validation**
   - Prevents typos and invalid values
   - Guides LLM to valid choices
   - All subsections in one enum (relies on description for hierarchy)

## Implementation Details

### 1. Building Tool Definitions

```javascript
function buildToolDefinitions() {
    if (!window.documentParser || !window.documentParser.sections) {
        return [];
    }
    
    // Build structured hierarchy
    const sections = window.documentParser.sections.map(s => ({
        name: s.title,
        subsections: s.subsections.map(sub => sub.title)
    }));
    
    // Generate clear description listing all sections and their subsections
    const sectionDescriptions = sections.map(s => {
        if (s.subsections.length > 0) {
            return `${s.name} (subsections: ${s.subsections.join(', ')})`;
        }
        return s.name;
    }).join('; ');
    
    // Extract enums
    const sectionNames = sections.map(s => s.name);
    const allSubsections = sections.flatMap(s => s.subsections);
    const uniqueSubsections = [...new Set(allSubsections)];
    
    return [{
        function_declarations: [{
            name: "navigate_to_section",
            description: `When user asks about content related to these sections, navigate there instead of describing it. Available sections: ${sectionDescriptions}`,
            parameters: {
                type: "object",
                properties: {
                    section: {
                        type: "string",
                        description: "The main section name",
                        enum: sectionNames
                    },
                    subsection: {
                        type: "string",
                        description: "The subsection name within the main section (optional). Only provide if user asks about specific subsection content.",
                        enum: uniqueSubsections.length > 0 ? uniqueSubsections : undefined
                    }
                },
                required: ["section"]
            }
        }]
    }];
}
```

### 2. System Prompt Construction

```javascript
const systemPrompt = `You are a helpful AI assistant that helps users navigate and understand the report.

<report>
${documentContent}
</report>

<available-sections>
${sectionHierarchy}
</available-sections>

Remember: 
- Base your answers on the document content provided above
- Be helpful in navigating the document
- Keep responses concise and relevant
- When users ask about specific topics that are covered in the sections, jump to that section instead of responding with a message`;
```

### 3. Handling Tool Calls

```javascript
function handleToolCall(toolCall) {
    if (toolCall.tool === 'navigate_to_section') {
        const { section: sectionName, subsection: subsectionName } = toolCall;
        
        // Find matching section (case-insensitive)
        const sectionObj = window.documentParser.sections.find(
            s => s.title.toLowerCase() === sectionName.toLowerCase()
        );
        
        if (!sectionObj) {
            addMessage(`I couldn't find the section "${sectionName}".`, 'assistant');
            return;
        }
        
        if (subsectionName) {
            // Find matching subsection
            const subsectionObj = sectionObj.subsections.find(
                sub => sub.title.toLowerCase() === subsectionName.toLowerCase()
            );
            
            if (subsectionObj) {
                navigateToSection(sectionObj.id, subsectionObj.id);
                addArtifactToChat(`${sectionObj.title} > ${subsectionObj.title}`, 'subsection', subsectionObj.id);
            } else {
                // Fallback to main section
                navigateToSection(sectionObj.id);
                addMessage(`I couldn't find "${subsectionName}" in ${sectionName}, showing the main section.`, 'assistant');
            }
        } else {
            navigateToSection(sectionObj.id);
            addArtifactToChat(sectionObj.title, 'section', sectionObj.id);
        }
    }
}
```

### 4. Cloudflare Worker Configuration

```javascript
export default {
  async fetch(request, env) {
    const body = await request.json();
    
    // Direct API call (not through AI Gateway)
    const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/${body.model || 'gemini-2.0-flash'}:generateContent`;
    
    const response = await fetch(`${API_URL}?key=${env.GOOGLE_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: body.contents,
        generationConfig: body.generationConfig,
        tools: body.tools || []
      })
    });
    
    return response;
  }
}
```

## Testing Strategy

### Test Suite Overview

1. **test-1-basic.sh** - Basic tool calling with simple prompt
2. **test-2-complex-prompt.sh** - Tool calling with tone instructions
3. **test-3-hierarchy.sh** - Hierarchical navigation with enum validation
4. **test-4-cloudflare.sh** - Worker proxy functionality
5. **test-5-full-prompt.sh** - Production system prompt
6. **test-6-hierarchical-nav.sh** - Complete navigation protocol
7. **test-7-subsection-validation.sh** - Validates proper section/subsection pairing

### Running Tests

```bash
# Run all tests with detailed output
./run-all-tests.sh

# Run tests with compact output
./run-tests-compact.sh

# Run specific test with verbose curl output
./run-tests-verbose.sh test-6-hierarchical-nav.sh

# Validate request formats
./test-request-format.sh
```

### Key Test Insights

- All tests include request/response logging
- Tests validate both successful tool calls and proper parameter values
- Edge cases like invalid subsections are tested
- Worker proxy compatibility is verified

## Common Issues and Solutions

### Issue 1: No Function Call Detected

**Symptom**: LLM returns text instead of calling the function

**Solutions**:
1. Add "instead" to the prompt: "jump to that section instead of describing it"
2. Ensure tool definitions are properly formatted
3. Check that you're using the v1beta endpoint

### Issue 2: Invalid JSON Payload Errors

**Symptom**: "Unknown name 'tools': Cannot find field"

**Cause**: Using v1 endpoint instead of v1beta

**Solution**: Use v1beta API endpoint (either direct or through properly configured proxy)

### Issue 3: Wrong Section/Subsection Combinations

**Symptom**: LLM selects subsections that don't belong to the chosen section

**Solutions**:
1. Clear hierarchy in tool description
2. Enum constraints on both parameters
3. Client-side validation as fallback

### Issue 4: Case Sensitivity

**Symptom**: Navigation fails due to case mismatch

**Solution**: Implement case-insensitive matching in `handleToolCall()`

## Best Practices

### 1. Prompt Engineering

- Always use decisive language ("instead", "rather than")
- List available sections clearly in the tool description
- Keep system prompts focused on navigation

### 2. Tool Definition Structure

- Use descriptive function names (`navigate_to_section` not `nav`)
- Provide clear parameter descriptions
- Include examples in the description when helpful

### 3. Error Handling

- Validate tool calls before processing
- Provide fallback behavior (e.g., show main section if subsection not found)
- Give clear error messages to users

### 4. Testing

- Test each level of complexity separately
- Include edge cases in test suite
- Log requests and responses for debugging

### 5. Security

- Never expose API keys in client-side code
- Use server-side proxies (like Cloudflare Workers)
- Validate all inputs before processing

## Example Implementation Flow

1. **User Query**: "How does Agno handle performance?"

2. **LLM Processing**:
   - Identifies "Agno" as the section
   - Identifies "performance" relates to Performance subsection
   - Calls tool with `section="Agno"`, `subsection="Performance"`

3. **System Response**:
   - Validates section exists
   - Validates subsection exists under that section
   - Navigates to `agno` section with `performance` subsection
   - Shows visual indicator of navigation

4. **Fallback Handling**:
   - If subsection not found, shows main section
   - Provides informative message about fallback

## Conclusion

Successful tool calling implementation requires:
1. Proper prompt engineering (use "instead")
2. Clear tool definitions with appropriate constraints
3. Correct API endpoint (v1beta)
4. Comprehensive testing
5. Good error handling

The hierarchical navigation protocol with separate section/subsection parameters provides the best balance of clarity, validation, and flexibility for document navigation use cases.