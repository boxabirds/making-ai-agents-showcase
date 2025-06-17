#!/bin/bash
set -e -E

echo "=== Testing Cloudflare AI Gateway API Version Support ==="
echo ""

# You'll need to set these environment variables
CF_ACCOUNT_ID="${CF_ACCOUNT_ID}"
GATEWAY_ID="${GATEWAY_ID}"
GOOGLE_API_KEY="${GOOGLE_API_KEY}"

# Test payload with tools
cat << EOF > test-request.json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "Hello, what is 2+2?"
        }
      ]
    }
  ],
  "generationConfig": {
    "responseMimeType": "text/plain",
    "temperature": 0.0,
    "maxOutputTokens": 100
  },
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "calculate",
          "description": "Performs basic math calculations",
          "parameters": {
            "type": "object",
            "properties": {
              "expression": {
                "type": "string"
              }
            }
          }
        }
      ]
    }
  ]
}
EOF

echo "Test 1: AI Gateway with v1 endpoint"
echo "===================================="
echo "URL: https://gateway.ai.cloudflare.com/v1/${CF_ACCOUNT_ID}/${GATEWAY_ID}/google-ai-studio/v1/models/gemini-2.0-flash:generateContent"
echo ""

curl -s -X POST \
  "https://gateway.ai.cloudflare.com/v1/${CF_ACCOUNT_ID}/${GATEWAY_ID}/google-ai-studio/v1/models/gemini-2.0-flash:generateContent" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: ${GOOGLE_API_KEY}" \
  -d @test-request.json | jq . || echo "Failed"

echo ""
echo ""

echo "Test 2: AI Gateway with v1beta endpoint"
echo "======================================="
echo "URL: https://gateway.ai.cloudflare.com/v1/${CF_ACCOUNT_ID}/${GATEWAY_ID}/google-ai-studio/v1beta/models/gemini-2.0-flash:generateContent"
echo ""

curl -s -X POST \
  "https://gateway.ai.cloudflare.com/v1/${CF_ACCOUNT_ID}/${GATEWAY_ID}/google-ai-studio/v1beta/models/gemini-2.0-flash:generateContent" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: ${GOOGLE_API_KEY}" \
  -d @test-request.json | jq . || echo "Failed"

echo ""
echo ""

echo "Test 3: Direct Google API v1beta (for comparison)"
echo "================================================="
echo "URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
echo ""

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GOOGLE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @test-request.json | jq .

echo ""
echo "Summary:"
echo "- If Test 1 fails with 'Unknown name tools', v1 doesn't support tools"
echo "- If Test 2 works, AI Gateway can proxy to v1beta"  
echo "- If Test 2 fails with 404, AI Gateway doesn't support v1beta proxying"
echo "- Test 3 should always work as it's direct to Google"