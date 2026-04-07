#!/usr/bin/env python3
"""
ReAct Agent — Reason + Act Loop
The foundational pattern: Think → Do → Observe → Repeat.

Usage: OPENAI_API_KEY=xxx OPENAI_BASE_URL=xxx python react_agent.py
"""

import json, os, sys, requests

API_KEY = os.environ["OPENAI_API_KEY"]
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_STEPS = 5

# --- Available Tools ---
def calculate(expr: str) -> str:
    """Safely evaluate a math expression."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expr):
        return "Error: invalid expression"
    return str(eval(expr))

def get_time(city: str) -> str:
    """Get current time for a city (mock)."""
    from datetime import datetime, timezone, timedelta
    offsets = {"beijing": 8, "tokyo": 9, "london": 0, "new york": -4, "san francisco": -7}
    tz = offsets.get(city.lower(), 0)
    t = datetime.now(timezone.utc) + timedelta(hours=tz)
    return f"{t.strftime('%Y-%m-%d %H:%M')} (UTC{tz:+d})"

TOOLS = {
    "calculate": {"fn": calculate, "desc": "Evaluate a math expression", "param": "expr (str)"},
    "get_time": {"fn": get_time, "desc": "Get current time in a city", "param": "city (str)"},
}

TOOL_PROMPT = "You have these tools:\n"
for name, t in TOOLS.items():
    TOOL_PROMPT += f"- {name}: {t['desc']}. Param: {t['param']}\n"
TOOL_PROMPT += "\nRespond in JSON: {\"thought\": \"...\", \"action\": \"tool_name|answer\", \"input\": \"...\", \"answer\": \"...\"}\n"
TOOL_PROMPT += "Use action=answer with answer field when you have the final answer.\n"

def call_llm(messages):
    r = requests.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "temperature": 0.1})
    return r.json()["choices"][0]["message"]["content"]

def react_loop(query: str):
    messages = [
        {"role": "system", "content": "You are a helpful agent. " + TOOL_PROMPT},
        {"role": "user", "content": query},
    ]
    for step in range(MAX_STEPS):
        print(f"\n--- Step {step + 1} ---")
        resp = call_llm(messages)
        print(f"Agent: {resp}")
        try:
            parsed = json.loads(resp)
        except json.JSONDecodeError:
            return resp

        action = parsed.get("action", "")
        if action == "answer":
            return parsed.get("answer", resp)
        
        if action in TOOLS:
            result = TOOLS[action]["fn"](parsed.get("input", ""))
            print(f"Tool [{action}] → {result}")
            messages.append({"role": "assistant", "content": resp})
            messages.append({"role": "user", "content": f"Observation: {result}"})
        else:
            messages.append({"role": "user", "content": f"Unknown tool: {action}. Try again."})
    
    return "Max steps reached."

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "What time is it in Beijing? And what is 42 * 17 + 3?"
    print(f"Query: {query}")
    answer = react_loop(query)
    print(f"\n✅ Final Answer: {answer}")
