from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """Load repo-root .env first, then app-local overrides."""
    app_root = Path(__file__).resolve().parents[2]
    agents_root = app_root.parent.parent.parent
    # override=True so repo-root values win over placeholders already in os.environ
    # (e.g. from the shell or an early .env load before main.py runs)
    load_dotenv(agents_root / ".env", override=True)
    load_dotenv(app_root / ".env", override=True)
