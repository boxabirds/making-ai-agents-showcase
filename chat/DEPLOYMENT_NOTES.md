# Deployment Notes for Tool Calling Fix

## Changes Made

### 1. Worker Update (matrix/backend/worker.js)
- Changed from using Cloudflare AI Gateway to direct Google AI API
- AI Gateway doesn't support the `tools` and `responseMimeType` fields
- Updated endpoint from:
  ```javascript
  https://gateway.ai.cloudflare.com/v1/${env.CF_ACCOUNT_ID}/${env.GATEWAY_ID}/google-ai-studio/v1beta/models/...
  ```
- To direct API:
  ```javascript
  https://generativelanguage.googleapis.com/v1beta/models/${body.model}:generateContent?key=${env.GOOGLE_API_KEY}
  ```

### 2. Chat Application Updates (chat/script.js)
- Updated system prompt to use "jump to that section instead" phrasing
- Updated tool description to be clearer about when to trigger navigation
- These changes ensure Gemini properly detects when to use the navigation tool

## Deployment Required

The worker at `https://tech-writer-ai-proxy.julian-harris.workers.dev` needs to be redeployed with the updated code.

To deploy:
```bash
cd matrix/backend
./deploy.sh
```

## Test Results

- ✅ Direct API calls work perfectly (tests 1-3)
- ❌ Worker proxy fails due to AI Gateway limitations (test 4)
- ✅ Complex prompts work with proper "instead" phrasing (test 5)

## Key Learning

The critical factor for tool calling is the prompt phrasing:
- ✅ "jump to that section **instead**" - triggers tool use
- ❌ "use the navigation function" - often ignored by the model

The word "instead" signals to the model that it should take an action rather than provide a description.