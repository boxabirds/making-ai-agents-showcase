#!/bin/bash

echo "=== Testing Live Chat Integration with New Navigation Protocol ==="
echo

# Test 1: Direct navigation to a main section
echo "Test 1: Navigate to main section"
echo "Prompt: 'Tell me about building agents'"
echo

curl -s https://tech-writer-ai-proxy.julian-harris.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.0-flash",
    "contents": [
      {
        "role": "user",
        "parts": [{"text": "You are helping navigate a document. When asked about content, jump to that section instead of describing it. Available sections: Getting Started with AI Agents (subsections: What are AI Agents?, Key Components); Building Your First Agent (subsections: Setting Up the Environment, Creating the Agent)"}]
      },
      {
        "role": "model",
        "parts": [{"text": "I understand. I will help you navigate the document by jumping to relevant sections."}]
      },
      {
        "role": "user",
        "parts": [{"text": "Tell me about building agents"}]
      }
    ],
    "tools": [{
      "function_declarations": [{
        "name": "navigate_to_section",
        "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Getting Started with AI Agents (subsections: What are AI Agents?, Key Components); Building Your First Agent (subsections: Setting Up the Environment, Creating the Agent)",
        "parameters": {
          "type": "object",
          "properties": {
            "section": {
              "type": "string",
              "description": "The main section name",
              "enum": ["Getting Started with AI Agents", "Building Your First Agent"]
            },
            "subsection": {
              "type": "string",
              "description": "The subsection name within the main section (optional). Only provide if user asks about specific subsection content.",
              "enum": ["What are AI Agents?", "Key Components", "Setting Up the Environment", "Creating the Agent"]
            }
          },
          "required": ["section"]
        }
      }]
    }]
  }' | jq '.'

echo
echo "---"
echo

# Test 2: Navigate to specific subsection
echo "Test 2: Navigate to specific subsection"
echo "Prompt: 'How do I set up the environment?'"
echo

curl -s https://tech-writer-ai-proxy.julian-harris.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.0-flash",
    "contents": [
      {
        "role": "user",
        "parts": [{"text": "You are helping navigate a document. When asked about content, jump to that section instead of describing it. Available sections: Getting Started with AI Agents (subsections: What are AI Agents?, Key Components); Building Your First Agent (subsections: Setting Up the Environment, Creating the Agent)"}]
      },
      {
        "role": "model",
        "parts": [{"text": "I understand. I will help you navigate the document by jumping to relevant sections."}]
      },
      {
        "role": "user",
        "parts": [{"text": "How do I set up the environment?"}]
      }
    ],
    "tools": [{
      "function_declarations": [{
        "name": "navigate_to_section",
        "description": "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Getting Started with AI Agents (subsections: What are AI Agents?, Key Components); Building Your First Agent (subsections: Setting Up the Environment, Creating the Agent)",
        "parameters": {
          "type": "object",
          "properties": {
            "section": {
              "type": "string",
              "description": "The main section name",
              "enum": ["Getting Started with AI Agents", "Building Your First Agent"]
            },
            "subsection": {
              "type": "string",
              "description": "The subsection name within the main section (optional). Only provide if user asks about specific subsection content.",
              "enum": ["What are AI Agents?", "Key Components", "Setting Up the Environment", "Creating the Agent"]
            }
          },
          "required": ["section"]
        }
      }]
    }]
  }' | jq '.'

echo
echo "=== Integration Test Complete ==="