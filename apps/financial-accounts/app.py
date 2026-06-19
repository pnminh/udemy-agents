import json
import os

import gradio as gr
import robin_stocks.robinhood as r
from dotenv import load_dotenv
from gradio.themes import Soft as SoftTheme
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Configuration
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
# Authentication state
# ---------------------------------------------------------------------------
SESSION_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(SESSION_DIR, ".robinhood_session.pickle")

robin_stocks_logged_in = False
logged_in_email: str | None = None

# Try stored session before showing the login form
if os.path.exists(SESSION_FILE):
    env_email = os.getenv("ROBINHOOD_EMAIL")
    try:
        r.login(
            env_email or "",
            "",
            store_session=True,
            pickle_path=SESSION_FILE,
        )
        robin_stocks_logged_in = True
        logged_in_email = env_email
        print("✅ Logged into Robinhood via stored session", flush=True)
    except Exception as e:
        print(f"⚠️  Stored session expired: {e}", flush=True)
        os.remove(SESSION_FILE)


def do_login(email: str, password: str) -> str:
    """Attempt Robinhood login. Returns status message."""
    global robin_stocks_logged_in, logged_in_email
    try:
        r.login(
            email,
            password,
            store_session=True,
            pickle_path=SESSION_FILE,
        )
        robin_stocks_logged_in = True
        logged_in_email = email
        return f"✅ Logged in as {email}"
    except Exception as e:
        return f"❌ Login failed: {e}"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
def get_portfolio_summary() -> str:
    """Return overall portfolio value, buying power, and cash balance."""
    try:
        portfolios = r.account.build_user_profile()
    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps(
        {
            "total_equity": portfolios.get("equity", "N/A"),
            "extended_hours_equity": portfolios.get("extended_hours_equity", "N/A"),
            "buying_power": portfolios.get("buying_power", "N/A"),
            "cash": portfolios.get("cash", "N/A"),
        }
    )


def get_holdings() -> str:
    """Return all stock/ETF positions currently held."""
    try:
        positions = r.account.build_holdings()
    except Exception as e:
        return json.dumps({"error": str(e)})

    if not positions:
        return json.dumps({"holdings": [], "message": "No positions found."})

    holdings_list = []
    for symbol, data in positions.items():
        holdings_list.append(
            {
                "symbol": symbol,
                "quantity": float(data.get("quantity", 0)),
                "avg_buy_price": float(data.get("average_buy_price", 0)),
                "equity": float(data.get("equity", 0)),
                "percent_change": float(data.get("percent_change", 0)),
                "equity_change": float(data.get("equity_change", 0)),
            }
        )

    return json.dumps({"holdings": holdings_list})


def get_stock_price(symbol: str) -> str:
    """Get the latest price for a given stock ticker symbol.

    Args:
        symbol: The stock ticker symbol (e.g. AAPL, TSLA, MSFT).
    """
    try:
        quote = r.stocks.get_latest_price(symbol, includeExtendedHours=False)
        if quote:
            return json.dumps({"symbol": symbol.upper(), "price": quote[0]})
        return json.dumps({"error": f"Could not fetch price for {symbol}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_account_info() -> str:
    """Return basic stock account information."""
    try:
        profile = r.profiles.load_account_profile()
    except Exception as e:
        return json.dumps({"error": str(e)})

    info: dict[str, object] = {
        "email": logged_in_email or "unknown",
    }
    if isinstance(profile, dict):
        info["account_number"] = profile.get("account_number", "N/A")
        info["status"] = profile.get("status", "N/A")

    return json.dumps(info)


# ---------------------------------------------------------------------------
# Tool schema definitions (no authenticate tool — auth is handled in the UI)
# ---------------------------------------------------------------------------
tool_schemas: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_summary",
            "description": "Get the overall stock portfolio summary including total equity, buying power, and cash balance.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_holdings",
            "description": "Get all stock and ETF positions currently held in the portfolio including quantity, average buy price, current equity, and percent change.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the latest price for a given stock ticker symbol (e.g. AAPL, TSLA, MSFT).",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g. AAPL, TSLA, MSFT).",
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_account_info",
            "description": "Get basic stock account information including account number, status, and email.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_DISPATCH = {
    "get_portfolio_summary": get_portfolio_summary,
    "get_holdings": get_holdings,
    "get_stock_price": get_stock_price,
    "get_account_info": get_account_info,
}


