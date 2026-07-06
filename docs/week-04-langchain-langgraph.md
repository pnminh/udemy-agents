# Week 4 Tutorial: LangChain, LangGraph, and Your Personal Sidekick

**Code folder:** [`4_langchain_langgraph/`](../4_langchain_langgraph/)

Week 3 gave you high-level team abstractions. Week 4 zooms back in and asks: **what's actually happening under the hood?**

You'll climb four layers of abstraction — from raw LLM calls up to autonomous "Deep Agents" — and build **Sidekick**, a personal co-worker that accepts a task plus success criteria, plans in a visible to-do list, browses the web, asks for your help when stuck, and checks its own work before saying "done."

This week has the most conceptual depth in the course. Take it slowly. The payoff is understanding *any* agent framework, not just this one.

---

## What this week feels like

Day 1: Back to basics with LangChain messages and tools — familiar if you did Week 1.

Day 2: Draw your agent as a flowchart with LangGraph. This clicks for visual thinkers.

Day 3: `create_agent` — the loop pre-built, plus middleware hooks.

Day 4: Deep Agents for long tasks with planning and sub-agents.

Day 5: Sidekick capstone — everything combined, plus a Gradio app you can actually use for errands.

---

## The four layers (read this before the labs)

Think of four floors in a building. You can live on any floor, but you should know what's below you.

**Layer 1 — Building blocks (LangChain core):** Messages, models, tools, manual loops. Week 1 vibes, standardized.

**Layer 2 — LangGraph:** Stateful flowcharts. Nodes, edges, shared state, checkpointing. "If the model wants tools, go here; otherwise stop."

**Layer 3 — `create_agent`:** The standard tool loop as a pre-built graph, plus middleware (PII redaction, human approval, todo lists).

**Layer 4 — Deep Agents:** Planning, sandbox filesystem, sub-agent delegation. For long-horizon autonomous work.

Sidekick deliberately **mixes layers**: worker agent at Layer 3, evaluator at Layer 1 structured output, MCP tools from Layer 2 patterns. Real apps do this. You're not cheating.

---

## Day 1 — LangChain fundamentals

[`1_lab1.ipynb`](../4_langchain_langgraph/1_lab1.ipynb)

Chat models, message types (`SystemMessage`, `HumanMessage`), the `@tool` decorator, binding tools to a model, and the manual tool loop you already know from Week 1. Plus structured output with Pydantic.

If Week 1 felt clear, Day 1 is confirmation. If Week 1 felt shaky, Day 1 fills gaps with LangChain's vocabulary.

---

## Day 2 — LangGraph

[`2_lab2.ipynb`](../4_langchain_langgraph/2_lab2.ipynb)

Here's the mental model: a **shared notepad** (state) passes between **stations** (nodes). Each station does one thing — call the model, run tools, translate text. **Edges** are arrows. Some arrows are conditional: "only go to the tool station if the model asked for tools."

**Checkpointing** saves the notepad per conversation thread — like save points in a game. Close the app, come back, continue.

You'll also meet **LangSmith** (optional) for tracing which node ran with what input. Same purpose as Week 2's `trace()`, different dashboard.

This is the sweet spot when CrewAI's sequential/hierarchical processes aren't flexible enough — when you need "if X, go back to step 1" or pause mid-run for human approval.

---

## Day 3 — create_agent and middleware

[`3_lab3.ipynb`](../4_langchain_langgraph/3_lab3.ipynb)

`create_agent(model, tools, system_prompt)` gives you a working agent loop without drawing the graph yourself. Under the hood, it's LangGraph. You just don't have to draw it yet.

**Middleware** is the Week 4 superpower — hooks that run around model and tool calls:

- **TodoListMiddleware** — agent maintains a visible plan (Sidekick shows this live)
- **PIIMiddleware** — redacts emails and phone numbers before they hit the model
- **ModelCallLimitMiddleware** — caps API calls so a runaway agent doesn't drain your wallet
- **HumanInTheLoopMiddleware** — pauses before sensitive actions; you Approve, Edit, or Reject

Week 2 guardrails block bad output at the start or end. Middleware can intercept **mid-run** — much more useful for production.

You'll also connect **Playwright MCP** — a real browser the agent can control. First serious browser automation in the course.

---

