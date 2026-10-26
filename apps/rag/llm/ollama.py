import logging
import os
from typing import Any, Dict, Optional
import requests
from django.conf import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger("brofessor")


class OllamaLLMProvider(BaseLLMProvider):
    """
    Local Ollama LLM provider interfacing via Ollama's REST API.
    Configurable via OLLAMA_BASE_URL, OLLAMA_MODEL, and OLLAMA_TIMEOUT settings.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self._base_url = (base_url or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self._model_name = model_name or getattr(settings, "OLLAMA_MODEL", "llama3.2")
        env_timeout = int(os.getenv("OLLAMA_TIMEOUT", "180")) if os.getenv("OLLAMA_TIMEOUT") else 180
        self.timeout = timeout if timeout is not None else getattr(settings, "OLLAMA_TIMEOUT", env_timeout)

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_candidate_urls(self) -> list:
        candidates = [self._base_url]
        if "127.0.0.1" in self._base_url or "localhost" in self._base_url:
            alt = self._base_url.replace("127.0.0.1", "host.docker.internal").replace("localhost", "host.docker.internal")
            if alt not in candidates:
                candidates.append(alt)
        elif "host.docker.internal" in self._base_url:
            alt = self._base_url.replace("host.docker.internal", "127.0.0.1")
            if alt not in candidates:
                candidates.append(alt)
        return candidates

    def _get_available_models(self, base_url: str) -> list:
        try:
            res = requests.get(f"{base_url}/api/tags", timeout=5)
            if res.ok:
                data = res.json()
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass
        return []

    def _resolve_best_model(self, base_url: str) -> str:
        available = self._get_available_models(base_url)
        if not available:
            return self._model_name

        # Exact match
        if self._model_name in available:
            return self._model_name

        # Tag or prefix match (e.g. "llama3.2" matches "llama3.2:1b" or "llama3.2:latest")
        for m in available:
            if m.startswith(f"{self._model_name}:") or self._model_name.startswith(m.split(":")[0]):
                logger.info(f"Ollama auto-matched configured model '{self._model_name}' to installed '{m}'")
                return m

        # If user configured a missing model but has local models installed, pick the first one
        if available:
            logger.warning(
                f"Configured Ollama model '{self._model_name}' not found. Falling back to installed model '{available[0]}'."
            )
            return available[0]

        return self._model_name

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> LLMResponse:
        candidate_urls = self._get_candidate_urls()
        last_error = None
        working_url = None

        for candidate_url in candidate_urls:
            url = f"{candidate_url}/api/generate"
            resolved_model = self._resolve_best_model(candidate_url)
            self._model_name = resolved_model

            num_threads = min(8, max(2, os.cpu_count() or 4))
            max_tokens = kwargs.get("max_tokens") or 2500

            payload = {
                "model": self._model_name,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_thread": num_threads,
                },
            }
            if kwargs.get("json_mode") or "json" in (system_prompt or "").lower() or "json" in prompt.lower():
                payload["format"] = "json"

            if system_prompt:
                payload["system"] = system_prompt

            logger.info(f"Dispatching generation request to Ollama [{self._model_name}] at {candidate_url}")

            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                )
                
                # If model not found on this server, inspect tags and retry once if possible
                if response.status_code == 404:
                    available = self._get_available_models(candidate_url)
                    if available and self._model_name not in available:
                        fallback_model = available[0]
                        logger.warning(f"Ollama model '{self._model_name}' gave 404. Retrying with available '{fallback_model}'")
                        self._model_name = fallback_model
                        payload["model"] = fallback_model
                        response = requests.post(url, json=payload, timeout=self.timeout)

                response.raise_for_status()
                data = response.json()
                self._base_url = candidate_url  # Cache successful URL

                generated_text = data.get("response", "").strip()
                eval_count = data.get("eval_count")
                prompt_eval_count = data.get("prompt_eval_count")
                tokens_used = (eval_count or 0) + (prompt_eval_count or 0) if (eval_count or prompt_eval_count) else None

                return LLMResponse(
                    text=generated_text,
                    model=self._model_name,
                    tokens_used=tokens_used,
                    finish_reason=data.get("done_reason", "stop"),
                    metadata={
                        "total_duration_ns": data.get("total_duration"),
                        "eval_count": eval_count,
                        "prompt_eval_count": prompt_eval_count,
                    },
                )
            except requests.exceptions.ReadTimeout as te:
                logger.error(f"Ollama generation timed out after {self.timeout}s: {te}")
                available = self._get_available_models(candidate_url)
                models_hint = f" (Installed models: {', '.join(available)})" if available else ""
                raise TimeoutError(
                    f"Ollama request timed out after {self.timeout}s on model '{self._model_name}'. "
                    f"If running on CPU, consider switching to the faster 'llama3.2:1b' in Settings.{models_hint}"
                ) from te
            except requests.exceptions.ConnectionError as ce:
                logger.warning(f"Failed connecting to Ollama at {candidate_url}: {ce}")
                last_error = ce
                continue
            except requests.exceptions.RequestException as re:
                logger.error(f"Ollama generation request failed at {candidate_url}: {re}")
                available = self._get_available_models(candidate_url)
                models_hint = f" Available models: {', '.join(available)}." if available else ""
                raise RuntimeError(f"Ollama generation error: {str(re)}.{models_hint}") from re

        # If all candidates failed with ConnectionError
        raise ConnectionError(
            f"Ollama server is unreachable at {self._base_url} (also tried {candidate_urls}). "
            f"If running inside Docker, ensure host Ollama is running and accessible via http://host.docker.internal:11434."
        ) from last_error
