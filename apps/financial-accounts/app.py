import contextlib
import getpass
import io
import json
import os
import pickle
import queue
import threading

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
SESSION_STORAGE = os.path.join(SESSION_DIR, ".robinhood_session")
PICKLE_FILE = os.path.join(SESSION_STORAGE, "robinhood.pickle")

robin_stocks_logged_in = False
logged_in_email: str | None = None

print("🔧 Checking for stored session...", flush=True)
print(f"   Storage dir: {SESSION_STORAGE}", flush=True)
print(f"   Pickle file: {PICKLE_FILE}", flush=True)

if os.path.exists(SESSION_STORAGE):
    print("   SESSION_STORAGE exists", flush=True)
    if os.path.isfile(SESSION_STORAGE):
        # Old format — was stored as a single file, now it's a directory
        print("   Removing old single-file session", flush=True)
        os.remove(SESSION_STORAGE)
        print("   Old session removed", flush=True)
    elif os.path.isdir(SESSION_STORAGE):
        print("   SESSION_STORAGE is a directory", flush=True)
        if os.path.exists(PICKLE_FILE):
            print("   PICKLE_FILE exists, loading...", flush=True)
            try:
                with open(PICKLE_FILE, "rb") as f:
                    auth = pickle.load(f)
                stored_email = (
                    getattr(auth, "username", "pnminh232@gmail.com")
                    or "pnminh232@gmail.com"
                )

                # Use r.login() to fully initialize the session
                old_getpass = getpass.getpass
                getpass.getpass = lambda prompt="": ""
                try:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        r.login(
                            stored_email,
                            "",
                            store_session=True,
                            pickle_path=SESSION_STORAGE,
                        )
                    robin_stocks_logged_in = True
                    logged_in_email = stored_email
                    print(f"✅ Session loaded for {logged_in_email}", flush=True)
                except Exception as e:
                    print(f"⚠️ r.login() failed: {type(e).__name__}: {e}", flush=True)
                    import shutil

                    shutil.rmtree(SESSION_STORAGE)
                    print("   Session removed", flush=True)
                finally:
                    getpass.getpass = old_getpass
            except Exception as e:
                print(f"⚠️ Failed to load pickle: {type(e).__name__}: {e}", flush=True)
                import shutil

                shutil.rmtree(SESSION_STORAGE)
                print("   Corrupted session removed", flush=True)
        else:
            print("   No PICKLE_FILE inside directory", flush=True)
            import shutil

            shutil.rmtree(SESSION_STORAGE)
            print("   Empty session dir removed", flush=True)
else:
    print("   No stored session found", flush=True)

print(f"🔧 Login state: robin_stocks_logged_in={robin_stocks_logged_in}", flush=True)
print(
    f"🔧 UI will show: {'chat' if robin_stocks_logged_in else 'login form'}", flush=True
)


def do_login(email: str, password: str):
    """Attempt Robinhood login. Yields status updates in real-time as they come from robin_stocks."""
    global robin_stocks_logged_in, logged_in_email

    yield "🔄 Connecting to Robinhood..."

    msg_queue: queue.Queue[str | None] = queue.Queue()
    exception_container: list[Exception | None] = []

    class StreamCapture(io.StringIO):
        """Captures writes and pushes each new unique line into the queue in real-time."""

        _last: str = ""

        def write(self, s) -> int:
            stripped = s.strip()
            if stripped and stripped != self._last:
                self._last = stripped
                msg_queue.put(stripped)
            return super().write(s)

        def flush(self):
            pass

    captured_out = StreamCapture()
    captured_err = StreamCapture()

    def target():
        try:
            with (
                contextlib.redirect_stdout(captured_out),
                contextlib.redirect_stderr(captured_err),
            ):
                r.login(
                    email,
                    password,
                    store_session=True,
                    pickle_path=SESSION_STORAGE,
                )
            exception_container.append(None)
        except Exception as e:
            exception_container.append(e)
        finally:
            msg_queue.put(None)  # sentinel — signals we're done

    thread = threading.Thread(target=target, daemon=True)
    thread.start()

    # Read messages from the queue as they arrive (real-time)
    while True:
        try:
            msg = msg_queue.get(timeout=0.3)
            if msg is None:  # sentinel
                break
            # Flush any accumulated content still in the stream
            remaining = captured_out.getvalue().strip()
            if remaining and remaining != msg:
                for line in remaining.split("\n"):
                    line = line.strip()
                    if line and line != msg:
                        yield line
            yield msg
        except queue.Empty:
            if not thread.is_alive():
                # Flush any remaining content
                for s in (captured_out, captured_err):
                    remaining = s.getvalue().strip()
                    if remaining:
                        for line in remaining.split("\n"):
                            line = line.strip()
                            if line:
                                yield line
                break

    if exception_container and exception_container[0] is None:
        robin_stocks_logged_in = True
        logged_in_email = email
        file_exists = os.path.exists(SESSION_STORAGE) and os.path.exists(PICKLE_FILE)
        print(f"🔧 Login success. Session file exists: {file_exists}", flush=True)
        yield f"✅ Logged in as {email}"
    else:
        err = (
            exception_container[0]
            if exception_container
            else Exception("Unknown error")
        )
        yield f"❌ Login failed: {err}"


