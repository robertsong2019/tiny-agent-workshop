#!/usr/bin/env bash
#
# Chain Agent — Agent Pipeline / Chaining
# Each agent's output feeds into the next, like a Unix pipe for AI.
#
# Usage: OPENAI_API_KEY=xxx OPENAI_BASE_URL=xxx bash chain_agent.sh "AI agents"

set -euo pipefail

API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY}"
BASE_URL="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
MODEL="${MODEL:-gpt-4o-mini}"
TOPIC="${*:-AI agents}"

call_llm() {
  local system="$1" user="$2"
  curl -s "$BASE_URL/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg model "$MODEL" --arg sys "$system" --arg user "$user" \
      '{model: $model, messages: [{role:"system",content:$sys},{role:"user",content:$user}], temperature: 0.7}')" \
    | jq -r '.choices[0].message.content'
}

echo "🔗 Chain Pipeline: Research → Summarize → Translate → Format"
echo "📖 Topic: $TOPIC"
echo ""

# Agent 1: Researcher
echo "1️⃣ Researcher..."
STEP1=$(call_llm "You are a research agent. Generate 5 key bullet points about the given topic. Be factual and insightful." "$TOPIC")
echo "   ✅ Done (${#STEP1} chars)"

# Agent 2: Summarizer
echo "2️⃣ Summarizer..."
STEP2=$(call_llm "You are a summarization agent. Take the following notes and create a concise 2-3 sentence summary capturing the essence." "$STEP1")
echo "   ✅ Done (${#STEP2} chars)"

# Agent 3: Translator (to Chinese)
echo "3️⃣ Translator..."
STEP3=$(call_llm "You are a translator. Translate the following English text to Chinese. Keep it natural." "$STEP2")
echo "   ✅ Done (${#STEP3} chars)"

# Agent 4: Formatter
echo "4️⃣ Formatter..."
STEP4=$(call_llm "You are a formatting agent. Take the following content and format it beautifully as a mini-report with a title, horizontal rules, and clear sections. Use markdown." "Topic: $TOPIC\n\nEnglish summary: $STEP2\nChinese translation: $STEP3")
echo "   ✅ Done"

echo ""
echo "═══════════════════════════════════"
echo "📋 Final Output:"
echo "═══════════════════════════════════"
echo "$STEP4"
