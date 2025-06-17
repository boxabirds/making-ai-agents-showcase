#!/bin/bash
set -e -E

# Test 3: Two-level section hierarchy
echo "=== Test 3: Two-Level Section Hierarchy ==="
echo "Testing navigation to both sections and subsections"
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
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead. A section_id is denoted by starting with a # (hash) for main sections or ## for subsections.\n\n== The report ==\n# Agno\nAgno is a powerful agent framework.\n\n## Architecture\nAgno uses a modular architecture with plugins.\n\n## Performance\nAgno achieves high performance through efficient task scheduling.\n\n# Autogen\nAutogen is a multi-agent conversation framework.\n\n## Getting Started\nAutogen makes it easy to build agent systems.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate this report about Agno and Autogen frameworks. The report has main sections (#Agno, #Autogen) and subsections like ##Architecture, ##Performance under Agno, and ##Getting Started, ##Advanced Features under Autogen. When users ask about specific topics, I'll use the jump_to_section function to navigate directly to the relevant section or subsection."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "tell me about agno's architecture"
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
            "description": "User mentions a section or subsection so we return a request to jump to that section id. Main sections use single hash (#) and subsections use double hash (##)",
            "parameters": {
              "type": "object",
              "properties": {
                "section_id": {
                  "type": "string",
                  "description": "The section ID to navigate to (e.g., 'agno' for #Agno or 'architecture' for ##Architecture)"
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
echo "Expected: Function call to jump_to_section with section_id 'architecture'"

# Check if response contains a function call
if echo "$response" | grep -q "functionCall"; then
    echo "✅ Function call detected"
    exit 0
else
    echo "❌ No function call detected - got text response instead"
    exit 1
fi