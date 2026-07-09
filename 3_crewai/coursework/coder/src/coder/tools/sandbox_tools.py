import subprocess
import time
from pathlib import Path

from crewai.tools import tool

SANDBOX_DIR = Path(__file__).parents[3] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

PODMAN_IMAGE = "python:3.13-slim"
PODMAN_MAX_ATTEMPTS = 5
PODMAN_RETRY_DELAY_SEC = 3
PODMAN_MACHINE_START_TIMEOUT_SEC = 120
PODMAN_MACHINE_POLL_SEC = 3
RUN_TIMEOUT_SEC = 180

_write_used = False


def _never_cache(*_args, **_kwargs) -> bool:
    return False


def _podman_info_ok() -> bool:
    result = subprocess.run(
        ["podman", "info"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode == 0


def _ensure_podman_ready() -> tuple[bool, str]:
    """Ensure Podman is reachable; start podman machine on macOS/Windows if needed."""
    if _podman_info_ok():
        return True, "Podman is ready."

    start = subprocess.run(
        ["podman", "machine", "start"],
        capture_output=True,
        text=True,
        timeout=PODMAN_MACHINE_START_TIMEOUT_SEC,
    )
    start_msg = (start.stderr or start.stdout or "").strip()
    if start.returncode != 0 and not _podman_info_ok():
        return False, start_msg or "podman machine start failed"

    deadline = time.monotonic() + PODMAN_MACHINE_START_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if _podman_info_ok():
            return True, "Podman machine is up."
        time.sleep(PODMAN_MACHINE_POLL_SEC)

    return False, "Timed out waiting for Podman after podman machine start."


def _is_retryable_podman_error(result: subprocess.CompletedProcess[str]) -> bool:
    if result.returncode == 0:
        return False
    combined = f"{result.stderr or ''}\n{result.stdout or ''}".lower()
    markers = (
        "cannot connect to podman",
        "connection refused",
        "unable to connect to podman",
        "podman socket",
        "podman machine",
        "error: unable to connect",
        "failed to connect",
    )
    return any(marker in combined for marker in markers)


def _format_run_result(
    *,
    status: str,
    attempt: int,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    note: str = "",
) -> str:
    lines = [
        status,
        f"attempt: {attempt}/{PODMAN_MAX_ATTEMPTS}",
        f"exit_code: {exit_code if exit_code is not None else 'n/a'}",
        "stdout:",
        stdout.rstrip() if stdout else "(empty)",
        "stderr:",
        stderr.rstrip() if stderr else "(empty)",
    ]
    if note:
        lines.append(f"note: {note}")
    return "\n".join(lines)


def _run_podman_python(filename: str) -> str:
    """Run a sandbox Python file in Podman, retrying infra errors without LLM involvement."""
    ready, ready_msg = _ensure_podman_ready()
    if not ready:
        return _format_run_result(
            status="FAILED",
            attempt=0,
            exit_code=None,
            stdout="",
            stderr=ready_msg,
            note="Could not start Podman machine.",
        )

    last_stdout = ""
    last_stderr = ""
    last_exit: int | None = None

    for attempt in range(1, PODMAN_MAX_ATTEMPTS + 1):
        if attempt > 1:
            ready, ready_msg = _ensure_podman_ready()
            if not ready:
                last_stderr = ready_msg
                time.sleep(PODMAN_RETRY_DELAY_SEC)
                continue

        try:
            result = subprocess.run(
                [
                    "podman", "run", "--rm",
                    "-v", f"{SANDBOX_DIR}:/workspace",
                    "-w", "/workspace",
                    PODMAN_IMAGE,
                    "python", filename,
                ],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT_SEC,
            )
            last_stdout = result.stdout or ""
            last_stderr = result.stderr or ""
            last_exit = result.returncode

            if result.returncode == 0:
                return _format_run_result(
                    status="SUCCESS",
                    attempt=attempt,
                    exit_code=result.returncode,
                    stdout=last_stdout,
                    stderr=last_stderr,
                )

            if not _is_retryable_podman_error(result):
                return _format_run_result(
                    status="FAILED",
                    attempt=attempt,
                    exit_code=result.returncode,
                    stdout=last_stdout,
                    stderr=last_stderr,
                    note="Python/script error — not retried. Fix the file content.",
                )

        except subprocess.TimeoutExpired as exc:
            last_stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            last_stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            last_exit = None
            if attempt < PODMAN_MAX_ATTEMPTS:
                time.sleep(PODMAN_RETRY_DELAY_SEC)
                continue
            return _format_run_result(
                status="FAILED",
                attempt=attempt,
                exit_code=None,
                stdout=last_stdout,
                stderr=last_stderr or f"Timed out after {RUN_TIMEOUT_SEC}s",
                note="Podman run timed out on final attempt.",
            )

        if attempt < PODMAN_MAX_ATTEMPTS:
            time.sleep(PODMAN_RETRY_DELAY_SEC)
            continue

    return _format_run_result(
        status="FAILED",
        attempt=PODMAN_MAX_ATTEMPTS,
        exit_code=last_exit,
        stdout=last_stdout,
        stderr=last_stderr,
        note="Podman unavailable after all retries. Check podman machine status.",
    )


@tool("Check Sandbox Directory")
def check_sandbox_directory() -> str:
    """
    Verify the sandbox directory exists and is ready for read/write.

    Returns:
        Status message with the absolute sandbox path.
    """
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    if not SANDBOX_DIR.is_dir():
        return f"ERROR: Sandbox directory missing: {SANDBOX_DIR}"
    probe = SANDBOX_DIR / ".write_probe"
    probe.write_text("ok")
    probe.unlink(missing_ok=True)
    return f"Sandbox directory exists and is writable: {SANDBOX_DIR}"


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """
    List the filenames currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames, or a message if the sandbox is empty.
    """
    names = sorted(p.name for p in SANDBOX_DIR.iterdir() if p.is_file())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """
    Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "solution.py").
    Returns:
        The file's contents, or a message if the file does not exist.
    """
    path = SANDBOX_DIR / filename
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text()


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """
    Write text to a file in the sandbox directory exactly once per crew run.
    A second call is rejected — fix your code before the single write.

    Args:
        filename: The name of the file to write (e.g. "solution.py").
        content: The text content to write.
    Returns:
        A confirmation message, or an error if write was already used.
    """
    global _write_used
    if _write_used:
        return (
            "ERROR: Write Sandbox File already used once this run. "
            "Do not call this tool again. Use Run Sandbox Python File on the existing file."
        )
    path = SANDBOX_DIR / filename
    path.write_text(content)
    _write_used = True
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """
    Execute a Python file from the sandbox directory inside Podman.
    Ensures the Podman machine is running (starts it if needed), then runs the script.
    Retries Podman infrastructure failures internally (no extra LLM calls).

    Args:
        filename: The name of the Python file to run (e.g. "solution.py").
    Returns:
        SUCCESS or FAILED with exit_code, stdout, and stderr.
    """
    path = SANDBOX_DIR / filename
    if not path.is_file():
        return f"ERROR: No such file in the sandbox: {filename}"
    return _run_podman_python(filename)


sandbox_tools = [
    check_sandbox_directory,
    list_sandbox_files,
    read_sandbox_file,
    write_sandbox_file,
    run_sandbox_python,
]

for _t in sandbox_tools:
    _t.cache_function = _never_cache
