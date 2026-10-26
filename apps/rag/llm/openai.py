import logging
import json
from typing import Any, Dict, Optional
import requests
from django.conf import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger("brofessor")


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI-compatible LLM provider interfacing via standard chat completions REST API.
    Supports OpenAI, OpenRouter, Groq, Mistral, and local vLLM instances.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        self._api_key = (api_key or getattr(settings, "OPENAI_API_KEY", "")).strip()
        self._model_name = (model_name or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")).strip()
        self._base_url = (base_url or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self._api_key:
            raise ValueError(
                "OpenAI/Cloud API key is not configured. Please add your OPENAI_API_KEY or CLOUD_LLM_API_KEY in Settings."
            )

        url = f"{self._base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if kwargs.get("json_mode") or "json" in (system_prompt or "").lower() or "json" in prompt.lower():
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        logger.info(f"Dispatching generation request to OpenAI-compatible provider [{self._model_name}] at {self._base_url}")

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"OpenAI API returned no choices: {data}")

            choice = choices[0]
            generated_text = choice.get("message", {}).get("content", "").strip()
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")

            return LLMResponse(
                text=generated_text,
                model=self._model_name,
                tokens_used=tokens_used,
                finish_reason=choice.get("finish_reason", "stop"),
                metadata={
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                },
            )
        except requests.exceptions.HTTPError as e:
            error_details = ""
            try:
                error_details = response.json().get("error", {}).get("message", "")
            except Exception:
                pass
            msg = f"Cloud LLM HTTP Error ({response.status_code}): {error_details or str(e)}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Cloud LLM request failed: {e}")
            raise RuntimeError(f"Cloud LLM connection error: {str(e)}") from e
