"""
OpenAI-compatible AI provider implementation.

Works with:
- OpenAI API directly
- Any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM, Anthropic via proxy)
"""

import os
import logging
from typing import Optional

import httpx

from app.services.ai import AIProvider, AIMessage, AIResponse

logger = logging.getLogger(__name__)

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

SYSTEM_PROMPT = (
    "You are an AI coding assistant integrated into Colab.ai, a collaborative Linux lab platform. "
    "Help users with programming questions, debugging, and shell commands. "
    "Be concise and practical."
)


class OpenAIProvider(AIProvider):
    """OpenAI-compatible API provider."""

    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY", "")
        self._base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI"

    def is_available(self) -> bool:
        return bool(self._api_key and self._api_key != "your-openai-key-here")

    def list_models(self) -> list[str]:
        return OPENAI_MODELS if self.is_available() else []

    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        if not self.is_available():
            raise RuntimeError("OpenAI provider is not configured (missing OPENAI_API_KEY)")

        model = model or self.default_model

        # Build message list with system prompt
        openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": openai_messages,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
            response.raise_for_status()

        data = response.json()

        try:
            reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected OpenAI response format: {e}")

        usage = {}
        if "usage" in data:
            usage = {
                "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                "completion_tokens": data["usage"].get("completion_tokens", 0),
                "total_tokens": data["usage"].get("total_tokens", 0),
            }

        return AIResponse(
            content=reply,
            model=model,
            provider=self.name,
            usage=usage,
        )
