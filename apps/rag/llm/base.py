from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional


@dataclass
class LLMResponse:
    """Standardized response from an LLM provider."""
    text: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract interface for pluggable LLM generation providers."""

    @property
    def provider_name(self) -> str:
        """Identifier for the LLM provider (e.g. ollama, gemini, openai)."""
        return getattr(self, "_provider_name", self.__class__.__name__.lower().replace("llmprovider", ""))

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active model."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response text for the given prompt and system instructions."""
        pass

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream response tokens as an iterator of strings."""
        resp = self.generate(prompt, system_prompt=system_prompt, temperature=temperature, **kwargs)
        words = resp.text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
