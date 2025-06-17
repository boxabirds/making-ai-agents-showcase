#!/bin/bash
set -e -E

GEMINI_API_KEY="$GEMINI_API_KEY"
MODEL_ID="gemini-2.0-flash"
GENERATE_CONTENT_API="streamGenerateContent"

cat << EOF > request.json
{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "You are a helpful tech writer report agent. You help people understanding aspects of the report provided below. This report is provided to the user separately so if they refer to a section specifically, then we should jump to that section instead. A section_id is denoted by starting with a # (hash). \n\n== The report ==\n# Agno\nAgno is great. \n\n# Autogen\nAutogen is great as well. \n"
          },
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "text": "Okay, I understand. I'm ready to help users understand the report. I will pay close attention to any section IDs they mention (e.g., #Agno, #Autogen) and use the `jump_to_section` function to direct them to the relevant part of the report. I will also answer general questions about the content to the best of my ability.\n"
          },
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "text": "tell me about agno then"
          },
        ]
      },
      {
        "role": "model",
        "parts": [
          {
            "function_call": {
              "name": "jump_to_section",
              "args": {"section_id":"Agno"}
            }
          },
        ]
      },
      {
        "role": "user",
        "parts": [
          {
            "function_response": {
              "name": "jump_to_section",
              "response": {
                "output": ""
              }
            }
          },
          {
            "text": "INSERT_INPUT_HERE"
          },
        ]
      },
    ],
    "generationConfig": {
      "responseMimeType": "text/plain",
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
              }
            }
          },
        ]
      },
    ],
}
EOF

curl \
-X POST \
-H "Content-Type: application/json" \
"https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${GEMINI_API_KEY}" -d '@request.json'
