#!/bin/bash

# Minimal test of the bash tech writer API call

set -euo pipefail

MODEL="openai/gpt-4o-mini"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# Simple test message
messages='[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Say hello"}]'

# Make API call
response=$(curl -s -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d "{
        \"model\": \"gpt-4o-mini\",
        \"messages\": $messages,
        \"temperature\": 0
    }")

echo "Response:"
echo "$response" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
if 'choices' in data:
    print(data['choices'][0]['message']['content'])
else:
    print(json.dumps(data, indent=2))
"