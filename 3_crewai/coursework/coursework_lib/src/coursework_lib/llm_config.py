import os
import subprocess
from functools import lru_cache
from typing import Literal

from crewai import LLM

Provider = Literal["gemini", "deepseek"]

DEFAULT_GEMINI_MODEL = "gemini/gemini-3.1-pro-preview"
DEFAULT_DEEPSEEK_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_GEMINI_LOCATION = "global"
DEFAULT_GCP_PROJECT = "your-gcp-project-id"
DEFAULT_DEEPSEEK_API_KEY = "your-deepseek-api-key"


def get_llm_provider() -> Provider:
    provider = (
        os.getenv("COURSEWORK_LLM_PROVIDER")
        or os.getenv("DEBATE_LLM_PROVIDER")
        or "gemini"
    ).strip().lower()
    if provider not in ("gemini", "deepseek"):
        raise ValueError(
            f"Unsupported COURSEWORK_LLM_PROVIDER={provider!r}. "
            "Use 'gemini' or 'deepseek'."
        )
    return provider  # type: ignore[return-value]


def _gcloud_project() -> str | None:
    try:
        return subprocess.check_output(
            ["gcloud", "config", "get-value", "project"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _resolve_gcp_project() -> str:
    return (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
        or _gcloud_project()
        or DEFAULT_GCP_PROJECT
    )


def _configure_vertex_adc() -> None:
    """Vertex ADC auth fails if a Gemini API key is also present in the environment."""
    for key in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        os.environ.pop(key, None)


def _build_gemini_llm() -> LLM:
    _configure_vertex_adc()
    return LLM(
        model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        project=_resolve_gcp_project(),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", DEFAULT_GEMINI_LOCATION),
    )


def _build_deepseek_llm() -> LLM:
    return LLM(
        model=os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
        api_key=os.getenv("DEEPSEEK_API_KEY", DEFAULT_DEEPSEEK_API_KEY),
    )


@lru_cache(maxsize=2)
def get_llm(provider: str | None = None) -> LLM:
    selected = (provider or get_llm_provider()).lower()
    if selected == "gemini":
        return _build_gemini_llm()
    if selected == "deepseek":
        return _build_deepseek_llm()
    raise ValueError(
        f"Unsupported LLM provider {selected!r}. Use 'gemini' or 'deepseek'."
    )
