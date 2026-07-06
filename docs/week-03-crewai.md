# Week 3 Tutorial: CrewAI — Build a Team, Not a Solo Agent

**Code folder:** [`3_crewai/`](../3_crewai/)

So far you've built individual agents — one brain, one loop. This week you run a **team**.

**CrewAI** lets you define agents with job titles in YAML files, assign them tasks, and run the whole crew with one command. You're the director; CrewAI handles the handoffs.

By the end you'll progress from a simple debate crew to a four-engineer software team that writes code in Docker sandboxes. Your own projects go in [`coursework/`](../3_crewai/coursework/); study the instructor versions in [`reference/`](../3_crewai/reference/).

---

## What this week feels like

Imagine staffing a small company. You write job descriptions (`agents.yaml`), define deliverables (`tasks.yaml`), and hire a manager to run sequential or hierarchical workflows. Day one is a debate club. By week's end, you're running a mini software agency.

---

## Getting set up

From the repo root:

```bash
uv tool install crewai==1.14.4
uv tool list   # confirm the version
```

Windows users: install MS Build Tools first (see [`3_crewai/README.md`](../3_crewai/README.md)) or installation may fail.

For the advanced projects (`coder`, `engineering_team`), install and start **Docker Desktop**. The agents run code inside containers so a hallucinated `rm -rf` doesn't touch your laptop.

Optional but helpful for Cursor:

```bash
npx skills add crewaiinc/skills
```

Create your own project:

```bash
cd 3_crewai
crewai create crew my_project_name
```

Copy prompts from `reference/` into `coursework/` to save time, then customize.

---

## How a CrewAI project is organized

Every project follows the same shape — learn it once, reuse forever:

- **`agents.yaml`** — who is on the team (role, goal, backstory)
- **`tasks.yaml`** — what they must deliver (description, expected output, which agent)
- **`crew.py`** — Python wiring with `@CrewBase`, `@agent`, `@task`, `@crew`
- **`main.py`** — entry point; calls `crew.kickoff(inputs={"motion": "..."})`
- **`.env`** — API keys

Placeholders like `{company}` in YAML get replaced at runtime from the inputs dict you pass to `kickoff()`.

Run everything with:

```bash
crewai run
```

---

## Walk through the reference projects (easiest → hardest)

### Start here: Debate

[`reference/debate/`](../3_crewai/reference/debate/)

Two agents — a debater and a judge — and three sequential tasks: argue for, argue against, decide winner. You type a motion; the crew writes `output/propose.md`, `oppose.md`, and `decide.md`.

Run it. Read the YAML. Change the motion to something fun ("AI should replace all managers"). This is your template for everything else.

### Researcher

Two agents: one gathers ten bullet points on a topic, another expands them into a markdown report. Introduces writing output to files.

### Financial Researcher

Adds **live web search** via SerperDevTool. The analyst's report task uses **context** from the research task — meaning it automatically receives the researcher's output without you writing plumbing code.

You'll need `SERPER_API_KEY` in `.env`.

### Stock Picker

The "production patterns" reference before the engineering capstone:
- **Hierarchical process** — a manager delegates to specialists
- **Structured outputs** via `output_pydantic`
- **Crew memory** across tasks
- **Push notification** when a stock is picked

### Coder

One agent writes Python, runs it in **Docker**, reads the output, fixes errors, repeats. Requires Docker running.

### Engineering Team — the capstone

Four agents build a real app from a one-line requirement: lead designs (with Context7 MCP for live docs), backend engineer writes Python, frontend engineer builds Gradio UI, test engineer writes unit tests until green. Shared Docker sandbox.

Study this one carefully. It's the closest thing in the course to "agents building software."

---

## The tools behind this week

### Why CrewAI in Week 3, not Week 2?

Week 2 taught you to orchestrate agents in **Python code** — explicit, flexible, great for custom pipelines. CrewAI shines when work naturally splits into **roles**: researcher → analyst, debater → judge, lead → engineers.

If your workflow sounds like a meeting agenda with named attendees, CrewAI is probably faster than writing orchestration code.

If your workflow sounds like "if search fails, retry three times then branch left," LangGraph (Week 4) is a better fit.

### YAML config — job postings on paper

Separating prompts from Python means you can tweak an agent's personality without hunting through code. Product managers can review YAML. Developers wire tools in `crew.py`.

The trade-off: complex branching logic gets awkward in YAML. Keep crews focused.

### SerperDevTool — Google search for your agents

Week 2 used OpenAI's hosted WebSearchTool — convenient but tied to OpenAI. CrewAI uses **Serper**, a Google search API that works with whatever LLM you configure. One more API key, but you're not locked in.

Serper also powers Sidekick's search in Week 4 and complements Tavily in Week 6. Same family of tool, different weeks.

### Task context — passing the baton

When `reporting_task` lists `context: [research_task]`, CrewAI automatically feeds the research output into the report task. Week 2 did this manually in Python. Week 3 declares it.

### Docker sandbox — don't let agents run code on your laptop

Letting an LLM execute arbitrary Python on your machine is risky. Docker is a walled garden — the agent writes files and runs commands inside a container. Your personal files stay safe.

First run downloads images; be patient. This is heavier than Week 5–6 MCP filesystem tools, which isolate files but don't execute code.

### Context7 MCP — your first taste of MCP

The engineering lead connects to **Context7**, an MCP server that fetches live library documentation. Agents hallucinate API signatures constantly; live docs help.

Week 5 uses MCP for filesystem access in every framework. Week 6 goes all-in — building and composing six servers. Week 3 is the gentle introduction.

### Pluggable LLMs

CrewAI agents accept different models via the `llm=` parameter. Your coursework debate project can switch between Gemini on Vertex and DeepSeek with an environment variable. Same lesson as Week 1 Lab 2, now inside a crew.

---

## CrewAI vs what you already know

**Compared to Week 1:** You don't write the loop. You don't write tool schemas by hand. You define a team and run `kickoff()`.

**Compared to Week 2:** Less fine-grained control over exact call order. More natural for role-based workflows. No OpenAI hosted tools or native OpenAI traces — use CrewAI tracing (`tracing=True`, login via `crewai login`) instead.

**Compared to Week 4:** CrewAI is higher-level and YAML-first. LangGraph gives you graph nodes, conditional edges, and human-in-the-loop pauses. Use CrewAI when the workflow is "A then B then C." Use LangGraph when it's "A, then maybe B or C depending on what happened."

---

## Your checklist

- [ ] CrewAI 1.14.4 installed
- [ ] Debate reference running (`crewai run`)
- [ ] At least one project in `coursework/` started
- [ ] Understand sequential vs hierarchical process
- [ ] Optional: Stock Picker or Engineering Team with Docker

---

## When you're ready

Continue to **[Week 4 — LangChain & LangGraph](./week-04-langchain-langgraph.md)** — time to look under the hood again and build Sidekick.