def expire_session() -> None:
    """Reset auth state and delete stored session when token expires."""
    global robin_stocks_logged_in, logged_in_email
    robin_stocks_logged_in = False
    logged_in_email = None
    import shutil

    if os.path.exists(SESSION_STORAGE):
        shutil.rmtree(SESSION_STORAGE)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
def _is_auth_error(e: Exception) -> bool:
    """Check if an exception is related to expired/invalid authentication."""
    msg = str(e).lower()
    keywords = [
        "401",
        "unauthorized",
        "session expired",
        "authenticate",
        "token expired",
        "access_denied",
        "not authenticated",
    ]
    return any(k in msg for k in keywords)


def _call_or_expire(fn, *args, **kwargs) -> str:
    """Call a robin_stocks function. If it fails with an auth error, expire the session."""
    try:
        result = fn(*args, **kwargs)
        return json.dumps(result) if not isinstance(result, str) else result
    except Exception as e:
        print(f"🔧 API call failed: {type(e).__name__}: {e}", flush=True)
        if _is_auth_error(e):
            print("   → Auth error detected, expiring session", flush=True)
            expire_session()
            return json.dumps({"session_expired": True, "error": str(e)})
        return json.dumps({"error": str(e)})


def get_portfolio_summary() -> str:
    """Return overall portfolio value, buying power, and cash balance."""
    raw = _call_or_expire(r.account.build_user_profile)
    try:
        data = json.loads(raw)
        if "session_expired" in data or "error" in data:
            return raw
        return json.dumps(
            {
                "total_equity": data.get("equity", "N/A"),
                "extended_hours_equity": data.get("extended_hours_equity", "N/A"),
                "buying_power": data.get("buying_power", "N/A"),
                "cash": data.get("cash", "N/A"),
            }
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return raw


def get_holdings() -> str:
    """Return all stock/ETF positions currently held."""
    result = _call_or_expire(r.account.build_holdings)
    # Parse and format the holdings list
    try:
        data = json.loads(result)
        if "session_expired" in data or "error" in data:
            return result
        if not data:
            return json.dumps({"holdings": [], "message": "No positions found."})
        holdings_list = []
        for symbol, info in data.items():
            holdings_list.append(
                {
                    "symbol": symbol,
                    "quantity": float(info.get("quantity", 0)),
                    "avg_buy_price": float(info.get("average_buy_price", 0)),
                    "equity": float(info.get("equity", 0)),
                    "percent_change": float(info.get("percent_change", 0)),
                    "equity_change": float(info.get("equity_change", 0)),
                }
            )
        return json.dumps({"holdings": holdings_list})
    except (json.JSONDecodeError, TypeError, ValueError):
        return result


def get_stock_price(symbol: str) -> str:
    """Get the latest price for a given stock ticker symbol.

    Args:
        symbol: The stock ticker symbol (e.g. AAPL, TSLA, MSFT).
    """
    raw = _call_or_expire(r.stocks.get_latest_price, symbol, includeExtendedHours=False)
    try:
        data = json.loads(raw)
        if isinstance(data, list) and data:
            return json.dumps({"symbol": symbol.upper(), "price": data[0]})
        if isinstance(data, dict) and ("session_expired" in data or "error" in data):
            return raw
        return json.dumps({"error": f"Could not fetch price for {symbol}"})
    except (json.JSONDecodeError, TypeError):
        return raw


def get_account_info() -> str:
    """Return basic stock account information."""
    raw = _call_or_expire(r.profiles.load_account_profile)
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and ("session_expired" in data or "error" in data):
            return raw
        info: dict[str, object] = {
            "email": logged_in_email or "unknown",
        }
        if isinstance(data, dict):
            info["account_number"] = data.get("account_number", "N/A")
            info["status"] = data.get("status", "N/A")
        return json.dumps(info)
    except (json.JSONDecodeError, TypeError):
        return raw


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
    global robin_stocks_logged_in
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

        # Detect session expiry and break out of any further tool calls
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and parsed.get("session_expired"):
                robin_stocks_logged_in = False
        except (json.JSONDecodeError, TypeError):
            pass

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
    "If a tool returns a session_expired error, tell the user their session has expired "
    "and they need to log in again using the login form.\n"
    "If a tool returns an error, simply say the data is currently unavailable."
)


