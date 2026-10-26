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

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model_name}:generateContent?key={self._api_key}"

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

        logger.info(f"Dispatching generation request to Google Gemini [{self._model_name}]")

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"Gemini API returned no candidates: {data}")

            first_candidate = candidates[0]
            content = first_candidate.get("content", {})
            parts = content.get("parts", [])
            generated_text = "".join(part.get("text", "") for part in parts).strip()

            usage = data.get("usageMetadata", {})
            tokens_used = usage.get("totalTokenCount")

            return LLMResponse(
                text=generated_text,
                model=self._model_name,
                tokens_used=tokens_used,
                finish_reason=first_candidate.get("finishReason", "STOP"),
                metadata={
                    "prompt_token_count": usage.get("promptTokenCount"),
                    "candidates_token_count": usage.get("candidatesTokenCount"),
                },
            )
        except requests.exceptions.HTTPError as e:
            res_obj = getattr(e, "response", None) or response
            status_code = res_obj.status_code if res_obj is not None else 0
            error_details = ""
            if res_obj is not None:
                try:
                    error_details = res_obj.json().get("error", {}).get("message", "")
                except Exception:
                    error_details = getattr(res_obj, "text", "")[:200]

            # If the configured model is not found, unsupported, or deprecated on this API key/tier, fall back to gemini-1.5-flash
            err_lower = (error_details or "").lower()
            is_unsupported = (
                status_code in (404, 400)
                and any(kw in err_lower for kw in ("not found", "unsupported", "unknown model", "does not exist", "is not supported"))
            ) or (status_code == 404)

            if is_unsupported and self._model_name != "gemini-1.5-flash":
                logger.warning(
                    f"Gemini model '{self._model_name}' is not supported ({status_code}: {error_details}). "
                    f"Automatically falling back to 'gemini-1.5-flash'..."
                )
                fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self._api_key}"
                try:
                    fallback_resp = requests.post(
                        fallback_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=self.timeout,
                    )
                    fallback_resp.raise_for_status()
                    fb_data = fallback_resp.json()
                    fb_candidates = fb_data.get("candidates", [])
                    if fb_candidates:
                        fb_first = fb_candidates[0]
                        fb_content = fb_first.get("content", {})
                        fb_parts = fb_content.get("parts", [])
                        fb_text = "".join(part.get("text", "") for part in fb_parts).strip()
                        fb_usage = fb_data.get("usageMetadata", {})
                        return LLMResponse(
                            text=fb_text,
                            model="gemini-1.5-flash (fallback)",
                            tokens_used=fb_usage.get("totalTokenCount"),
                            finish_reason=fb_first.get("finishReason", "STOP"),
                            metadata={
                                "fallback_from": self._model_name,
                                "prompt_token_count": fb_usage.get("promptTokenCount"),
                                "candidates_token_count": fb_usage.get("candidatesTokenCount"),
                            },
                        )
                except Exception as fb_err:
                    logger.error(f"Fallback to gemini-1.5-flash also failed: {fb_err}")

            msg = f"Gemini API HTTP Error ({status_code}): {error_details or str(e)}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini generation request failed: {e}")
            raise RuntimeError(f"Gemini connection error: {str(e)}") from e
