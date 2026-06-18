import json
import os

import matplotlib

matplotlib.use("Agg")
import gradio as gr
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Configuration – pick up API key and base URL from environment
# ---------------------------------------------------------------------------
API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_OPEN_API_ENDPOINT") or "https://api.openai.com/v1"

if not API_KEY:
    raise RuntimeError(
        "Missing API key. Set DEEPSEEK_API_KEY or OPENAI_API_KEY in your .env file."
    )

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
MODEL = os.getenv("MODEL", "deepseek-v4-flash")

# ---------------------------------------------------------------------------
# Generate 5 numbered placeholder images (only once)
# ---------------------------------------------------------------------------
PICTURES_DIR = os.path.join(os.path.dirname(__file__), "pictures")
os.makedirs(PICTURES_DIR, exist_ok=True)

COLORS = ["#E6194B", "#3CB44B", "#FFE119", "#4363D8", "#F58231"]

for num in range(1, 6):
    path = os.path.join(PICTURES_DIR, f"{num}.png")
    if os.path.exists(path):
        continue
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    bg_color = COLORS[num - 1]
    ax.set_facecolor(bg_color)
    ax.text(
        0.5,
        0.5,
        str(num),
        fontsize=100,
        ha="center",
        va="center",
        fontweight="bold",
        color="white",
    )
    fig.savefig(path, bbox_inches="tight", pad_inches=0.2, facecolor=bg_color)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Tool definition (JSON schema format)
# ---------------------------------------------------------------------------
show_picture_schema = {
    "name": "show_picture",
    "description": "Show the picture corresponding to the given number (1-5 only).",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "The picture number to display (must be between 1 and 5).",
            }
        },
        "required": ["number"],
        "additionalProperties": False,
    },
}

tools = [{"type": "function", "function": show_picture_schema}]


def show_picture(number: int) -> str:
    """Validate the number and return the result."""
    if number < 1 or number > 5:
        return json.dumps(
            {
                "valid": False,
                "message": f"{number} is not a valid number. Please choose a number between 1 and 5.",
            }
        )
    return json.dumps({"valid": True, "number": number})


def handle_tool_call(tool_calls):
    """Execute tool calls and return the result messages."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}({arguments})", flush=True)

        if tool_name == "show_picture":
            result = show_picture(**arguments)
        else:
            result = json.dumps({"error": f"Unknown tool: {tool_name}"})

        results.append(
            {
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id,
            }
        )
    return results


def get_picture_number_from_tool_result(tool_result: str) -> int | None:
    """Extract the picture number from a show_picture tool result, if valid."""
    try:
        data = json.loads(tool_result)
        if data.get("valid"):
            return data["number"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return None


# ---------------------------------------------------------------------------
# Agent logic
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful assistant that shows pictures numbered 1 through 5. "
    "When the user asks to see a picture, call the show_picture tool with the number. "
    "If show_picture returns valid=False, tell the user the number is invalid "
    "and ask them to pick a number between 1 and 5. "
    "If show_picture returns valid=True, tell the user you are showing that picture. "
    "If the user provides something that isn't a number, tell them it's not valid "
    "and ask them to choose a number between 1 and 5."
)


def normalize_history(history: list) -> list:
    """Convert Gradio's chat history to the OpenAI API message format."""
    normalized = []
    for msg in history:
        entry = {"role": msg["role"]}
        content = msg.get("content")
        if isinstance(content, list):
            # Gradio 6 returns content as a list of text blocks
            texts = []
            for block in content:
                if isinstance(block, dict):
                    texts.append(block.get("text", ""))
                elif isinstance(block, str):
                    texts.append(block)
            entry["content"] = " ".join(texts).strip()
        else:
            entry["content"] = (content or "").strip()
        if entry["content"]:
            normalized.append(entry)
    return normalized


def chat(message: str, history: list):
    """Process user input through the agent and return a response + optional image."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *normalize_history(history),
        {"role": "user", "content": message},
    ]

    done = False
    while not done:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )

        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            assistant_msg = response.choices[0].message
            tool_calls = assistant_msg.tool_calls
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "tool_calls": tool_calls,
                }
            )
            tool_results = handle_tool_call(tool_calls)
            messages.extend(tool_results)
        else:
            done = True

    final_content = response.choices[0].message.content or ""

    # Check if any tool result in the last turn had a valid picture number
    picture_num = None
    for msg in reversed(messages):
        if msg["role"] == "tool":
            num = get_picture_number_from_tool_result(msg["content"])
            if num is not None:
                picture_num = num
                break

    if picture_num is not None:
        img_path = os.path.join(PICTURES_DIR, f"{picture_num}.png")
        return final_content, img_path

    return final_content, None


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with gr.Blocks(title="Picture Picker Agent") as demo:
        gr.Markdown("# 🖼️ Picture Picker Agent")
        gr.Markdown(
            'Ask me to show you a picture! Try **"Show me picture 3"** or **"I want to see number 1"**.'
        )

        chatbot = gr.Chatbot(label="Conversation")
        msg = gr.Textbox(
            label="Your message", placeholder="e.g. Show me picture 3", scale=3
        )
        btn = gr.Button("Send", variant="primary", scale=1)

        with gr.Row():
            image_display = gr.Image(label="Picture", height=300, width=300)

        def respond(user_msg, chat_history):
            bot_msg, img = chat(user_msg, chat_history)
            chat_history.append({"role": "user", "content": user_msg})
            chat_history.append({"role": "assistant", "content": bot_msg})
            return chat_history, img

        msg.submit(respond, [msg, chatbot], [chatbot, image_display])
        btn.click(respond, [msg, chatbot], [chatbot, image_display])

    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
