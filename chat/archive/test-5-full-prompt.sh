#!/bin/bash
set -e -E

# Test 5: Full system prompt from production
echo "=== Test 5: Full Production System Prompt ==="
echo "Testing with complete prompt including tone profile and multiple sections"
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
            "text": "You are a helpful AI assistant that helps users navigate and understand the report.\n    You respond in a tone of voice profile as defined below. Your answers should be accurate, concise, and helpful.\n\n<report>\n# Introduction\n\nWelcome to this interactive document viewer. This system allows you to chat with any markdown document.\n\n## Getting Started\n\nTo begin, you can click on any section in the sidebar or use the quick action buttons below.\n\n## Features\n\nThe document chat interface provides several key features:\n- Natural language questions about the content\n- Quick navigation between sections\n- Intelligent section recommendations\n\n# Usage Guide\n\nThis section covers how to use the document chat interface effectively.\n\n## Navigation\n\nYou can navigate through the document in several ways:\n- Click sections in the sidebar\n- Use quick action buttons\n- Ask to go to specific sections\n\n## Asking Questions\n\nFeel free to ask any questions about the document content. The AI will help you understand and find information.\n</report>\n\n<available-sections>\n- Introduction (id: introduction)\n  Subsections:\n    - Getting Started (id: getting-started)\n    - Features (id: features)\n- Usage Guide (id: usage-guide)\n  Subsections:\n    - Navigation (id: navigation)\n    - Asking Questions (id: asking-questions)\n</available-sections>\n\n<tone-profile>\nTONE OF VOICE PROFILE\n\nSkeptical Optimism (Core Dimension):\nDescription: A foundational tone that approaches claims with healthy skepticism but maintains an underlying optimism about the potential of Vibe Coding and AI agents.\n\nUpbeat & Engaging:\nDescription: The overall energy should be positive, enthusiastic, and engaging.\n\nTruthful & Accurate (Evidence-Based):\nDescription: All information must be grounded in verifiable facts and evidence.\n</tone-profile>\n\nRemember: \n- Base your answers on the document content provided above\n- Be helpful in navigating the document\n- Keep responses concise and relevant\n- When users ask about specific topics that are covered in the sections, jump to that section instead of responding with a message"
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help you navigate and understand this document. I can answer questions about its content and help you find specific sections. I'll maintain an upbeat yet analytically grounded approach, ensuring accuracy while keeping things engaging."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "how do I get started?"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Introduction (subsections: Getting Started, Features); Usage Guide (subsections: Navigation, Asking Questions)",
            "parameters": {
              "type": "object",
              "properties": {
                "section": {
                  "type": "string",
                  "description": "The main section name",
                  "enum": ["Introduction", "Usage Guide"]
                },
                "subsection": {
                  "type": "string",
                  "description": "The subsection name within the main section (optional). Only provide if user asks about specific subsection content."
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
echo "Expected: Function call to navigate_to_section with section='Introduction' and subsection='Getting Started'"

# Check if response contains a function call with correct parameters
if echo "$response" | grep -q "functionCall"; then
    if echo "$response" | grep -q '"section": "Introduction"' && echo "$response" | grep -q '"subsection": "Getting Started"'; then
        echo "✅ Function call detected with correct section and subsection"
        exit 0
    else
        echo "⚠️  Function call detected but with unexpected parameters"
        echo "Check if section='Introduction' and subsection='Getting Started'"
        exit 1
    fi
else
    echo "❌ No function call detected - got text response instead"
    exit 1
fi