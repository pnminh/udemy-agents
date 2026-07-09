"""Sandbox tools for the engineering team crew.

Podman readiness and retries run inside tools (no extra LLM turns).
Call prepare_sandbox_for_crew() from main before kickoff so agents start with a
ready sandbox and Podman already verified.
"""

import shutil
import subprocess
import time
from pathlib import Path

from crewai.tools import tool

SANDBOX_DIR = Path(__file__).resolve().parents[3] / "sandbox"
PODMAN_IMAGE = "ghcr.io/astral-sh/uv:python3.13-bookworm-slim"
PODMAN_RETRIES = 5
PODMAN_RETRY_DELAY = 3
MAX_WRITES = 10

_write_count = 0


def reset_write_budget() -> None:
    global _write_count
    _write_count = 0


def reset_sandbox() -> None:
    """Remove sandbox/ and recreate with uv init + gradio."""
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["uv", "init", "--bare", "--python", "3.13"],
        cwd=SANDBOX_DIR,
        check=True,
        capture_output=True,
    )
    subprocess.run(["uv", "add", "gradio"], cwd=SANDBOX_DIR, check=True, capture_output=True)


def _ensure_podman_ready() -> str:
    """Start Podman machine if needed and wait until podman info succeeds."""
    try:
        subprocess.run(["podman", "info"], check=True, capture_output=True, text=True)
        return "Podman is ready."
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        subprocess.run(["podman", "machine", "start"], check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return "ERROR: podman not found on PATH."

    for _ in range(30):
        try:
            subprocess.run(["podman", "info"], check=True, capture_output=True, text=True)
            return "Podman machine started and ready."
        except (subprocess.CalledProcessError, FileNotFoundError):
            time.sleep(2)

    return "ERROR: Podman did not become ready in time."


def _check_sandbox_directory() -> str:
    if not SANDBOX_DIR.exists():
        return f"ERROR: Sandbox directory missing at {SANDBOX_DIR}"
    if not (SANDBOX_DIR / "pyproject.toml").exists():
        return "ERROR: Sandbox missing pyproject.toml — run reset_sandbox first."
    return f"Sandbox ready at {SANDBOX_DIR} (pyproject.toml present)."


def prepare_sandbox_for_crew() -> dict[str, str]:
    """Reset sandbox, verify layout, and ensure Podman before any LLM work."""
    reset_sandbox()
    reset_write_budget()
    return {
        "sandbox_status": _check_sandbox_directory(),
        "podman_status": _ensure_podman_ready(),
    }


def _run_podman_python(script_name: str) -> str:
    """Run a Python script in the sandbox via Podman+uv with internal retries."""
    script_path = SANDBOX_DIR / script_name
    if not script_path.exists():
        return f"ERROR: Script not found: {script_name}"

    last_error = ""
    for attempt in range(1, PODMAN_RETRIES + 1):
        try:
            result = subprocess.run(
                [
                    "podman",
                    "run",
                    "--rm",
                    "-v",
                    f"{SANDBOX_DIR.resolve()}:/sandbox:Z",
                    "-w",
                    "/sandbox",
                    PODMAN_IMAGE,
                    "uv",
                    "run",
                    script_name,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            if result.returncode == 0:
                return (
                    f"SUCCESS (exit_code=0)\n"
                    f"stdout:\n{stdout or '(empty)'}\n"
                    f"stderr:\n{stderr or '(empty)'}"
                )
            last_error = (
                f"FAILED (exit_code={result.returncode}, attempt {attempt}/{PODMAN_RETRIES})\n"
                f"stdout:\n{stdout or '(empty)'}\n"
                f"stderr:\n{stderr or '(empty)'}"
            )
        except subprocess.TimeoutExpired:
            last_error = f"FAILED: timeout on attempt {attempt}/{PODMAN_RETRIES}"
        except Exception as exc:
            last_error = f"FAILED: {exc} on attempt {attempt}/{PODMAN_RETRIES}"

        if attempt < PODMAN_RETRIES:
            time.sleep(PODMAN_RETRY_DELAY)

    return last_error


@tool("Check Sandbox Directory")
def check_sandbox_directory() -> str:
    """Verify the sandbox directory exists and has pyproject.toml. Call this first."""
    return _check_sandbox_directory()


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """List all files in the sandbox directory."""
    if not SANDBOX_DIR.exists():
        return f"ERROR: Sandbox directory not found at {SANDBOX_DIR}"
    files = sorted(str(p.relative_to(SANDBOX_DIR)) for p in SANDBOX_DIR.rglob("*") if p.is_file())
    if not files:
        return "Sandbox is empty (no files yet)."
    return "Sandbox files:\n" + "\n".join(files)


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """Read the contents of a file in the sandbox directory."""
    filepath = SANDBOX_DIR / filename
    if not filepath.exists():
        return f"ERROR: File not found: {filename}"
    return filepath.read_text()


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """Write content to a file in the sandbox. Limited write budget — one write per file."""
    global _write_count
    if _write_count >= MAX_WRITES:
        return (
            f"ERROR: Write budget exhausted ({MAX_WRITES} writes). "
            "Do not rewrite files; fix issues with Run Sandbox Python File or report failure."
        )
    filepath = SANDBOX_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)
    _write_count += 1
    remaining = MAX_WRITES - _write_count
    return f"Wrote {filename} ({remaining} writes remaining)."


@tool("Run Sandbox Python File")
def run_sandbox_python_file(script_name: str) -> str:
    """Run a Python script in the sandbox using Podman+uv. Retries happen inside the tool."""
    podman_status = _ensure_podman_ready()
    if podman_status.startswith("ERROR"):
        return podman_status
    return _run_podman_python(script_name)


sandbox_tools = [
    check_sandbox_directory,
    list_sandbox_files,
    read_sandbox_file,
    write_sandbox_file,
    run_sandbox_python_file,
]


def _never_cache(*_args, **_kwargs) -> bool:
    return False


for _t in sandbox_tools:
    _t.cache_function = _never_cache
