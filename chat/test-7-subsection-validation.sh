#!/bin/bash
set -e -E

# Test 7: Subsection Validation - Ensure only valid subsections are chosen
echo "=== Test 7: Subsection Validation ==="
echo "Testing that LLM only selects valid subsections for each section"
echo ""

GEMINI_API_KEY="$GEMINI_API_KEY"
MODEL_ID="gemini-2.0-flash"
GENERATE_CONTENT_API="generateContent"

# Test Case 1: Valid subsection request
cat << EOF > request1.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead of describing it. \n\n== The report ==\n# Agno\nAgno is a powerful AI agent framework designed for scalable agent deployment.\n\n## Architecture\nAgno uses a modular plugin-based architecture that allows developers to extend functionality.\n\n## Tools\nAgno provides various tools for agent development including debugging, monitoring, and deployment utilities.\n\n## Performance\nAgno achieves high performance through efficient task scheduling and resource management.\n\n# Autogen\nAutogen is Microsoft's framework for building multi-agent conversational systems.\n\n## Getting Started\nAutogen makes it easy to create agent systems with simple configuration.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration patterns and tool use.\n\n## Examples\nVarious examples demonstrate Autogen's capabilities in different domains."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this report about agent frameworks. When users ask about specific topics, I'll use the navigation function to jump directly to the relevant section or subsection instead of describing the content."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "how do I get started with autogen?"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples)",
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
                  "enum": ["Architecture", "Tools", "Performance", "Getting Started", "Advanced Features", "Examples"]
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

echo "Test Case 1: Valid subsection request"
echo "====================================="
echo "Query: 'how do I get started with autogen?'"
echo "Expected: section='Autogen', subsection='Getting Started'"
echo ""
echo "Request being sent:"
echo "-------------------"
cat request1.json | jq .
echo ""

response1=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" \
-d '@request1.json')

echo "Response:"
echo "---------"
echo "$response1" | jq .

# Check for expected navigation
if echo "$response1" | grep -q '"section": "Autogen"' && echo "$response1" | grep -q '"subsection": "Getting Started"'; then
    echo ""
    echo "✅ Correctly selected valid subsection 'Getting Started' for section 'Autogen'"
else
    echo ""
    echo "❌ Failed to select correct section/subsection"
fi

echo ""
echo ""

# Test Case 2: Ambiguous subsection request that could match wrong section
cat << EOF > request2.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead of describing it. \n\n== The report ==\n# Agno\nAgno is a powerful AI agent framework designed for scalable agent deployment.\n\n## Architecture\nAgno uses a modular plugin-based architecture that allows developers to extend functionality.\n\n## Tools\nAgno provides various tools for agent development including debugging, monitoring, and deployment utilities.\n\n## Performance\nAgno achieves high performance through efficient task scheduling and resource management.\n\n# Autogen\nAutogen is Microsoft's framework for building multi-agent conversational systems.\n\n## Getting Started\nAutogen makes it easy to create agent systems with simple configuration.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration patterns and tool use.\n\n## Examples\nVarious examples demonstrate Autogen's capabilities in different domains."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this report about agent frameworks. When users ask about specific topics, I'll use the navigation function to jump directly to the relevant section or subsection instead of describing the content."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "show me examples of how autogen works"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples)",
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
                  "enum": ["Architecture", "Tools", "Performance", "Getting Started", "Advanced Features", "Examples"]
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

echo "Test Case 2: Request for examples (should pick Autogen > Examples)"
echo "================================================================="
echo "Query: 'show me examples of how autogen works'"
echo "Expected: section='Autogen', subsection='Examples'"
echo ""
echo "Request being sent:"
echo "-------------------"
cat request2.json | jq .
echo ""

response2=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" \
-d '@request2.json')

echo "Response:"
echo "---------"
echo "$response2" | jq .

# Check for expected navigation
if echo "$response2" | grep -q '"section": "Autogen"' && echo "$response2" | grep -q '"subsection": "Examples"'; then
    echo ""
    echo "✅ Correctly selected 'Examples' subsection under 'Autogen'"
else
    echo ""
    echo "❌ Failed to select correct section/subsection combination"
fi

echo ""
echo ""

# Test Case 3: Test that doesn't match invalid combinations (e.g., won't select Agno > Getting Started)
cat << EOF > request3.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead of describing it. \n\n== The report ==\n# Agno\nAgno is a powerful AI agent framework designed for scalable agent deployment.\n\n## Architecture\nAgno uses a modular plugin-based architecture that allows developers to extend functionality.\n\n## Tools\nAgno provides various tools for agent development including debugging, monitoring, and deployment utilities.\n\n## Performance\nAgno achieves high performance through efficient task scheduling and resource management.\n\n# Autogen\nAutogen is Microsoft's framework for building multi-agent conversational systems.\n\n## Getting Started\nAutogen makes it easy to create agent systems with simple configuration.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration patterns and tool use.\n\n## Examples\nVarious examples demonstrate Autogen's capabilities in different domains."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this report about agent frameworks. When users ask about specific topics, I'll use the navigation function to jump directly to the relevant section or subsection instead of describing the content."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "explain agno's performance characteristics"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples)",
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
                  "enum": ["Architecture", "Tools", "Performance", "Getting Started", "Advanced Features", "Examples"]
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

echo "Test Case 3: Agno performance request"
echo "====================================="
echo "Query: 'explain agno's performance characteristics'"
echo "Expected: section='Agno', subsection='Performance'"
echo "Should NOT select 'Getting Started' or other Autogen subsections"
echo ""
echo "Request being sent:"
echo "-------------------"
cat request3.json | jq .
echo ""

response3=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" \
-d '@request3.json')

echo "Response:"
echo "---------"
echo "$response3" | jq .

# Check for expected navigation
if echo "$response3" | grep -q '"section": "Agno"' && echo "$response3" | grep -q '"subsection": "Performance"'; then
    echo ""
    echo "✅ Correctly selected 'Performance' under 'Agno' (not a subsection from another section)"
    
    # Extra check - make sure it didn't select an invalid combination
    if echo "$response3" | grep -q '"subsection": "Getting Started"' || echo "$response3" | grep -q '"subsection": "Examples"'; then
        echo "❌ WARNING: Selected a subsection that doesn't belong to Agno!"
    fi
else
    echo ""
    echo "❌ Failed to select correct section/subsection combination"
fi

echo ""
echo ""
echo "Summary:"
echo "========"
echo "This test validates that:"
echo "1. The LLM correctly matches subsections to their parent sections"
echo "2. The enum constraint helps prevent invalid section/subsection combinations"
echo "3. The description in the tool definition guides proper hierarchy understanding"