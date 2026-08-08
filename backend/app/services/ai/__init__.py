"""
AI service data types.

Provides shared data classes used by the LangChain-based provider registry
and the AI agent router.
"""

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
