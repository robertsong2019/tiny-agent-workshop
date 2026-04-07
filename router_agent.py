#!/usr/bin/env python3
"""
Intent Router Agent — Mixture of Agents pattern.
A lightweight router classifies intent and dispatches to specialized sub-agents.

Usage: OPENAI_API_KEY=xxx OPENAI_BASE_URL=xxx python router_agent.py
"""

import json, os, sys, requests

API_KEY = os.environ["OPENAI_API_KEY"]
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")

def call_llm(system: str, user: str) -> str:
    r = requests.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ], "temperature": 0.1})
    return r.json()["choices"][0]["message"]["content"]

# --- Specialized Agents ---
AGENTS = {
    "code": {
        "system": "You are a coding expert. Give concise, working code answers. Use markdown code blocks.",
        "desc": "Code generation, debugging, programming questions",
    },
    "creative": {
        "system": "You are a creative writer. Be imaginative, vivid, and engaging. Tell stories, write poems, craft descriptions.",
        "desc": "Creative writing, storytelling, poetry",
    },
    "analyst": {
        "system": "You are a data analyst. Think in numbers, comparisons, and trade-offs. Be precise and structured.",
        "desc": "Data analysis, comparisons, research, facts",
    },
    "general": {
        "system": "You are a helpful, friendly assistant. Answer clearly and concisely.",
        "desc": "General questions, casual chat",
    },
}

ROUTER_SYSTEM = f"""Classify the user's message into exactly one category. Respond with ONLY the category name.

Categories:
{chr(10).join(f"- {k}: {v['desc']}" for k, v in AGENTS.items())}

Respond with just the category key, nothing else."""

def route_and_respond(query: str) -> str:
    # Step 1: Route
    category = call_llm(ROUTER_SYSTEM, query).strip().lower()
    if category not in AGENTS:
        category = "general"
    print(f"🔀 Routed to: {category}")
    
    # Step 2: Dispatch to specialist
    response = call_llm(AGENTS[category]["system"], query)
    return response

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Write a haiku about Python programming"
    print(f"Query: {query}")
    answer = route_and_respond(query)
    print(f"\n✅ Response ({'routed'}):\n{answer}")
