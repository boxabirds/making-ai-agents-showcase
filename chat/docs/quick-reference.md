# Tool Calling Quick Reference

## Critical Success Factors

### 1. The Magic Word: "Instead"
```javascript
// ✅ WORKS
"jump to that section instead of responding with a message"

// ❌ FAILS
"use the navigation function"
```

### 2. Use v1beta Endpoint
```javascript
// ✅ CORRECT
https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent

// ❌ WRONG (no tool support)
https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent
```

### 3. Ensure Correct API Version in Proxy
```javascript
// ❌ FAILS - v1 endpoint doesn't support tools
https://gateway.ai.cloudflare.com/v1/{account}/google-ai-studio/v1/models/...

// ✅ WORKS - v1beta endpoint supports tools
https://gateway.ai.cloudflare.com/v1/{account}/google-ai-studio/v1beta/models/...
```

## Minimal Working Example

```javascript
// Tool Definition
const tools = [{
  function_declarations: [{
    name: "navigate_to_section",
    description: "When user asks about sections, jump there instead",
    parameters: {
      type: "object",
      properties: {
        section: { type: "string", enum: ["Agno", "Autogen"] },
        subsection: { type: "string" }
      },
      required: ["section"]
    }
  }]
}];

// System Prompt (key phrase!)
const prompt = "When users ask about sections, jump to that section instead of describing it";

// API Call
const response = await fetch(
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${KEY}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: messages,
      tools: tools,
      generationConfig: {
        temperature: 0.0,
        responseMimeType: "text/plain"
      }
    })
  }
);
```

## Response Handling

```javascript
// Parse function call from response
if (response.candidates[0].content.parts[0].functionCall) {
  const call = response.candidates[0].content.parts[0].functionCall;
  // call.name = "navigate_to_section"
  // call.args = { section: "Agno", subsection: "Tools" }
}
```

## Testing Checklist

- [ ] Using "instead" in prompts
- [ ] Using v1beta endpoint
- [ ] Tools array properly formatted
- [ ] Enum constraints on parameters
- [ ] Case-insensitive matching in handler
- [ ] Fallback behavior implemented
- [ ] Request/response logging enabled