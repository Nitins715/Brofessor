import json
from pathlib import Path
from typing import Any, Dict, Optional
from django.conf import settings
from .base import BaseLLMProvider
from .ollama import OllamaLLMProvider
from .gemini import GeminiLLMProvider
from .openai import OpenAILLMProvider
from .mock import MockLLMProvider


def get_ai_config_file() -> Path:
    data_dir = getattr(settings, "DATA_DIR", settings.BASE_DIR / "data")
    return Path(data_dir) / "ai_config.json"


def get_system_ai_config() -> Dict[str, Any]:
    config_file = get_ai_config_file()
    saved = {}
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            saved = {}

    return {
        "llm_provider": saved.get("llm_provider") or getattr(settings, "LLM_PROVIDER", "ollama"),
        "gemini_api_key": saved.get("gemini_api_key") or getattr(settings, "GEMINI_API_KEY", ""),
        "gemini_model": saved.get("gemini_model") or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"),
        "openai_api_key": saved.get("openai_api_key") or getattr(settings, "OPENAI_API_KEY", ""),
        "openai_model": saved.get("openai_model") or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
        "openai_base_url": saved.get("openai_base_url") or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "ollama_base_url": saved.get("ollama_base_url") or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        "ollama_model": saved.get("ollama_model") or getattr(settings, "OLLAMA_MODEL", "gemma3:4b"),
    }


def save_system_ai_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    config = get_system_ai_config()
    config.update(updates)
    config_file = get_ai_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory resolving active LLM generation provider.
    Supported: 'gemini', 'openai', 'ollama', 'mock'.
    """
    ai_cfg = get_system_ai_config()
    provider = provider_name or ai_cfg.get("llm_provider") or getattr(settings, "LLM_PROVIDER", "ollama")
    normalized = provider.lower().strip()

    if normalized in ("mock", "test"):
        return MockLLMProvider()
    elif normalized in ("gemini", "google"):
        return GeminiLLMProvider(
            api_key=ai_cfg.get("gemini_api_key") or getattr(settings, "GEMINI_API_KEY", ""),
            model_name=ai_cfg.get("gemini_model") or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"),
        )
    elif normalized in ("openai", "openrouter", "groq", "cloud"):
        return OpenAILLMProvider(
            api_key=ai_cfg.get("openai_api_key") or getattr(settings, "OPENAI_API_KEY", ""),
            model_name=ai_cfg.get("openai_model") or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            base_url=ai_cfg.get("openai_base_url") or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    elif normalized in ("ollama", "local"):
        return OllamaLLMProvider(
            base_url=ai_cfg.get("ollama_base_url") or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model_name=ai_cfg.get("ollama_model") or getattr(settings, "OLLAMA_MODEL", "llama3.2"),
        )
    else:
        return OllamaLLMProvider()
