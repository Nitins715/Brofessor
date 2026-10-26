import logging
from typing import Any, Dict, Optional, Tuple
from django.conf import settings

from apps.rag.llm.base import BaseLLMProvider
from apps.rag.llm.ollama import OllamaLLMProvider
from apps.rag.llm.gemini import GeminiLLMProvider
from apps.rag.llm.openai import OpenAILLMProvider
from apps.rag.llm.mock import MockLLMProvider
from apps.rag.llm.registry import get_system_ai_config

logger = logging.getLogger("brofessor")


class AssessmentProviderError(Exception):
    """Base error for assessment provider failures."""
    def __init__(self, message: str, provider: str, difficulty: str, can_retry: bool = True):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.difficulty = difficulty
        self.can_retry = can_retry


class ProviderNotConfiguredError(AssessmentProviderError):
    """Raised when the mandated provider for a difficulty tier has missing credentials or endpoints."""
    pass


class ProviderUnavailableError(AssessmentProviderError):
    """Raised when the provider endpoint is unreachable or returned connection/service errors."""
    pass


class AssessmentProviderResolver:
    """
    Enforces the assessment architecture requirements:
    - Easy: Local Ollama API (OLLAMA_BASE_URL, OLLAMA_MODEL)
    - Medium: Configured External Cloud LLM API (Gemini or OpenAI)
    - Hard: Configured External Cloud LLM API (Gemini or OpenAI)

    Never silently substitutes a different provider when the required provider fails.
    """

    @classmethod
    def get_provider_for_difficulty(
        cls,
        difficulty: str = "easy",
        override_provider: Optional[BaseLLMProvider] = None,
    ) -> BaseLLMProvider:
        """
        Resolves the LLM provider for the given assessment difficulty level.
        Auto-priority: Cloud (Gemini/OpenAI) by default if available,
        otherwise automatically falls back to Local Ollama. No user selection needed.
        """
        if override_provider is not None:
            return override_provider

        diff_norm = (difficulty or "easy").lower().strip()
        # Map legacy aliases
        if diff_norm in ("basic", "beginner"):
            diff_norm = "easy"
        elif diff_norm in ("intermediate",):
            diff_norm = "medium"
        elif diff_norm in ("advanced", "expert"):
            diff_norm = "hard"

        ai_cfg = get_system_ai_config()

        # Mock / Test environment support
        global_provider = (ai_cfg.get("llm_provider") or getattr(settings, "LLM_PROVIDER", "")).lower().strip()
        if global_provider in ("mock", "test"):
            return MockLLMProvider()

        gemini_key = (ai_cfg.get("gemini_api_key") or getattr(settings, "GEMINI_API_KEY", "")).strip()
        openai_key = (ai_cfg.get("openai_api_key") or getattr(settings, "OPENAI_API_KEY", "")).strip()

        # Auto-routing: Cloud by default if credentials exist, else local Ollama
        if gemini_key or openai_key:
            return cls._resolve_cloud(ai_cfg, diff_norm)
        else:
            return cls._resolve_ollama(ai_cfg, diff_norm)

    @classmethod
    def _resolve_ollama(cls, ai_cfg: Dict[str, Any], difficulty: str) -> OllamaLLMProvider:
        """Resolve and validate local Ollama configuration for Easy tier."""
        if "ollama_base_url" in ai_cfg:
            base_url = (ai_cfg.get("ollama_base_url") or "").strip().rstrip("/")
        else:
            base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")

        if "ollama_model" in ai_cfg:
            model_name = (ai_cfg.get("ollama_model") or "").strip()
        else:
            model_name = getattr(settings, "OLLAMA_MODEL", "llama3.2").strip()

        if not base_url:
            raise ProviderNotConfiguredError(
                message="Local Ollama base URL is not configured. Please specify OLLAMA_BASE_URL in Settings.",
                provider="ollama",
                difficulty=difficulty,
            )

        if not model_name:
            raise ProviderNotConfiguredError(
                message="Local Ollama model name is not specified. Please configure OLLAMA_MODEL (e.g. 'llama3.2') in Settings.",
                provider="ollama",
                difficulty=difficulty,
            )

        return OllamaLLMProvider(base_url=base_url, model_name=model_name)

    @classmethod
    def _resolve_cloud(cls, ai_cfg: Dict[str, Any], difficulty: str) -> BaseLLMProvider:
        """Resolve and validate external cloud LLM configuration for Medium/Hard tiers."""
        cloud_choice = (
            ai_cfg.get("cloud_provider")
            or getattr(settings, "CLOUD_LLM_PROVIDER", "")
        ).lower().strip()

        gemini_key = (
            ai_cfg.get("gemini_api_key")
            or getattr(settings, "GEMINI_API_KEY", "")
        ).strip()
        gemini_model = (
            ai_cfg.get("gemini_model")
            or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        ).strip()

        openai_key = (
            ai_cfg.get("openai_api_key")
            or getattr(settings, "OPENAI_API_KEY", "")
        ).strip()
        openai_model = (
            ai_cfg.get("openai_model")
            or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        ).strip()
        openai_base_url = (
            ai_cfg.get("openai_base_url")
            or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).strip().rstrip("/")

        # Check explicit selection or infer from available keys
        if cloud_choice == "openai" or (not gemini_key and openai_key):
            if not openai_key:
                raise ProviderNotConfiguredError(
                    message=(
                        f"External Cloud API key is missing for {difficulty.title()} assessments. "
                        "Please configure OPENAI_API_KEY in Settings or environment variables."
                    ),
                    provider="openai",
                    difficulty=difficulty,
                )
            return OpenAILLMProvider(
                api_key=openai_key,
                model_name=openai_model,
                base_url=openai_base_url,
            )
        else:
            # Default cloud provider is Google Gemini
            if not gemini_key:
                raise ProviderNotConfiguredError(
                    message=(
                        f"External Cloud API key is not configured for {difficulty.title()} assessments. "
                        "Please set your GEMINI_API_KEY or OPENAI_API_KEY in Settings or environment variables."
                    ),
                    provider="gemini",
                    difficulty=difficulty,
                )
            return GeminiLLMProvider(
                api_key=gemini_key,
                model_name=gemini_model,
            )

    @classmethod
    def get_provider_info(cls, difficulty: str = "easy") -> Dict[str, Any]:
        """Returns non-sensitive provider summary for UI display."""
        diff_norm = (difficulty or "easy").lower().strip()
        ai_cfg = get_system_ai_config()

        gemini_key = (ai_cfg.get("gemini_api_key") or getattr(settings, "GEMINI_API_KEY", "")).strip()
        openai_key = (ai_cfg.get("openai_api_key") or getattr(settings, "OPENAI_API_KEY", "")).strip()

        if gemini_key or openai_key:
            provider_type = "gemini" if gemini_key or not openai_key else "openai"
            model_name = (
                (ai_cfg.get("gemini_model") or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"))
                if provider_type == "gemini"
                else (ai_cfg.get("openai_model") or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"))
            )
            return {
                "difficulty": diff_norm,
                "tier_name": f"{diff_norm.title()} (Cloud: {provider_type.upper()})",
                "provider": provider_type,
                "model": model_name,
                "is_local": False,
                "is_configured": True,
            }
        else:
            return {
                "difficulty": diff_norm,
                "tier_name": f"{diff_norm.title()} (Local: Ollama)",
                "provider": "ollama",
                "model": ai_cfg.get("ollama_model") or getattr(settings, "OLLAMA_MODEL", "llama3.2"),
                "is_local": True,
                "endpoint": ai_cfg.get("ollama_base_url") or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                "is_configured": bool(ai_cfg.get("ollama_base_url") or getattr(settings, "OLLAMA_BASE_URL", "")),
            }