SESSION_EXPIRED_MARKER = "__SESSION_EXPIRED__"


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


def chat(message: str, history: list):
    """Generator. Yields thinking steps, then yields the final response."""
    if not robin_stocks_logged_in:
        yield SESSION_EXPIRED_MARKER
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *normalize_history(history),
        {"role": "user", "content": message},
    ]

    yield "🤔 Thinking..."

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

            # Show agent's reasoning
            if assistant_msg.content:
                yield f"🤔 {assistant_msg.content}"

            # Show each tool being called
            if tool_calls:
                for tc in tool_calls:
                    name = tc.function.name  # type: ignore[union-attr]
                    args = json.loads(tc.function.arguments)  # type: ignore[union-attr]
                    descs = {
                        "get_portfolio_summary": "Fetching portfolio summary...",
                        "get_holdings": "Fetching stock holdings...",
                        "get_stock_price": f"Looking up price for {args.get('symbol', '?')}...",
                        "get_account_info": "Fetching account info...",
                    }
                    yield f"⚙️ {descs.get(name, name)}"

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "tool_calls": tool_calls,
                }
            )
            tool_results = handle_tool_call(tool_calls)
            messages.extend(tool_results)

            # Show tool results
            for tr in tool_results:
                parsed = json.loads(tr["content"])
                if isinstance(parsed, dict):
                    if parsed.get("session_expired"):
                        yield "🔒 Session expired. Please log in again."
                        yield SESSION_EXPIRED_MARKER
                        return
                    if "holdings" in parsed:
                        count = len(parsed["holdings"])
                        yield f"✅ Found {count} position{'s' if count != 1 else ''}"
                    elif "total_equity" in parsed:
                        yield "✅ Portfolio summary retrieved"
                    elif "price" in parsed:
                        yield f"✅ {parsed['symbol']} price: ${parsed['price']}"
                    elif "error" in parsed:
                        yield f"⚠️ {parsed['error']}"
                    else:
                        yield "✅ Done"
                else:
                    yield "✅ Done"
        else:
            break

    final = response.choices[0].message.content or ""
    yield final


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
            status = ""
            for status in do_login(email, password):
                yield (
                    gr.update(visible=not robin_stocks_logged_in),
                    gr.update(visible=robin_stocks_logged_in),
                    status,
                    gr.update(interactive=False),
                )
            # Re-enable button if login failed (form is still visible)
            if not robin_stocks_logged_in:
                yield (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    status,
                    gr.update(interactive=True),
                )

        login_btn.click(
            fn=on_login,
            inputs=[login_email, login_password],
            outputs=[login_box, chat_box, login_status, login_btn],
        )
        login_password.submit(
            fn=on_login,
            inputs=[login_email, login_password],
            outputs=[login_box, chat_box, login_status, login_btn],
        )

        # --- Chat handler ---
        def respond(user_msg, chat_history):
            # Show user message, clear textbox, disable send button
            chat_history.append({"role": "user", "content": user_msg})
            yield (
                chat_history,
                gr.update(value="", interactive=False),
                gr.update(interactive=False),
                gr.update(),
                gr.update(),
            )
            try:
                for step in chat(user_msg, chat_history):
                    if step == SESSION_EXPIRED_MARKER:
                        # Session expired — switch to login form
                        yield (
                            chat_history,
                            gr.update(value="", interactive=True),
                            gr.update(interactive=True),
                            gr.update(visible=True),
                            gr.update(visible=False),
                        )
                        return
                    # Add each thinking step as a new assistant message
                    chat_history.append({"role": "assistant", "content": step})
                    yield (
                        chat_history,
                        gr.update(value="", interactive=True),
                        gr.update(interactive=True),
                        gr.update(),
                        gr.update(),
                    )
            except Exception as e:
                chat_history.append({"role": "assistant", "content": f"❌ Error: {e}"})
                yield (
                    chat_history,
                    gr.update(value="", interactive=True),
                    gr.update(interactive=True),
                    gr.update(),
                    gr.update(),
                )

        msg.submit(respond, [msg, chatbot], [chatbot, msg, btn, login_box, chat_box])
        btn.click(respond, [msg, chatbot], [chatbot, msg, btn, login_box, chat_box])

    demo.queue().launch(server_name="0.0.0.0", server_port=7861, theme=SoftTheme())
