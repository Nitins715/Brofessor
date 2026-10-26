from typing import Any, Dict, Optional
from .base import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock LLM provider for fast unit tests and offline testing.
    Can return predefined responses or formatted template responses without an Ollama instance.
    """

    def __init__(
        self,
        fixed_response: Optional[str] = None,
        model_name: str = "mock-llama3-local",
    ):
        self.fixed_response = fixed_response
        self._model_name = model_name
        self.call_history: list = []

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
        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "kwargs": kwargs,
        })

        if self.fixed_response is not None:
            text = self.fixed_response
        else:
            text = f"Mock response based on context for prompt: {prompt[:80]}..."

        return LLMResponse(
            text=text,
            model=self._model_name,
            tokens_used=42,
            finish_reason="stop",
            metadata={"mock": True},
        )
