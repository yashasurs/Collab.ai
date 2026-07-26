"""
Abstract base class for AI providers.

All AI providers (Gemini, OpenAI, Ollama, etc.) implement this interface,
enabling provider-agnostic chat and automatic fallback chains.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class AIMessage:
    """A single message in a conversation."""
    role: str       # "user", "assistant", "system"
    content: str


@dataclass
class AIResponse:
    """Response from an AI provider."""
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)  # token counts if available


class AIProvider(ABC):
    """Abstract base class for AI provider implementations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g., 'gemini', 'openai', 'ollama')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return a list of available model identifiers."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""
        ...

    @property
    def default_model(self) -> str:
        """The default model to use if none is specified."""
        models = self.list_models()
        return models[0] if models else ""
