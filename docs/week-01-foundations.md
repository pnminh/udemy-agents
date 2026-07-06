# Week 1 Tutorial: Foundations — Talk to a Model, Then Teach It to Act

**Code folder:** [`1_foundations/`](../1_foundations/)

Welcome to Week 1. This is where everyone starts — including people who go on to build production agent systems.

This week you will **not** use a fancy agent framework. That's on purpose. You'll talk to a language model with plain Python, chain a few calls together, build a chatbot that sounds like you, give it tools, and deploy it to the internet. When Week 2 hands you a framework, you'll know exactly what it's doing under the hood — because you already built it yourself.

Your capstone project is the **Digital Twin**: a website chatbot that represents you, answers questions about your career, captures visitor emails, and pings your phone when it gets stumped.

---

## What this week feels like

Day 1 is "hello world" with a model. Day 2 is "wait, I can use *many* models?" Days 3–4 are the real meat: building an agent loop by hand. Day 5 (optional extra) shows the same loop with a visible checklist in the terminal.

If anything feels slow, trust the process. The slowness *is* the lesson.

---

## Day 1 — Your first conversation with a model

Open [`1_lab1.ipynb`](../1_foundations/1_lab1.ipynb) and work through it cell by cell.

You'll load a `.env` file (where your API keys live), create an OpenAI client, and send a simple message. Then you'll chain three calls together: generate a hard question, answer it, evaluate the answer. That's already a tiny agentic pipeline — three specialists in a row, even though it's just you calling the API three times.

There's also an alternate notebook, [`1_lab1_vertex_gemini.ipynb`](../1_foundations/1_lab1_vertex_gemini.ipynb), if you prefer Google Gemini on Vertex AI with `gcloud` login instead of an API key. Same lab, different front door.

**Try this yourself:** The exercise at the end asks you to build a 3-step business consultant: pick an industry, identify a pain point, propose an agentic solution. It's good practice for chaining calls.

---

## Day 2 — Ask five experts, pick the best answer

Open [`2_lab2.ipynb`](../1_foundations/2_lab2.ipynb).

Here's the idea: one model might be wrong, but five models plus a judge? Much harder to fool. You'll send the same prompt to OpenAI, Anthropic, Gemini, DeepSeek, Groq, and others — all using the **same Python library** with different web addresses. Then a "judge" model ranks the answers.

This matters for the whole course. You're not married to OpenAI. Models are interchangeable if you know the pattern.

You'll also meet **Ollama** — run models locally on your laptop for free. Slower, private, and perfect for experimenting without spending money.

---

## Days 3–4 — Build your Digital Twin

This is the heart of Week 1. Open [`3_lab3.ipynb`](../1_foundations/3_lab3.ipynb) and [`4_lab4.ipynb`](../1_foundations/4_lab4.ipynb).

You'll export your LinkedIn profile as a PDF, extract the text, combine it with a short bio you write in `summary.txt`, and inject all of that into a **system prompt** — the model's standing instructions about who it is and what it knows.

Then you'll wrap it in **Gradio**, a Python library that turns your script into a chat website in minutes. No HTML required.

Next comes the big idea: **tools**. You teach the model to call Python functions — record a visitor's email, send you a push notification when it can't answer a question. The model decides *when* to call them; your code *runs* them.

The **agent loop** looks like this in plain English:

1. Send the user's message to the model (with tool definitions attached).
2. If the model says "I want to use a tool," run that tool and send the result back.
3. Repeat until the model gives a normal text answer.
4. Show that answer to the user.

In code, that's a `while` loop checking `finish_reason == "tool_calls"`. Every framework in later weeks implements this same loop. You're writing the original.

By Day 4, you'll refactor the notebook into proper Python files in the [`twin/`](../1_foundations/twin/) folder and deploy to **HuggingFace Spaces** — a free hosting platform. Share the link. That's a real agent on the internet.

---

## Optional extra — Watch the agent think

[`5_extra.ipynb`](../1_foundations/5_extra.ipynb) rebuilds the loop with a terminal UI (Rich library) and checklist tools. The agent writes a to-do list, crosses items off one by one, and you watch it work. Great for building intuition about "planning" before frameworks do it automatically.

---

## The tools behind this week (and why not earlier or later)

Let me walk you through every major tool Week 1 introduces, in the order you'll actually meet it.

### Python and Jupyter notebooks

You'll work in `.ipynb` notebook files — run one cell, see the result, run the next. It's like a lab workbook where the experiments are live. We use notebooks in Week 1 because you need to *see* every step. Nothing is hidden inside a library.

Later weeks shift capstone code into `.py` files when you're ready to deploy. Notebooks are for learning; modules are for shipping.

