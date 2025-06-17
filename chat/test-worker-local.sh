#!/bin/bash
set -e -E

# Test Worker with Tool Calling (Local Version)
echo "=== Test Worker with Tool Calling ==="
echo "This tests the worker.js changes locally"
echo ""

# Note: This simulates what the worker would do
GOOGLE_API_KEY="$GEMINI_API_KEY"
MODEL_ID="gemini-2.0-flash"

cat << EOF > request.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful assistant. If the user asks about colors, use the get_color function instead of describing them. Available colors: red, blue, green."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. When users ask about colors, I'll use the get_color function to retrieve the information instead of describing them directly."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "tell me about the color red"
          }
        ]
      }
    ],
    "generationConfig": {
      "responseMimeType": "text/plain",
      "temperature": 0.0,
      "maxOutputTokens": 1024
    },
    "tools": [
      {
        "functionDeclarations": [
          {
            "name": "get_color",
            "description": "Get information about a color",
            "parameters": {
              "type": "object",
              "properties": {
                "color": {
                  "type": "string",
                  "description": "The color to get information about"
                }
              },
              "required": ["color"]
            }
          }
        ]
      }
    ]
}
EOF

echo "Testing Direct API (what worker will use):"
echo "=========================================="
response=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent?key=${GOOGLE_API_KEY}" \
-d '@request.json')

echo "$response" | jq .

# Check if response contains a function call
if echo "$response" | grep -q "functionCall"; then
    echo ""
    echo "✅ Direct API supports tool calling"
    exit 0
else
    echo ""
    echo "❌ Direct API did not return function call"
    exit 1
fi