# Welcome to the Agentic AI Course

Hi! These guides are written for **you** — a human learning to build AI agents, not a reference manual for machines. Work through them in order, one week at a time, with the notebooks open beside you.

The course code lives in numbered folders at the repo root. The number is the week:

1. **[Week 1 — Foundations](./week-01-foundations.md)** → [`1_foundations/`](../1_foundations/)
2. **[Week 2 — OpenAI Agents SDK](./week-02-openai-agents-sdk.md)** → [`2_openai/`](../2_openai/)
3. **[Week 3 — CrewAI](./week-03-crewai.md)** → [`3_crewai/`](../3_crewai/)
4. **[Week 4 — LangChain & LangGraph](./week-04-langchain-langgraph.md)** → [`4_langchain_langgraph/`](../4_langchain_langgraph/)
5. **[Week 5 — Agent Frameworks](./week-05-agent-frameworks.md)** → [`5_agent_frameworks/`](../5_agent_frameworks/)
6. **[Week 6 — MCP & Autonomous Traders](./week-06-mcp.md)** → [`6_mcp/`](../6_mcp/)

---

## The story of the six weeks

Imagine you're opening a small business and teaching AI to run parts of it.

In **Week 1**, you hire your first employee — a language model — and teach them by hand: how to answer the phone, take notes, use tools, and call you when they're stuck. No management software. You write every instruction yourself.

In **Week 2**, you buy a lightweight toolkit (the OpenAI Agents SDK) that handles scheduling, memory, and safety checks so you can focus on *who does what* instead of loop mechanics.

In **Week 3**, you stop working alone and build a **team** with job titles — researcher, analyst, judge — using CrewAI.

In **Week 4**, you learn to draw **flowcharts** for how work moves (LangGraph), and you build Sidekick: a personal assistant that plans tasks, browses the web, and asks for your approval before doing sensitive things.

In **Week 5**, you visit six different "offices" (Google ADK, AWS Strands, Pydantic AI, and others) and discover they all run the same five-step playbook — just with different vocabulary.

In **Week 6**, the finale: you plug everything into a **universal tool belt** (MCP), build your own tools, and run a simulated trading floor with a live dashboard.

By the end, you won't just have *used* AI — you'll understand how agents actually work.

---

## Before you write any code

Set up your machine first. Pick your operating system:

- [Windows setup](../setup/SETUP-PC.md)
- [Mac setup](../setup/SETUP-mac.md)
- [Linux setup](../setup/SETUP-linux.md)

You'll also need [Node.js](../setup/SETUP-node.md) later in the course (Weeks 4–6).

Helpful guides in the repo:
- [Intro to the course](../guides/01_intro.ipynb)
- [How to use notebooks](../guides/05_notebooks.ipynb)
- [Using different AI providers and free models](../guides/09_ai_apis_and_ollama.ipynb)

Video walkthroughs live on [Ed Donner's course page](https://edwarddonner.com/2025/04/21/the-complete-agentic-ai-engineering-course/).

**About API costs:** Most labs call real AI models, which costs a little money. Put your keys in a `.env` file at the repo root and never commit it. If you'd rather not spend much, the guides show cheaper and free alternatives (Ollama, DeepSeek, Gemini).

---

## How to use these tutorials

Each week doc is a **walkthrough**, not a spec sheet. Read it once before the week starts, then keep it open while you work through the labs.

Every week follows the same rhythm:
- **Daily labs** — notebooks named `1_lab1.ipynb`, `2_lab2.ipynb`, and so on
- **A capstone** — a bigger project you build across several days
- **Community contributions** — optional student projects for inspiration

When you hit a word you don't know, check the glossary below. When you wonder *why* we're using a particular tool this week and not last week, each tutorial has a section called **"The tools behind this week"** that explains exactly that in plain language.

---

## A small glossary (we'll reuse these words a lot)

**LLM** — the "brain." GPT, Gemini, Claude, and similar models.

**Agent** — an LLM that can *do things*, not just chat. Usually: instructions + tools + a loop.

**Tool** — a function the agent can call: search the web, send an email, read a file.

**Agent loop** — the repeating cycle: think → maybe use a tool → read the result → think again, until done.

**Orchestration** — deciding who runs when. Sometimes you decide in code; sometimes another agent decides.

**MCP** — a standard way for agents to plug into external tools, like USB for AI.

**Structured output** — making the model fill in a form (JSON schema) instead of writing free-form text.

**Guardrail** — a safety check that can stop bad inputs or outputs before they cause harm.

---

## How tools evolve week to week (don't memorize this — just skim)

You'll notice the course reuses the same *ideas* with different *tools* as you progress. That's intentional.

In Week 1 you write the agent loop yourself with a `while` loop. In Week 2, `Runner.run()` does that for you. In Week 3, `crew.kickoff()` runs a whole team. In Week 4, LangGraph draws the flow as a graph. By Week 6, you're composing six MCP tool servers around an agent.

Push notifications appear in Week 1 and never leave — they become email in Week 2, approval pings in Week 4, and trader alerts in Week 6. Gradio shows up in Week 1 for quick demos and evolves into a full FastAPI + Vite dashboard by Week 6.

The point isn't to learn six different worlds. It's to recognize the same patterns wearing different clothes.

---

## If you get stuck

- Ask in the course community on your learning platform
- Email the instructor: ed@edwarddonner.com
- [LinkedIn — Ed Donner](https://www.linkedin.com/in/eddonner/)
- [YouTube — @edward.donner](https://youtube.com/@edward.donner)
- [Course Avatar](https://edwarddonner.com/avatar) — answers common questions

Ready? Start with **[Week 1 — Foundations](./week-01-foundations.md)**. Take it one cell at a time. You've got this.
