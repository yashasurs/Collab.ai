"""
AI Provider Registry.

Central registry that manages available AI providers and implements
automatic fallback chains when a provider is unavailable or errors out.
"""

import logging
from typing import Optional

from app.services.ai import AIProvider, AIMessage, AIResponse
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Manages AI providers with auto-detection and fallback.

    Providers are tried in priority order. If the selected provider fails,
    the registry falls back to the next available provider.
    """

    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._priority: list[str] = []
        self._register_defaults()

    def _register_defaults(self):
        """Register all built-in providers."""
        self.register(GeminiProvider())
        self.register(OpenAIProvider())

    def register(self, provider: AIProvider):
        """Register a new AI provider."""
        self._providers[provider.name] = provider
        self._priority.append(provider.name)
        logger.info(
            f"AI provider registered: {provider.display_name} "
            f"(available={provider.is_available()})"
        )

    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get a specific provider by name."""
        return self._providers.get(name)

    def get_available_providers(self) -> list[dict]:
        """List all providers with their availability status."""
        return [
            {
                "name": p.name,
                "displayName": p.display_name,
                "available": p.is_available(),
                "models": p.list_models(),
            }
            for p in self._providers.values()
        ]

    def get_default_provider(self) -> Optional[AIProvider]:
        """Get the first available provider in priority order."""
        for name in self._priority:
            provider = self._providers[name]
            if provider.is_available():
                return provider
        return None

    async def chat(
        self,
        messages: list[AIMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Send a chat request, with automatic fallback.

        If provider_name is specified, try that provider first.
        On failure, falls back to the next available provider.
        """
        # Build ordered list of providers to try
        providers_to_try: list[AIProvider] = []

        if provider_name:
            specific = self.get_provider(provider_name)
            if specific and specific.is_available():
                providers_to_try.append(specific)

        # Add remaining available providers as fallbacks
        for name in self._priority:
            provider = self._providers[name]
            if provider.is_available() and provider not in providers_to_try:
                providers_to_try.append(provider)

        if not providers_to_try:
            return AIResponse(
                content=(
                    "No AI providers are configured. "
                    "Set GEMINI_API_KEY or OPENAI_API_KEY environment variable to enable AI assistant."
                ),
                model="none",
                provider="stub",
            )

        # Try each provider, falling back on error
        last_error = None
        for provider in providers_to_try:
            try:
                response = await provider.chat(messages, model=model, **kwargs)
                return response
            except Exception as e:
                logger.warning(f"AI provider '{provider.name}' failed: {e}")
                last_error = e
                continue

        # All providers failed
        return AIResponse(
            content=f"All AI providers failed. Last error: {last_error}",
            model="none",
            provider="fallback",
        )


# Singleton registry instance
registry = ProviderRegistry()