## Day 4 — Deep Agents

[`4_lab4.ipynb`](../4_langchain_langgraph/4_lab4.ipynb)

Some tasks are too long for one agent context window. Deep Agents add built-in planning, a sandbox filesystem, and **sub-agents** — delegated helpers with fresh context, invoked via a `task` tool.

The lab demo: research a topic → write a fleet briefing → generate a PowerPoint slide.

Compared to Week 3 crews: Deep Agents feel like one manager delegating temp workers. CrewAI feels like a permanent org chart. Different shapes for different problems.

---

## Day 5 — Sidekick capstone

[`5_lab5.ipynb`](../4_langchain_langgraph/5_lab5.ipynb) walks you through building Sidekick step by step. The finished app lives in:

- [`sidekick.py`](../4_langchain_langgraph/sidekick.py) — worker + evaluator
- [`sidekick_tools.py`](../4_langchain_langgraph/sidekick_tools.py) — search, browser, filesystem, push, human-help tools
- [`app.py`](../4_langchain_langgraph/app.py) — Gradio UI

Run it:

```bash
cd 4_langchain_langgraph
uv run app.py
```

Give Sidekick a request **and** explicit success criteria — "Find the cheapest flight NYC to London next month" plus "Must include airline name, price, and booking URL." Vague goals produce vague results.

Sidekick plans (visible in the UI), works (browser, search, files), and may **pause** to ask you to approve a push notification or help with a login screen. When it thinks it's done, a separate **evaluator** checks the work against your criteria. Fail? It retries up to three times with feedback.

Try the Hacker News headline task first. Then flights. Then something from your actual life.

---

## The tools behind this week

### Why LangChain/LangGraph now?

CrewAI optimizes for **teams with roles**. LangGraph optimizes for **custom control flow**. Sidekick needs both agent capabilities *and* conditional logic (pause for approval, retry on evaluator failure). That's LangGraph territory.

You could build Sidekick in raw Week 1 Python. You could approximate it in CrewAI. LangGraph + `create_agent` + middleware is the production-shaped middle ground.

### MCP browser and filesystem

Week 3 touched MCP with Context7 docs. Week 4 adds **Playwright** (browse real websites) and **filesystem** (read/write a sandbox folder) via `langchain-mcp-adapters`.

Why MCP instead of custom Python tools? Community servers are maintained, feature-rich, and reusable across frameworks. You'll build your own in Week 6; Week 4 teaches you to *consume* them well.

Requires Node.js v22+. Install it before Day 3.

### Serper and Wikipedia

For quick facts, opening a full browser is overkill. Sidekick also has Google search (Serper — same as Week 3) and Wikipedia. Match the tool to the job.

### The evaluator loop — a second opinion

Guardrails ask "is this safe?" The evaluator asks "did you actually complete the task?" Different question. Sidekick's evaluator is a separate LLM call with structured output — not a library feature, a pattern you build in [`sidekick.py`](../4_langchain_langgraph/sidekick.py).

LLM judging LLM isn't perfect. Make success criteria concrete and checkable.

### Gradio — third time, different purpose

Week 1: quick chat demo. Week 2: Deep Research UI. Week 4: Sidekick with live plan panel and Approve button. Same library, growing requirements.

When Week 6 needs portfolio charts and a decoupled API, Gradio stops being enough. Sidekick is Gradio's last comfortable stop.

---

## How Week 4 compares

**Better than Week 3 for:** Branching workflows, human-in-the-loop pauses, custom middleware, fine-grained observability.

**Harder than Week 3 for:** Quick team scaffolding — `crewai create crew` beats drawing graphs when you just need researcher → analyst.

**Builds on Week 1–2 directly:** Same tool loop, same Pydantic structured output, same Pushover side effects — just more control over the shape of execution.

---

## Your checklist

- [ ] Labs 1–5 complete
- [ ] Node.js v22+ installed for MCP
- [ ] `SERPER_API_KEY`, `PUSHOVER_*` in `.env`
- [ ] Sidekick running locally
- [ ] Completed at least one demo task with explicit success criteria
- [ ] Optional: personalize — gate file writes behind approval, add a custom tool

---

## When you're ready

Move to **[Week 5 — Agent Frameworks](./week-05-agent-frameworks.md)** — same recipe, six different kitchens.
