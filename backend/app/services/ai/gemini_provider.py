"""
Google Gemini AI provider implementation.

Wraps the Gemini REST API (generativelanguage.googleapis.com) behind
the abstract AIProvider interface.
"""

import os
import logging
from typing import Optional

import httpx

from app.services.ai import AIProvider, AIMessage, AIResponse

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = (
    "You are an AI coding assistant integrated into Colab.ai, a collaborative Linux lab platform. "
    "Help users with programming questions, debugging, and shell commands. "
    "Be concise and practical."
)

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self):
        self._api_key = os.getenv("GEMINI_API_KEY", "")

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Google Gemini"

    def is_available(self) -> bool:
        return bool(self._api_key and self._api_key != "your-gemini-key-here")

    def list_models(self) -> list[str]:
        return GEMINI_MODELS if self.is_available() else []

    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        if not self.is_available():
            raise RuntimeError("Gemini provider is not configured (missing GEMINI_API_KEY)")

        model = model or self.default_model

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            gemini_messages.append({
                "role": role,
                "parts": [{"text": msg.content}],
            })

        url = f"{GEMINI_API_URL.format(model=model)}?key={self._api_key}"
        payload = {
            "contents": gemini_messages,
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}],
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        data = response.json()

        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response format: {e}")

        # Extract usage metadata if available
        usage = {}
        if "usageMetadata" in data:
            meta = data["usageMetadata"]
            usage = {
                "prompt_tokens": meta.get("promptTokenCount", 0),
                "completion_tokens": meta.get("candidatesTokenCount", 0),
                "total_tokens": meta.get("totalTokenCount", 0),
            }

        return AIResponse(
            content=reply,
            model=model,
            provider=self.name,
            usage=usage,
        )
