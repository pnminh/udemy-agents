# Week 2 Tutorial: The OpenAI Agents SDK — Your First Framework

**Code folder:** [`2_openai/`](../2_openai/)

You wrote the agent loop by hand last week. This week, you get help.

The **OpenAI Agents SDK** (`openai-agents` package) wraps that same loop into two concepts: an **Agent** (who) and a **Runner** (run until done). You'll add tracing, memory, multi-agent orchestration, guardrails, and build a **Deep Research** system that plans web searches, writes a report, and emails it to you.

Think of Week 1 as learning to drive stick shift. Week 2 is discovering cruise control — same road, less leg work, more attention on *where you're going*.

---

## What this week feels like

Day 1: "Wait, that's it?" — Agent plus Runner replaces your while-loop.

Day 2: You run a small sales team — three copywriters, an editor, a mailroom.

Day 3: Typed outputs, different models, safety guardrails.

Day 4: The capstone — Deep Research, then refactor it into a deployable app.

---

## Day 1 — Meet the SDK

Open [`1_lab1.ipynb`](../2_openai/1_lab1.ipynb).

Install the package first — it's called **`openai-agents`**, not `agents`:

```bash
uv add openai-agents
```

The core pattern is almost embarrassingly simple:

```python
from agents import Agent, Runner

agent = Agent(
    name="Jokester",
    instructions="You tell great jokes.",
    model="gpt-4.1-mini"
)
result = await Runner.run(agent, "Tell me a joke about AI")
print(result.final_output)
```

That `Runner.run()` call? That's your Week 1 while-loop, packaged. You'll feel the difference if you built Week 1 properly.

The lab also introduces:
- **`trace()`** — wrap a run and get a link to a full timeline on the OpenAI dashboard. Essential when things get multi-step.
- **`@function_tool`** — write a Python function, decorator turns it into a tool. No manual JSON schemas.
- **`SQLiteSession`** — pass a session ID and the agent remembers prior conversation turns, even after restart.

**Bridge exercise:** Rebuild your Week 1 Digital Twin using the SDK. You'll finish in half the code.

---

## Day 2 — Orchestration: who decides what's next?

Open [`2_lab2.ipynb`](../2_openai/2_lab2.ipynb).

The business scenario is **sales email automation** — practical, relatable, and easy to adapt to other domains.

You'll set up email via SMTP (Gmail app passwords work) with a Pushover fallback in [`messenger.py`](../2_openai/messenger.py). Flip `USE_EMAIL=false` if you'd rather get phone pings than emails.

Then two orchestration styles:

**Orchestration by code** — *you* decide the sequence. Three agents write emails in different styles. You gather the results. A picker agent chooses the best. Optionally, a tool sends it. Predictable. Testable. This is how you'd build something you'd stake your job on.

**Orchestration by the LLM** — a "manager" agent decides which sub-agents to call. Wrap a specialist as `agent.as_tool()` and the manager invokes it like any other tool. Control returns to the manager afterward (A → B → A). This is flexible but less deterministic.

There's also **handoffs** — pass control to another agent permanently (A → B, no return). The lab shows why this is less reliable than agents-as-tools. Good to know; rarely the first choice.

---

## Day 3 — Structure, models, and guardrails

Open [`3_lab3.ipynb`](../2_openai/3_lab3.ipynb).

**Different models:** Use `OpenAIChatCompletionsModel` with any OpenAI-compatible client — DeepSeek, Gemini, whatever you configured in Week 1.

**Structured outputs:** Define a Pydantic class, attach it as `output_type`, and `result.final_output` is a typed Python object — not a string you have to parse. This pattern appears in every later week. Get comfortable with it here.

**Guardrails:** Functions that inspect input or output and can halt the pipeline. Like a bouncer, not a suggestion in the prompt. One caveat the lab teaches honestly: input guardrails only fire on the first message; output guardrails only on the final answer. For mid-pipeline checks, run an explicit checker agent.

---

## Day 4 — Deep Research

Open [`4_lab4.ipynb`](../2_openai/4_lab4.ipynb).

This is the Week 2 capstone and a pattern you'll see in dozens of real products: plan → gather → synthesize → deliver.

Four agents, orchestrated by code:
1. **Planner** — breaks your question into targeted web searches (structured output)
2. **Search agents** — one per search, run in parallel
3. **Writer** — long markdown report
4. **Emailer** — sends HTML to your inbox

