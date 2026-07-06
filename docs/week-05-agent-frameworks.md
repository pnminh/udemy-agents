# Week 5 Tutorial: Six Frameworks, One Recipe

**Code folder:** [`5_agent_frameworks/`](../5_agent_frameworks/)

New agent frameworks launch constantly. That used to feel overwhelming. After this week, it won't.

You'll rebuild the **same worker agent** six times using six different SDKs — Google ADK, AWS Strands, Pydantic AI, Microsoft Agent Framework, Agno, and Mastra (TypeScript). Same five steps every day. Same shared todo board. Same MCP filesystem server.

The capstone is wild: an **orchestrator agent** launches all five workers in parallel to build a **Language Learning Arcade** — mini browser games in Spanish, French, or whatever language you choose — then QA-tests them in a real browser.

This week is about **literacy**, not picking a forever winner.

---

## What this week feels like

Days 1–4 each introduce one or two frameworks and walk through five steps. Day 5 is the orchestra — agents managing agents, live board on screen, browser testing, arcade hub page at the end.

Don't try to memorize syntax. Watch for the pattern.

---

## The five steps (learn this, forget the rest)

Every framework, every day:

1. **Create** an agent — model + instructions
2. **Run** it — send a message, get a reply
3. **Add tools** — Python functions the agent can call (todo board tools)
4. **Connect MCP** — filesystem server so the agent can read/write files
5. **Goal loop** — agent reads the board, plans steps, acts, checks off, repeats until done

Steps 1–2 are just talking to a model. Step 3 adds hands. Step 4 connects to the outside world. **Step 5 is where autonomy begins** — the agent decides its own next move until the goal is complete.

You've done all of this before in different clothes. Week 1 step 5 was your while-loop. Week 2 was Runner.run(). Week 4 was LangGraph cycles. Now you see every vendor implements the same fifth step.

---

## Day 1 — Google ADK

[`1_google_adk_a2a/`](../5_agent_frameworks/1_google_adk_a2a/)

Google's Agent Development Kit. You'll use `LlmAgent`, add tools, wire MCP via `McpToolset`, and run the goal loop. Demo task: read `notes.txt`, translate to Spanish, write `spanish.txt`.

ADK also powers the Day 5 orchestrator — learn it first.

Bonus folder [`a2a_demo/`](../5_agent_frameworks/1_google_adk_a2a/a2a_demo/): agents discovering each other over HTTP (Agent-to-Agent protocol). Interesting preview; MCP remains the main integration story.

Each framework folder has a **`SWAP_AI.md`** showing how to switch models — OpenRouter, DeepSeek, Gemini, Ollama. Same lesson as Week 1, repeated until it sticks.

---

## Day 2 — Strands and Pydantic AI

[`2_strands_pydantic/`](../5_agent_frameworks/2_strands_pydantic/)

Two frameworks, same five steps:

- **AWS Strands** — minimal, `@tool` decorator, `MCPClient` in the tools list. Amazon's take.
- **Pydantic AI** — from the Pydantic team. If you loved typed outputs in Weeks 2 and 4, this feels like home.

Workers become subprocess-ready files (`strands_worker.py`, `pydantic_worker.py`) for Day 5.

---

## Day 3 — Microsoft Agent Framework and Agno

[`3_maf_agno/`](../5_agent_frameworks/3_maf_agno/)

- **MAF** — Microsoft's agent SDK. MCP via `MCPStdioTool`. Relevant if your workplace is Azure-heavy.
- **Agno** — fast to start, mentions **AgentOS** for serving agents as HTTP APIs. Relevant if you want "agent as a microservice."

---

## Day 4 — Mastra (TypeScript)

[`4_mastra/`](../4_mastra/)

Different language, same five steps. Follow [`lab.md`](../5_agent_frameworks/4_mastra/lab.md) through `step1.ts` to `step5.ts`. Tools use **Zod** (TypeScript's answer to Pydantic).

Run **Mastra Studio** (`npm run dev`) at `localhost:4111` — live traces in a browser UI. Nice if your team lives in JavaScript.

---

## Day 5 — The Language Learning Arcade

[`5_agent_loop/`](../5_agent_frameworks/5_agent_loop/)

```bash
cd 5_agent_frameworks/5_agent_loop
uv run agent_loop.py --language Spanish
```

What happens:

1. An ADK **orchestrator agent** receives a language
2. It writes shared CSS for all games
3. It **launches each framework's worker** as a subprocess — same workers you built Days 2–4, not rewritten
4. A live **SQLite todo board** on screen shows progress (color-coded per framework)
5. A **QA agent** with Playwright MCP opens each game in a real browser — pass or fail
6. Failed games get **one fix round**
7. A hub page (`site/index.html`) links all games — your arcade

The orchestrator is an agent with tools, not a Python `for` loop. That's the Week 5 lesson: **meta-agents** coordinating worker agents.

---

## The tools behind this week

### The shared SQLite todo board

Every worker reads and writes the same board via tools (`show_todos`, `plan_steps`, `complete_task`). Workers run as **subprocesses** — separate programs — so they need shared persistent storage, not variables in memory.

Same idea as Week 4's checkpointer (save conversation state) but organized around **tasks**, not chat messages.

### MCP filesystem — same server, six wiring styles

Every framework connects to `@modelcontextprotocol/server-filesystem`. The protocol is stable; only the adapter syntax changes. ADK uses `McpToolset`. Strands uses `MCPClient`. Pydantic AI uses `MCPToolset`. MAF uses `MCPStdioTool`. Mastra uses `MCPClient` in TypeScript.

Week 4 used Playwright MCP (browser). Week 5 uses filesystem only — lighter, focused on comparing frameworks not tools.

Week 6 composes **six different MCP servers** at once. Week 5 teaches wiring; Week 6 teaches composition.

### Playwright for QA

The QA agent opens each game's HTML in a real browser. Same Playwright MCP family as Week 4 Sidekick, different job — validation instead of research.

### Why six frameworks instead of mastering one?

Job interviews. Client requests. GitHub README confidence. And the deeper lesson: **they're variations on the five steps**. When the seventh framework launches next month, you'll ask "how do I create, run, add tools, connect MCP, and loop?" — not "oh no, another thing to learn from scratch."

Pick **one** for production based on your stack:
- Google shop → ADK
- AWS shop → Strands
- Types everywhere → Pydantic AI
- Microsoft shop → MAF
- Need HTTP agent API fast → Agno
- Full-stack JS team → Mastra
- General purpose / largest ecosystem → LangChain (Week 4)

---

## How Week 5 compares

**Better than Weeks 1–4 for:** Framework portability, MCP adapter patterns, seeing the universal agent loop.

**Worse for:** Building one polished product — you spend the week learning syntax, not features.

**Directly prepares you for Week 6:** If MCP wiring felt natural Day 4–5, Week 6's custom servers will click fast.

---

## Your checklist

- [ ] Day 1 ADK lab complete (five steps)
- [ ] At least two of Days 2–4 complete
- [ ] Understand the shared board + MCP pattern
- [ ] Run `agent_loop.py` at least once (even `--dry-run`)
- [ ] Open the arcade hub in a browser

---

## When you're ready

Final week: **[Week 6 — MCP & Autonomous Traders](./week-06-mcp.md)**.
