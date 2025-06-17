#!/bin/bash
set -e -E

# Test 4: Through Cloudflare Worker Proxy
echo "=== Test 4: Cloudflare Worker Proxy ==="
echo "Testing tool calling through the worker proxy"
echo ""

# Note: This requires the worker URL to be running
WORKER_URL="https://tech-writer-ai-proxy.julian-harris.workers.dev"
MODEL_ID="gemini-2.0-flash"

cat << EOF > request.json
{
    "model": "gemini-2.0-flash",
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead. A section_id is denoted by starting with a # (hash). \n\n== The report ==\n# Agno\nAgno is great. \n\n# Autogen\nAutogen is great as well."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users understand the report. I will pay close attention to any section IDs they mention (e.g., #Agno, #Autogen) and use the jump_to_section function to direct them to the relevant part of the report."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "tell me about autogen"
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
            "name": "jump_to_section",
            "description": "User mentions a section so we return a request to jump to that section id",
            "parameters": {
              "type": "object",
              "properties": {
                "section_id": {
                  "type": "string"
                }
              },
              "required": ["section_id"]
            }
          }
        ]
      }
    ]
}
EOF

echo "Request being sent to worker:"
echo "============================"
echo "URL: ${WORKER_URL}"
echo ""
cat request.json | jq .
echo ""

echo "Response:"
echo "========="
response=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"${WORKER_URL}" \
-d '@request.json')

echo "$response" | jq .

echo ""
echo "Expected: Function call to jump_to_section with section_id 'Autogen'"

# Check if response contains a function call or an error
if echo "$response" | grep -q "functionCall"; then
    echo "✅ Function call detected"
    exit 0
elif echo "$response" | grep -q "error"; then
    echo "❌ Error from worker - tool calling failed"
    echo ""
    echo "Note: Worker configuration issues:"
    echo "1. The worker might be using wrong endpoint format"
    echo "2. Cloudflare AI Gateway may not support tools"
    echo "3. Consider bypassing AI Gateway for tool support"
    exit 1
else
    echo "❌ No function call detected - got text response instead"
    exit 1
fi