def handle_tool_call(tool_calls) -> list[dict]:
    """Execute tool calls and return the result messages."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"🔧 Tool called: {tool_name}({arguments})", flush=True)

        func = TOOL_DISPATCH.get(tool_name)
        if func:
            result = func(**arguments)
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


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful financial assistant with access to the user's Robinhood stock account. "
    "You can answer questions about:\n"
    "- Portfolio summary: total equity, buying power, cash balance\n"
    "- Holdings: detailed list of all stock/ETF positions\n"
    "- Stock prices: current price for any ticker symbol\n"
    "- Account information\n"
    "\n"
    "Be clear and informative. Present financial data in a readable format. "
    "If a tool returns an error, simply say the data is currently unavailable."
)


# ---------------------------------------------------------------------------
# Chat logic
# ---------------------------------------------------------------------------
def normalize_history(history: list) -> list:
    """Convert Gradio's chat history to the OpenAI API message format."""
    normalized = []
    for msg in history:
        entry = {"role": msg["role"]}
        content = msg.get("content")
        if isinstance(content, list):
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


def chat(message: str, history: list) -> str:
    """Process user input through the agent and return a response."""
    if not robin_stocks_logged_in:
        return (
            "I'm not connected to Robinhood right now. "
            "Please log in using the form above first."
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *normalize_history(history),
        {"role": "user", "content": message},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tool_schemas,
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
            break

    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with gr.Blocks(title="Financial Accounts Agent") as demo:
        gr.Markdown("# 💰 Financial Accounts Agent")

        # --- Login section ---
        login_box = gr.Column(visible=not robin_stocks_logged_in)
        with login_box:
            gr.Markdown("### 🔐 Log in to Robinhood")
            login_email = gr.Textbox(label="Email", placeholder="your@email.com")
            login_password = gr.Textbox(
                label="Password", placeholder="********", type="password"
            )
            login_status = gr.Markdown()
            login_btn = gr.Button("Log in", variant="primary")

        # --- Chat section ---
        chat_box = gr.Column(visible=robin_stocks_logged_in)
        with chat_box:
            gr.Markdown(
                "Ask me about your Robinhood stock account! "
                'Try **"How is my portfolio doing?"**, '
                '**"What stocks do I hold?"**, '
                'or **"What is the price of AAPL?"**.'
            )

            chatbot = gr.Chatbot(label="Conversation")
            msg = gr.Textbox(
                label="Your message",
                placeholder="e.g. How is my portfolio doing?",
                scale=3,
            )
            btn = gr.Button("Send", variant="primary", scale=1)

        # --- Login handler ---
        def on_login(email, password):
            status = do_login(email, password)
            if robin_stocks_logged_in:
                return (
                    gr.update(visible=False),  # hide login box
                    gr.update(visible=True),  # show chat box
                    f"✅ Logged in as {email}",
                )
            return (
                gr.update(visible=True),  # keep login box
                gr.update(visible=False),  # keep chat hidden
                f"❌ {status}",
            )

        login_btn.click(
            fn=on_login,
            inputs=[login_email, login_password],
            outputs=[login_box, chat_box, login_status],
        )

        # --- Chat handler ---
        def respond(user_msg, chat_history):
            bot_msg = chat(user_msg, chat_history)
            chat_history.append({"role": "user", "content": user_msg})
            chat_history.append({"role": "assistant", "content": bot_msg})
            return chat_history

        msg.submit(respond, [msg, chatbot], [chatbot])
        btn.click(respond, [msg, chatbot], [chatbot])

    demo.launch(server_name="0.0.0.0", server_port=7861, theme=SoftTheme())
