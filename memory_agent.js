#!/usr/bin/env node
/**
 * Memory Agent — Conversational Memory Management
 * Demonstrates sliding window, summarization, and importance-based memory.
 *
 * Usage: OPENAI_API_KEY=xxx OPENAI_BASE_URL=xxx node memory_agent.js
 */

const API_KEY = process.env.OPENAI_API_KEY;
const BASE_URL = process.env.OPENAI_BASE_URL || "https://api.openai.com/v1";
const MODEL = process.env.MODEL || "gpt-4o-mini";

// --- Memory Store ---
class AgentMemory {
  constructor(maxTurns = 4) {
    this.messages = [];
    this.summary = "";
    this.maxTurns = maxTurns;
  }

  add(role, content) {
    this.messages.push({ role, content, ts: Date.now() });
    if (this.messages.length > this.maxTurns * 2) {
      this.summarize();
    }
  }

  async summarize() {
    const old = this.messages.slice(0, -this.maxTurns * 2);
    const text = old.map(m => `${m.role}: ${m.content}`).join("\n");
    // Simple extractive summary — keep last summary + truncate
    this.summary = (this.summary + "\n" + text).slice(-500);
    this.messages = this.messages.slice(-this.maxTurns * 2);
    console.log(`  🧠 Memory compressed: ${old.length} messages → summary (${this.summary.length} chars)`);
  }

  getContext() {
    const ctx = [];
    if (this.summary) {
      ctx.push({ role: "system", content: `Conversation summary so far:\n${this.summary}` });
    }
    return [...ctx, ...this.messages];
  }
}

async function callLLM(messages) {
  const r = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: MODEL, messages, temperature: 0.3 }),
  });
  const data = await r.json();
  return data.choices[0].message.content;
}

async function main() {
  const readline = require("readline");
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const memory = new AgentMemory(3);

  console.log("🧠 Memory Agent — type messages (Ctrl+C to exit)\n");

  const ask = () => {
    rl.question("You: ", async (input) => {
      if (!input.trim()) return ask();
      memory.add("user", input);

      const response = await callLLM([
        { role: "system", content: "You are a friendly assistant with good memory. Reference earlier conversation when relevant." },
        ...memory.getContext(),
      ]);
      memory.add("assistant", response);
      console.log(`Agent: ${response}\n  [Memory: ${memory.messages.length} active messages, ${memory.summary.length} chars summary]\n`);
      ask();
    });
  };
  ask();
}

main();
