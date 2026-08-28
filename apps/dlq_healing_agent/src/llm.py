"""LLM provider selection for the DLQ recovery workflow.

The application defaults to OpenAI so existing deployments keep their current
behavior. Local development can select Ollama with environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    base_url: str | None = None


def get_llm_settings() -> LLMSettings:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    if provider == "openai":
        return LLMSettings(
            provider=provider,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    if provider == "ollama":
        return LLMSettings(
            provider=provider,
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    raise ValueError("LLM_PROVIDER must be either 'openai' or 'ollama'")


def is_llm_configured() -> bool:
    settings = get_llm_settings()
    return settings.provider == "ollama" or bool(os.getenv("OPENAI_API_KEY"))


def build_chat_model():
    """Create the selected LangChain chat model without making a request."""
    settings = get_llm_settings()

    if settings.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.model, temperature=0)

    from langchain_ollama import ChatOllama

    return ChatOllama(model=settings.model, base_url=settings.base_url, temperature=0)
