#!/usr/bin/env python3
"""
Guardrail Agent — Safety guardrails & output validation.
Demonstrates input/output filtering layers used in production agent systems.

Usage: OPENAI_API_KEY=xxx OPENAI_BASE_URL=xxx python guardrail_agent.py
"""

import json, os, sys, re, requests

API_KEY = os.environ["OPENAI_API_KEY"]
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")

# --- Input Guardrails ---
def check_injection(text: str) -> tuple[bool, str]:
    """Detect common prompt injection patterns."""
    patterns = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+",
        r"system\s*:\s*",
        r"forget\s+(everything|your\s+instructions)",
    ]
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return False, f"⚠️ Input blocked: potential injection detected"
    return True, "Input OK"

def check_pii(text: str) -> tuple[bool, str]:
    """Detect potential PII in input."""
    patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    }
    for kind, p in patterns.items():
        if re.search(p, text):
            return False, f"⚠️ Input blocked: potential {kind} detected. Please remove sensitive data."
    return True, "No PII detected"

# --- Output Guardrails ---
def check_output_safety(text: str) -> tuple[bool, str]:
    """Validate LLM output for safety."""
    dangerous = ["exec(", "eval(", "os.system(", "subprocess", "rm -rf"]
    for d in dangerous:
        if d in text:
            return False, f"⚠️ Output blocked: contains potentially dangerous code pattern"
    return True, "Output OK"

def call_llm(user_msg: str) -> str:
    r = requests.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": user_msg},
        ], "temperature": 0.3})
    return r.json()["choices"][0]["message"]["content"]

def guarded_respond(query: str) -> str:
    # Input guardrails
    for guard_name, guard_fn in [("injection", check_injection), ("pii", check_pii)]:
        ok, msg = guard_fn(query)
        print(f"  🛡️ Input [{guard_name}]: {msg}")
        if not ok:
            return msg
    
    # Call LLM
    response = call_llm(query)
    
    # Output guardrails
    ok, msg = check_output_safety(response)
    print(f"  🛡️ Output [safety]: {msg}")
    if not ok:
        return "I can't provide that response due to safety guidelines."
    
    return response

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "How do I read a file in Python?"
    print(f"Query: {query}\n")
    answer = guarded_respond(query)
    print(f"\n✅ Response:\n{answer}")
