import pytest

from apps.dlq_healing_agent.src.llm import get_llm_settings, is_llm_configured


def test_openai_is_the_default_provider(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = get_llm_settings()

    assert settings.provider == "openai"
    assert settings.model == "gpt-4o-mini"
    assert is_llm_configured() is True


def test_ollama_does_not_require_an_openai_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:3b")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = get_llm_settings()

    assert settings.provider == "ollama"
    assert settings.model == "qwen2.5:3b"
    assert is_llm_configured() is True


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")

    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        get_llm_settings()
