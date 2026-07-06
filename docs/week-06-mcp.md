# Week 6 Tutorial: MCP and the Autonomous Traders Finale

**Code folder:** [`6_mcp/`](../6_mcp/)

This is the grand finale.

You return to the **OpenAI Agents SDK** from Week 2 — but now agents plug into a **universe of external tools** through Model Context Protocol (MCP). You'll use community servers, build your own with FastMCP, engineer context deliberately, and run **Autonomous Traders**: four AI traders on a simulated trading floor with a live dashboard that looks like a real product.

If Week 1 was learning to drive and Week 5 was test-driving six cars, Week 6 is building the highway system those cars share.

---

## What this week feels like

Day 1: Plug in tools someone else built (browser, fetch, filesystem).

Day 2: Build tools yourself.

Day 3: Learn **context engineering** — what information each agent sees and why.

Days 4–5: The capstone — traders, researcher, six MCP servers, Gradio dashboard evolving into FastAPI + Vite.

By Friday you're running three terminals and watching AI trade fake stocks on a chart. It's a lot. You've earned it.

---

## Day 1 — Meet MCP

[`1_lab1.ipynb`](../6_mcp/1_lab1.ipynb)

**Model Context Protocol** is a standard way for agents to talk to external programs. Think USB: one port shape, many devices.

An **MCP server** is a program that offers tools (do things), resources (show data), and prompts (templates). Your agent connects as a client.

You'll connect via **`MCPServerStdio`** — spawn a local subprocess:

| Server | What it gives your agent |
|--------|--------------------------|
| **Fetch** (`uvx mcp-server-fetch`) | Any URL → readable markdown |
| **Playwright** (`npx @playwright/mcp`) | Control a real browser |
| **Filesystem** (`npx @modelcontextprotocol/server-filesystem`) | Read/write a scoped folder |

Combine multiple servers in one agent — the model picks the right tool per task.

You'll also try **`MCPServerStreamableHttp`** — connect to a hosted MCP server over the internet (no local subprocess). Context7 docs server is a good example.

