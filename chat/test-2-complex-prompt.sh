#!/bin/bash
set -e -E

# Test 2: Complex prompt with tone profile
echo "=== Test 2: Complex Prompt with Tone Profile ==="
echo "Testing function call detection with sophisticated system prompt"
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
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead. A section_id is denoted by starting with a # (hash). \n\n== The report ==\n# Agno\nAgno is great. \n\n# Autogen\nAutogen is great as well. \n\n== Tone Profile ==\nRespond with skeptical optimism - question hype while looking for genuine value. Be upbeat and engaging, using active voice. Be truthful and evidence-based. Incorporate occasional subtle wit to add personality. Be analytical and discerning, comparing and contrasting information critically."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this report about Agno and Autogen. I'll maintain a skeptically optimistic tone - questioning marketing hype while recognizing genuine innovation. When users mention specific sections (like #Agno or #Autogen), I'll use the jump_to_section function to navigate there directly. I'll keep my responses engaging and evidence-based, with occasional wit where appropriate."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "what does the report say about agno?"
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

# Check if response contains a function call
if echo "$response" | grep -q "functionCall"; then
    echo "✅ Function call detected"
    exit 0
else
    echo "❌ No function call detected - got text response instead"
    exit 1
fi