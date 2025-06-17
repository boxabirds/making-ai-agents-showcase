#!/bin/bash
set -e -E

# Test 1: Basic tool calling - exact copy of working example
echo "=== Test 1: Basic Tool Calling ==="
echo "Testing simple function call with minimal prompt"
echo ""

GEMINI_API_KEY="$GEMINI_API_KEY"
MODEL_ID="gemini-2.0-flash"
GENERATE_CONTENT_API="generateContent"

cat << EOF > request.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead. A section_id is denoted by starting with a # (hash). \n\n== The report ==\n# Agno\nAgno is great. \n\n# Autogen\nAutogen is great as well. \n"
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "Okay, I understand. I'm ready to help users understand the report. I will pay close attention to any section IDs they mention (e.g., #Agno, #Autogen) and use the \`jump_to_section\` function to direct them to the relevant part of the report. I will also answer general questions about the content to the best of my ability.\n"
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "tell me about agno then"
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

echo "Request being sent:"
echo "=================="
echo "URL: https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=***"
echo ""
cat request.json | jq .
echo ""

echo "Response:"
echo "========="
response=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" \
-d '@request.json')

echo "$response" | jq .

echo ""
echo "Expected: Function call to jump_to_section with section_id 'Agno'"

# Save response for validation
response=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" \
-d '@request.json')

# Check if response contains a function call
if echo "$response" | grep -q "functionCall"; then
    echo "✅ Function call detected"
    exit 0
else
    echo "❌ No function call detected - got text response instead"
    exit 1
fi