### The `.env` file and python-dotenv

Before anything fun, you need a safe place for secrets. Your API keys go in a file called `.env` at the repo root. The `python-dotenv` library loads them when your code starts. Git ignores this file so you never accidentally publish your keys.

You'll use `.env` every week for the rest of the course. Week 1 is where the habit starts.

### The OpenAI Python SDK

This small library turns `openai.chat.completions.create(...)` into a web request and gives you back the model's reply. Here's the thing most beginners miss: **the library doesn't contain GPT**. It's a messenger. It calls someone's server and returns the answer.

This one function call is the foundation of the entire course:

```python
response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Week 2's `Runner.run()`, Week 3's crews, Week 4's LangGraph — they all eventually boil down to this. Learning it now saves you confusion later.

**Why not jump straight to a framework?** Because when something breaks in Week 4, you'll want to know whether the bug is in the framework or in the underlying model call. Week 1 teaches you to tell the difference.

### OpenAI-compatible APIs (Lab 2)

Many companies built their APIs to look like OpenAI's on purpose. Same Python code, different address:

```python
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

We teach this in Week 1 — not Week 5 — because you should feel free to swap models early. DeepSeek is cheap. Ollama is free and local. Gemini has a generous free tier. You're not locked in.

The trade-off: each provider names models differently and has its own limits. Frameworks help a bit, but never perfectly.

### Gradio

Gradio builds a chat UI from Python. Your Digital Twin needs a face — something you can send to a friend or put on your résumé. Gradio gets you there in an afternoon.

You'll meet Gradio again in Weeks 2, 4, and 6. It's always the "get a demo running fast" choice. When you need custom charts and a polished product UI (Week 6), you'll graduate to something heavier. But Gradio is the right tool for Week 1's "I built something real" moment.

### PyPDF

Your LinkedIn export arrives as a PDF. PyPDF pulls plain text out of it so the model can read your career history. This is the simplest possible version of "give the model context about you" — no vector database, no fancy retrieval. Just: here is text, read it.

That works for one document. If you had five hundred PDFs, you'd need the retrieval techniques from Week 4. Week 1 keeps it simple on purpose.

### Pushover

Pushover sends notifications to your phone. When a visitor asks your Digital Twin something it can't answer, your pocket buzzes. That small detail transforms the project from "cool demo" into "actually useful."

Agents that only print text feel like toys. Agents that *reach out to you* feel like colleagues. Pushover comes back in Weeks 2, 4, and 6 for the same reason.

### HuggingFace Spaces

Spaces hosts your Gradio app in the cloud for free. You push code, they give you a URL. Week 1 is your first deployment — a portfolio piece you can share in a job interview.

Running locally is fine for development. Spaces is how you show the world.

### asyncio (Lab 2)

When you ask five models the same question, waiting for each one sequentially is painful. Python's `asyncio` lets them run at the same time. Same idea returns in Week 2 when multiple search agents run in parallel — you'll recognize it.

---

## How Week 1 compares to what comes next

Week 1 is the **manual transmission** of agent building. You control every gear. That's slower, but you learn exactly how the car works.

Week 2 gives you an automatic transmission (`Runner.run()`). Week 3 gives you a whole team with job descriptions (CrewAI). Week 4 lets you draw the workflow as a flowchart (LangGraph). Week 5 shows you six brands of transmission that all shift the same way. Week 6 plugs in a universal tool belt (MCP).

None of those weeks replace Week 1. They assume you already understand the loop.

| If you want to… | Week 1 is… |
|-----------------|------------|
| Understand what's really happening | ✅ The best week |
| Build fast with many agents | ❌ Too much manual work — try Week 2 or 3 |
| Browse the web automatically | ❌ Not yet — Week 2 adds search |
| Deploy something shareable | ✅ Digital Twin on HuggingFace |

---

## Your capstone checklist

By the end of Week 1, you should have:

- [ ] A `.env` file with your API keys (not committed to git)
- [ ] Run all core lab notebooks through Lab 4
- [ ] A `summary.txt` and LinkedIn PDF feeding your Digital Twin's system prompt
- [ ] Tools that record emails and notify you via Pushover
- [ ] The [`twin/`](../1_foundations/twin/) app deployed to HuggingFace Spaces

**Stretch goals:** Add a vector database for richer context. Connect Telegram instead of Pushover. Rebuild the checklist agent from `5_extra.ipynb` from scratch without looking.

---

## When you're ready

Move on to **[Week 2 — OpenAI Agents SDK](./week-02-openai-agents-sdk.md)**. You'll rebuild much of what you just built — but faster, with a framework. And because you wrote the loop by hand, you'll feel the difference immediately.