The search agent uses OpenAI's **`WebSearchTool`** — hosted search, about a penny per call, zero setup. Great for learning. In production at scale, you'd swap in Serper or Tavily (Weeks 3–6) for cost control.

After the notebook, the project moves into [`deep_research/`](../2_openai/deep_research/) — modular Python files plus a Gradio app ([`app.py`](../2_openai/deep_research/app.py)). Deploy it like Week 1's Digital Twin.

---

## The tools behind this week

### OpenAI Agents SDK — why now, not Week 1?

Because you needed to feel the loop first. The SDK hides boilerplate — message formatting, tool dispatch, re-calling after tool results — that you manually wrote last week. Now that you've felt the friction, you'll appreciate the relief.

It's **better than Week 1** for multi-step pipelines, tracing, and multi-agent work.

It's **less transparent than Week 1** — when debugging, you sometimes peek at SDK internals or add print statements around `Runner.run()`.

It **returns in Week 6** as the MCP client for the trading floor capstone. The course comes full circle.

### Agent and Runner

An **Agent** is a named worker: instructions, model, optional tools, optional output type. Sound familiar? It's your system prompt from Week 1, with a name tag.

**Runner** executes the loop. Trust it because you built the loop yourself.

### trace()

Multi-agent pipelines fail in confusing ways — "which agent produced that?" Traces are a flight recorder. Wrap runs in `with trace("name"):` and open the link. Week 4 adds LangSmith for LangChain; Week 6 writes traces to your own database. Same need, different viewers.

### @function_tool

Week 1: you wrote JSON schemas by hand. Week 2: write a function, add a decorator, docstring becomes the tool description. Same capability, far less typing. LangChain's `@tool` (Week 4) and FastMCP (Week 6) follow the same philosophy.

### SQLiteSession

Week 1: you passed conversation history lists manually in Gradio. Week 2: `SQLiteSession("user-123")` persists memory on disk keyed by session. Simpler for chat apps.

Week 4's LangGraph **checkpointer** goes further — it saves arbitrary workflow state, not just messages. Useful when you need to pause mid-task for human approval.

### Pydantic structured outputs

Free-text LLM output is fragile when the next step expects `{title, summary, markdown}`. Pydantic forces the model to fill in a form. You'll see this in CrewAI's `output_pydantic` (Week 3), LangChain's `with_structured_output` (Week 4), and Mastra's Zod schemas (Week 5). Week 2 is where the pattern clicks.

### Guardrails vs Week 4 middleware

Week 2 guardrails are explicit tripwires — block and stop. Week 4's **middleware** (PII redaction, human-in-the-loop pauses, call limits) is richer and can intercept mid-run. Guardrails are the seed; middleware is the tree.

### WebSearchTool vs later search tools

Week 2's hosted search is convenient — no API key, one line. Weeks 3–6 use **Serper** or **Tavily** because they work with any LLM provider and cost less at scale. Start with WebSearchTool to learn the pipeline; swap the search backend when you're counting pennies.

### messenger.py — email and Pushover together

Centralizes delivery. SMTP for long reports; Pushover when email isn't configured. The graceful fallback pattern — try the fancy thing, fall back to the simple thing — is worth copying in your own projects.

---

## How Week 2 fits between Week 1 and Week 3

| Question | Reach for Week 2 when… | Reach elsewhere when… |
|----------|------------------------|----------------------|
| Quick OpenAI-native agents | ✅ | — |
| You want YAML role-based teams | — | Week 3 CrewAI |
| Custom branching workflows | — | Week 4 LangGraph |
| Compare six frameworks | — | Week 5 |
| Build your own tool servers | — | Week 6 MCP |

Week 2 agents are mostly **solo performers** you coordinate. Week 3 gives them **job titles and a shared org chart**. Different metaphor, different tool, same underlying LLM calls.

---

## Your capstone checklist

- [ ] Run Labs 1–4
- [ ] Deep Research working in the notebook
- [ ] [`deep_research/app.py`](../2_openai/deep_research/app.py) running locally
- [ ] Optional: deploy to HuggingFace Spaces
- [ ] Optional: swap WebSearchTool for a cheaper search API

---

## When you're ready

Head to **[Week 3 — CrewAI](./week-03-crewai.md)** — time to build a team.
