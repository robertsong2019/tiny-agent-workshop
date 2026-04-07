#!/usr/bin/env bash
#
# Tool Caller Agent — Function Calling via pure Bash + curl
# Demonstrates structured tool definitions and result parsing.
#
# Usage: OPENAI_API_KEY=xxx OPENAI_BASE_URL=xxx bash tool_caller.sh "What's 15 * 23?"

set -euo pipefail

API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY}"
BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
MODEL="${MODEL:-gpt-4o-mini}"
QUERY="${*:-What is the square root of 144 plus 28?}"

# Define tools in OpenAI function-calling format
TOOLS_JSON='[
  {
    "type": "function",
    "function": {
      "name": "calculate",
      "description": "Evaluate a math expression safely",
      "parameters": {
        "type": "object",
        "properties": {
          "expression": {"type": "string", "description": "Math expression to evaluate"}
        },
        "required": ["expression"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get mock weather for a city",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {"type": "string", "description": "City name"}
        },
        "required": ["city"]
      }
    }
  }
]'

call_api() {
  local messages="$1"
  local use_tools="${2:-false}"
  
  local payload
  if [ "$use_tools" = true ]; then
    payload=$(jq -n --arg model "$MODEL" --argjson messages "$messages" --argjson tools "$TOOLS_JSON" \
      '{model: $model, messages: $messages, tools: $tools, tool_choice: "auto"}')
  else
    payload=$(jq -n --arg model "$MODEL" --argjson messages "$messages" \
      '{model: $model, messages: $messages}')
  fi
  
  curl -s "$BASE_URL/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload"
}

echo "🔍 Query: $QUERY"
echo ""

# Step 1: Call with tools
MESSAGES=$(jq -n --arg q "$QUERY" '[{"role":"user","content":$q}]')
RESPONSE=$(call_api "$MESSAGES" true)

# Check if model wants to call a tool
TOOL_CALLS=$(echo "$RESPONSE" | jq '.choices[0].message.tool_calls // empty')

if [ -n "$TOOL_CALLS" ]; then
  echo "🔧 Agent wants to use tools:"
  
  # Process each tool call
  RESULTS="[]"
  for row in $(echo "$TOOL_CALLS" | jq -r '.[] | @base64'); do
    _jq() { echo "$row" | base64 -d | jq -r "$1"; }
    
    FN_NAME=$(_jq '.function.name')
    FN_ARGS=$(_jq '.function.arguments')
    CALL_ID=$(_jq '.id')
    
    echo "  → $FN_NAME($FN_ARGS)"
    
    # Execute tool
    case "$FN_NAME" in
      calculate)
        EXPR=$(echo "$FN_ARGS" | jq -r '.expression')
        RESULT=$(echo "$EXPR" | bc -l 2>/dev/null || echo "Error")
        ;;
      get_weather)
        CITY=$(echo "$FN_ARGS" | jq -r '.city')
        RESULT="22°C, sunny (mock data for $CITY)"
        ;;
      *)
        RESULT="Unknown tool"
        ;;
    esac
    
    echo "  ← $RESULT"
    RESULTS=$(echo "$RESULTS" | jq --arg id "$CALL_ID" --arg name "$FN_NAME" --arg res "$RESULT" \
      '. + [{"id": $id, "name": $name, "result": $res}]')
  done
  
  # Step 2: Send tool results back
  TOOL_MSG=$(echo "$TOOL_CALLS" | jq '[.[] | {"role": "tool", "tool_call_id": .id, "content": "executed"}]')
  ASSISTANT_MSG=$(echo "$RESPONSE" | jq '.choices[0].message')
  MESSAGES=$(jq -n --argjson msgs "$MESSAGES" --argjson assistant "$ASSISTANT_MSG" --argjson tools "$TOOL_MSG" \
    '$msgs + [$assistant] + $tools')
  
  FINAL=$(call_api "$MESSAGES" false)
  echo ""
  echo "✅ Answer: $(echo "$FINAL" | jq -r '.choices[0].message.content')"
else
  echo "✅ Answer: $(echo "$RESPONSE" | jq -r '.choices[0].message.content')"
fi
