from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """Load repo-root .env first, then debate-local overrides."""
    debate_root = Path(__file__).resolve().parents[2]
    agents_root = debate_root.parent.parent.parent
    load_dotenv(agents_root / ".env")
    load_dotenv(debate_root / ".env", override=True)