Browse more servers at [glama.ai/mcp](https://glama.ai/mcp) and [smithery.ai](https://smithery.ai).

**Windows Jupyter tip:** redirect MCP stderr to `DEVNULL` if pipes choke — the lab shows how.

---

## Day 2 — Build your own MCP server

[`2_lab2.ipynb`](../6_mcp/2_lab2.ipynb)

Consuming tools is half the story. Real products need **custom business logic** — account balances, trading rules, your company's internal APIs.

**FastMCP** makes this easy:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("accounts")

@mcp.tool()
def get_balance(name: str) -> str:
    """Get account balance for a trader."""
    ...
```

You'll build an accounts server, connect an agent to it, and see the same tool work regardless of which framework might call it later. That's the MCP promise from Week 5 made concrete.

Exercise hint: build a push-notification server ([`backend/push_server.py`](../6_mcp/backend/push_server.py)).

---

## Day 3 — Context engineering

[`3_lab3.ipynb`](../6_mcp/3_lab3.ipynb)

Prompt engineering asks "how should I phrase the instruction?" **Context engineering** asks "what information should this agent *see*?"

Four sources, four MCP servers:

- **Memory** — long-term facts that persist (`server-memory` → knowledge graph)
- **Tavily search** — fresh web information (with tool filtering so the agent only gets search, not every Tavily endpoint)
- **Qdrant** — vector store the agent builds and queries itself (**agentic RAG** — the agent decides what to remember)
- **Market data** — live or simulated stock prices

Dumping everything into one giant prompt doesn't scale. Different agents should see different context. Week 6's traders vs researcher split is the flagship example.

---

## Days 4–5 — Autonomous Traders

[`4_lab4.ipynb`](../6_mcp/4_lab4.ipynb) introduces the architecture. [`5_lab5.ipynb`](../6_mcp/5_lab5.ipynb) adds production polish.

### The cast

Four traders — **Warren**, **George**, **Ray**, **Cathie** — each with personality, strategy, and an account. They run on a timer via [`trading_floor.py`](../6_mcp/backend/trading_floor.py), making decisions without you clicking anything. That's new — prior weeks mostly ran agents once per user action.

Each trader connects to three MCP servers (accounts, push notifications, market data) plus a **Researcher agent wrapped as a tool**.

### Why a separate Researcher?

This is the week's most important design lesson, stated plainly:

**Agent roles exist for context management, not to mimic human org charts.**

Traders need concise decision prompts. Research needs long web fetches and memory. Mix both in one agent and both behaviors degrade. So the Researcher is a full agent — with its own MCP servers (fetch, Tavily, per-trader memory) — exposed to the trader via `researcher.as_tool()`. Same pattern as Week 2's agents-as-tools, now MCP-heavy.

### Six MCP servers total

Three you build (accounts, push, market). Three from the community (fetch, Tavily, memory). Week 5 wired one server six ways. Week 6 composes six servers into one system.

### Day 4 UI — Gradio

[`app.py`](../6_mcp/app.py) launches a Gradio dashboard reading the activity log. Two terminals:

```bash
uv run app.py                        # dashboard
uv run -m backend.trading_floor      # trading engine
```

Gradio again — Week 1's old friend — gets you a working dashboard fast.

### Day 5 upgrades

Three improvements:

**LogTracer** — custom trace processor writing OpenAI SDK spans to SQLite, displayed in the UI. Week 2's traces lived on OpenAI's website. Now they're embedded in *your* product.

**`change_strategy` tool** — traders review portfolio performance and rewrite their own strategy text in the database. Self-improvement that's explicit and auditable, not mysterious.

**FastAPI + Vite frontend** — proper API ([`backend/api.py`](../6_mcp/backend/api.py)) plus a TypeScript SPA ([`frontend/`](../6_mcp/frontend/)) with charts, heatmaps, and a live log. Three terminals:

```bash
uv run uvicorn backend.api:app --port 8000
cd frontend && npm run dev           # localhost:5173
uv run -m backend.trading_floor
```

This is what "graduating from demo to product" looks like. Same data as Gradio Day 4; better architecture Day 5.

---

## The tools behind this week — full tour

### MCP vs Week 1 inline tools

Week 1 tools were Python functions in your notebook. Simple, direct, perfect for learning.

MCP tools live in **separate processes**. More setup, but: reusable across frameworks, isolatable when they crash, shareable with the community, composable (six servers at once).

Use inline tools for quick personal scripts. Use MCP when you're building something others will extend or when tools need isolation.

### FastMCP vs @function_tool

Week 2's `@function_tool` attaches functions to one agent in one process. FastMCP creates a **server** any agent can connect to. Build once, use from Agents SDK, LangChain, ADK, whatever.

### Context engineering vs Week 1's system prompt

Week 1 stuffed your LinkedIn PDF into the system prompt. Worked for one document. Week 6 feeds agents from memory, search, RAG, and live APIs — each updating independently, each scoped to the agent that needs it.

### Gradio vs FastAPI + Vite

Gradio: fast, Python-only, limited customization. Right for Day 4 and every earlier week's demo.

FastAPI + Vite: decoupled backend and frontend, custom charts, polling, closer to how startups ship. Right for Day 5 when the dashboard *is* the product.

You need both skills. Prototype in Gradio; productize when requirements outgrow it.

### The trading floor scheduler

Prior weeks: you click Run. Week 6: agents run every N minutes on a timer (`RUN_EVERY_N_MINUTES`). That's cron-job territory — background workers, monitoring bots, autonomous ops. Think about API cost when `N` is small.

---

## How Week 6 connects to everything before

| You learned in… | You see it again in Week 6 as… |
|-----------------|--------------------------------|
| Week 1 loop | Runner + MCP tool loop |
| Week 1 Pushover | push_server MCP |
| Week 2 Agents SDK | Primary agent framework |
| Week 2 agents-as-tools | Researcher wrapped for traders |
| Week 2 structured output | Strategy resources in accounts DB |
| Week 3 Serper/search | Tavily MCP |
| Week 4 Playwright MCP | Research fetches (lighter than full browser for some tasks) |
| Week 4 Gradio | Day 4 dashboard |
| Week 5 MCP wiring | Six servers composed |
| Week 5 orchestrator pattern | trading_floor scheduler + agent roles |

Week 6 has the most moving parts. If it overwhelms, that's normal. Revisit Week 2's SDK and Week 5's MCP wiring — the capstone assumes those, not that you've memorized every trader's personality.

---

## Environment variables worth knowing

```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=...
PUSHOVER_USER=...
PUSHOVER_TOKEN=...

RUN_EVERY_N_MINUTES=60
RUN_EVEN_WHEN_MARKET_IS_CLOSED=true
USE_MANY_MODELS=false

# Optional live market data
MASSIVE_API_KEY=...
```

Simulated market data works without extra keys.

---

## Your final checklist

- [ ] Lab 1 — connected at least two MCP servers
- [ ] Lab 2 — built or understood the accounts server
- [ ] Lab 3 — tried memory + search + RAG sources
- [ ] Day 4 — Gradio trading dashboard running
- [ ] Day 5 — FastAPI + Vite frontend running
- [ ] Watched at least one full trader cycle in the log
- [ ] Understand *why* Researcher is separate from Trader

---

## You finished the course

Six weeks ago you sent a single `chat.completions.create()` call. Now you're running autonomous agents with custom tool servers, structured feedback loops, and a production-shaped dashboard.

Browse `community_contributions/` in each week folder for project ideas. Deploy your favorite capstone. Consider contributing back.

And if someone asks which framework to use? Tell them the truth you now know: **learn the five steps, pick the SDK that matches your stack, and compose MCP servers for everything else.**

Back to **[course home](./README.md)**.
