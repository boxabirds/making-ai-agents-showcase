#!/bin/bash
set -e -E

# Test 3: Two-level section hierarchy with enum validation
echo "=== Test 3: Two-Level Section Hierarchy with Enum Validation ==="
echo "Testing navigation with enum constraints on both sections and subsections"
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
            "name": "navigate_to_section",
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Performance); Autogen (subsections: Getting Started, Advanced Features)",
            "parameters": {
              "type": "object",
              "properties": {
                "section": {
                  "type": "string",
                  "description": "The main section name",
                  "enum": ["Agno", "Autogen"]
                },
                "subsection": {
                  "type": "string",
                  "description": "The subsection name within the main section (optional). Only provide if user asks about specific subsection content. Must be a valid subsection under the chosen section.",
                  "enum": ["Architecture", "Performance", "Getting Started", "Advanced Features"]
                }
              },
              "required": ["section"]
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
echo "Expected: Function call to navigate_to_section with section='Agno' and subsection='Architecture'"

# Check if response contains a function call with correct parameters
if echo "$response" | grep -q "functionCall"; then
    if echo "$response" | grep -q '"section": "Agno"' && echo "$response" | grep -q '"subsection": "Architecture"'; then
        echo "✅ Function call detected with correct section='Agno' and subsection='Architecture'"
        echo "✅ Enum validation ensures only valid combinations are possible"
        exit 0
    else
        echo "⚠️  Function call detected but with unexpected parameters"
        exit 1
    fi
else
    echo "❌ No function call detected - got text response instead"
    exit 1
fi