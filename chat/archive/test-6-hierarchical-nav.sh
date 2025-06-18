#!/bin/bash
set -e -E

# Test 6: Hierarchical Navigation with Section/Subsection
echo "=== Test 6: Hierarchical Navigation Protocol ==="
echo "Testing new section/subsection navigation structure"
echo ""

GEMINI_API_KEY="$GEMINI_API_KEY"
MODEL_ID="gemini-2.0-flash"
GENERATE_CONTENT_API="generateContent"

# Test document with rich hierarchy
cat << EOF > request.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead of describing it. \n\n== The report ==\n# Agno\nAgno is a powerful AI agent framework designed for scalable agent deployment.\n\n## Architecture\nAgno uses a modular plugin-based architecture that allows developers to extend functionality.\n\n## Tools\nAgno provides various tools for agent development including debugging, monitoring, and deployment utilities.\n\n## Performance\nAgno achieves high performance through efficient task scheduling and resource management.\n\n# Autogen\nAutogen is Microsoft's framework for building multi-agent conversational systems.\n\n## Getting Started\nAutogen makes it easy to create agent systems with simple configuration.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration patterns and tool use.\n\n## Examples\nVarious examples demonstrate Autogen's capabilities in different domains.\n\n# Deployment Guide\nInstructions for deploying agent systems in production.\n\n## Cloud Deployment\nDeploy agents to various cloud providers.\n\n## Security\nBest practices for securing agent deployments."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this comprehensive report about agent frameworks. When users ask about specific topics, I'll use the navigation function to jump directly to the relevant section or subsection instead of describing the content."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "tell me about how agno handles tools"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples); Deployment Guide (subsections: Cloud Deployment, Security)",
            "parameters": {
              "type": "object",
              "properties": {
                "section": {
                  "type": "string",
                  "description": "The main section name",
                  "enum": ["Agno", "Autogen", "Deployment Guide"]
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

echo "Test Case 1: Navigate to subsection (Agno > Tools)"
echo "=================================================="
echo "Query: 'tell me about how agno handles tools'"
echo ""
echo "Request being sent:"
echo "-------------------"
cat request.json | jq .
echo ""

response=$(curl -s \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" \
-d '@request.json')

echo "Response:"
echo "---------"
echo "$response" | jq .

# Check for expected navigation
if echo "$response" | grep -q '"section": "Agno"' && echo "$response" | grep -q '"subsection": "Tools"'; then
    echo ""
    echo "✅ Correctly identified section='Agno' and subsection='Tools'"
else
    echo ""
    echo "❌ Failed to identify correct section/subsection"
fi

echo ""
echo ""

# Test Case 2: Navigate to main section only
cat << EOF > request2.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead of describing it. \n\n== The report ==\n# Agno\nAgno is a powerful AI agent framework designed for scalable agent deployment.\n\n## Architecture\nAgno uses a modular plugin-based architecture that allows developers to extend functionality.\n\n## Tools\nAgno provides various tools for agent development including debugging, monitoring, and deployment utilities.\n\n## Performance\nAgno achieves high performance through efficient task scheduling and resource management.\n\n# Autogen\nAutogen is Microsoft's framework for building multi-agent conversational systems.\n\n## Getting Started\nAutogen makes it easy to create agent systems with simple configuration.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration patterns and tool use.\n\n## Examples\nVarious examples demonstrate Autogen's capabilities in different domains.\n\n# Deployment Guide\nInstructions for deploying agent systems in production.\n\n## Cloud Deployment\nDeploy agents to various cloud providers.\n\n## Security\nBest practices for securing agent deployments."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this comprehensive report about agent frameworks. When users ask about specific topics, I'll use the navigation function to jump directly to the relevant section or subsection instead of describing the content."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "what is autogen?"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples); Deployment Guide (subsections: Cloud Deployment, Security)",
            "parameters": {
              "type": "object",
              "properties": {
                "section": {
                  "type": "string",
                  "description": "The main section name",
                  "enum": ["Agno", "Autogen", "Deployment Guide"]
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

echo "Test Case 2: Navigate to main section only (Autogen)"
echo "==================================================="
echo "Query: 'what is autogen?'"
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
if echo "$response2" | grep -q '"section": "Autogen"'; then
    # Check that subsection is either null or not present
    if echo "$response2" | grep -q '"subsection": null' || ! echo "$response2" | grep -q '"subsection"'; then
        echo ""
        echo "✅ Correctly identified section='Autogen' without subsection"
    else
        echo ""
        echo "⚠️  Identified section='Autogen' but included unexpected subsection"
    fi
else
    echo ""
    echo "❌ Failed to identify correct section"
fi

echo ""
echo ""

# Test Case 3: Complex query about deployment security
cat << EOF > request3.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead of describing it. \n\n== The report ==\n# Agno\nAgno is a powerful AI agent framework designed for scalable agent deployment.\n\n## Architecture\nAgno uses a modular plugin-based architecture that allows developers to extend functionality.\n\n## Tools\nAgno provides various tools for agent development including debugging, monitoring, and deployment utilities.\n\n## Performance\nAgno achieves high performance through efficient task scheduling and resource management.\n\n# Autogen\nAutogen is Microsoft's framework for building multi-agent conversational systems.\n\n## Getting Started\nAutogen makes it easy to create agent systems with simple configuration.\n\n## Advanced Features\nAutogen supports complex multi-agent orchestration patterns and tool use.\n\n## Examples\nVarious examples demonstrate Autogen's capabilities in different domains.\n\n# Deployment Guide\nInstructions for deploying agent systems in production.\n\n## Cloud Deployment\nDeploy agents to various cloud providers.\n\n## Security\nBest practices for securing agent deployments."
          }
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "I understand. I'm ready to help users navigate and understand this comprehensive report about agent frameworks. When users ask about specific topics, I'll use the navigation function to jump directly to the relevant section or subsection instead of describing the content."
          }
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "how do I secure my agent deployment?"
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
            "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples); Deployment Guide (subsections: Cloud Deployment, Security)",
            "parameters": {
              "type": "object",
              "properties": {
                "section": {
                  "type": "string",
                  "description": "The main section name",
                  "enum": ["Agno", "Autogen", "Deployment Guide"]
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

echo "Test Case 3: Navigate to deployment security"
echo "==========================================="
echo "Query: 'how do I secure my agent deployment?'"
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
if echo "$response3" | grep -q '"section": "Deployment Guide"' && echo "$response3" | grep -q '"subsection": "Security"'; then
    echo ""
    echo "✅ Correctly identified section='Deployment Guide' and subsection='Security'"
else
    echo ""
    echo "❌ Failed to identify correct section/subsection for security query"
fi

echo ""
echo "Summary:"
echo "========"
echo "This test validates the new hierarchical navigation protocol where:"
echo "1. Section and subsection are separate parameters"
echo "2. The LLM can identify when to navigate to just a section vs a specific subsection"
echo "3. Complex queries map correctly to the appropriate section/subsection"