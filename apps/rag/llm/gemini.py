import logging
from typing import Any, Dict, Optional
import requests
from django.conf import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger("brofessor")


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini API LLM provider interfacing via Gemini REST API.
    Supports gemini-1.5-flash, gemini-2.0-flash, gemini-1.5-pro, etc.
    Requires GEMINI_API_KEY.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 60,
    ):
        self._api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self._model_name = model_name or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
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
                "Gemini API key is not configured. Please add your GEMINI_API_KEY in Settings."
            )

        generation_config: Dict[str, Any] = {
            "temperature": temperature,
        }
        if kwargs.get("json_mode") or "json" in (system_prompt or "").lower() or "json" in prompt.lower():
            generation_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": generation_config,
        }

        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        # Pool of 2-3 newer, fast models ONLY
        FAST_MODELS = [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ]
        if self._model_name in FAST_MODELS:
            model_pool = [self._model_name] + [m for m in FAST_MODELS if m != self._model_name]
        else:
            model_pool = list(FAST_MODELS)
        model_pool = model_pool[:3]

        # Fast timeout so queries don't hang for 60 seconds
        request_timeout = min(self.timeout, 8)
        last_error_desc = ""

        for model in model_pool:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self._api_key}"
            logger.info(f"Dispatching to Gemini fast pool model [{model}] (timeout={request_timeout}s)")
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=request_timeout,
                )
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        first_candidate = candidates[0]
                        content = first_candidate.get("content", {})
                        parts = content.get("parts", [])
                        generated_text = "".join(part.get("text", "") for part in parts).strip()
                        if generated_text:
                            usage = data.get("usageMetadata", {})
                            return LLMResponse(
                                text=generated_text,
                                model=model,
                                tokens_used=usage.get("totalTokenCount"),
                                finish_reason=first_candidate.get("finishReason", "STOP"),
                                metadata={
                                    "model_used": model,
                                    "pool_failover": model != self._model_name,
                                },
                            )
                else:
                    err_msg = ""
                    try:
                        err_msg = response.json().get("error", {}).get("message", "")
                    except Exception:
                        err_msg = response.text[:120]
                    last_error_desc = f"HTTP {response.status_code}: {err_msg}"
                    logger.warning(f"Gemini fast model [{model}] failed ({last_error_desc}). Trying next fast model in pool...")
            except requests.exceptions.Timeout:
                last_error_desc = f"Read timed out after {request_timeout}s"
                logger.warning(f"Gemini fast model [{model}] timed out after {request_timeout}s. Trying next fast model in pool...")
            except requests.exceptions.RequestException as req_err:
                last_error_desc = str(req_err)
                logger.warning(f"Gemini fast model [{model}] connection error: {req_err}. Trying next fast model in pool...")

        # If all models in the fast pool failed, return a clean API down error
        api_down_msg = (
            f"AI Cloud API is currently experiencing downtime or high demand across fast models ({last_error_desc}). "
            "Please try again in a few moments or switch to local Ollama in Settings."
        )
        logger.error(api_down_msg)
        raise RuntimeError(api_down_msg)

