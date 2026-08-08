"""
AI Provider Registry — LangChain-based.

Uses LangChain's unified chat model interface to support multiple AI backends
(Google Gemini, OpenAI, or any OpenAI-compatible endpoint) with automatic
failover via `with_fallbacks()`.
"""

import os
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage as LCAIMessage, SystemMessage

from app.services.ai import AIMessage, AIResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an AI coding assistant integrated into Colab.ai, a collaborative Linux lab platform. "
    "Help users with programming questions, debugging, and shell commands. "
    "Be concise and practical."
)

# Model lists for each provider
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]


class ProviderRegistry:
    """
    Manages LangChain chat models with auto-detection and fallback.

    On initialization, detects which API keys are available and builds
    a LangChain model chain with automatic failover.
    """

    def __init__(self):
        self._providers: list[dict] = []
        self._model = None  # The LangChain model (with fallbacks attached)
        self._setup()

    def _setup(self):
        """Detect available providers and build the LangChain model chain."""
        models = []
        
        # Define provider configurations
        configs = [
            {
                "name": "gemini",
                "displayName": "Google Gemini",
                "models": GEMINI_MODELS,
                "key_env": "GEMINI_API_KEY",
                "placeholder": "your-gemini-key-here",
                "init": lambda key: __import__('langchain_google_genai').ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash", google_api_key=key, temperature=0.7, timeout=30
                )
            },
            {
                "name": "openai",
                "displayName": "OpenAI",
                "models": OPENAI_MODELS,
                "key_env": "OPENAI_API_KEY",
                "placeholder": "your-openai-key-here",
                "init": lambda key: __import__('langchain_openai').ChatOpenAI(
                    model="gpt-4o-mini", api_key=key, temperature=0.7, timeout=30, 
                    base_url=os.getenv("OPENAI_BASE_URL")
                )
            }
        ]

        # Initialize providers
        for cfg in configs:
            key = os.getenv(cfg["key_env"], "")
            is_configured = bool(key and key != cfg["placeholder"])
            
            provider_info = {
                "name": cfg["name"],
                "displayName": cfg["displayName"],
                "available": False,
                "models": []
            }

            if is_configured:
                try:
                    model = cfg["init"](key)
                    models.append((cfg["name"], model))
                    provider_info["available"] = True
                    provider_info["models"] = cfg["models"]
                    logger.info(f"AI provider registered: {cfg['displayName']} (available=True)")
                except Exception as e:
                    logger.warning(f"Failed to initialize {cfg['displayName']} provider: {e}")
            else:
                logger.info(f"AI provider registered: {cfg['displayName']} (available=False)")

            self._providers.append(provider_info)

        # Build the chain with fallbacks
        if models:
            self._primary_name, primary_model = models[0]
            self._model = primary_model.with_fallbacks([m for _, m in models[1:]]) if len(models) > 1 else primary_model
            
            if len(models) > 1:
                logger.info(f"AI fallback chain: {' → '.join(n for n, _ in models)}")
        else:
            self._model = None
            self._primary_name = None

    def get_available_providers(self) -> list[dict]:
        """List all providers with their availability status."""
        return self._providers

    async def chat(
        self,
        messages: list[AIMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AIResponse:
        """
        Send a chat request using the LangChain model chain.

        Automatic failover is handled by LangChain's with_fallbacks().
        """
        if self._model is None:
            return AIResponse(
                content=(
                    "No AI providers are configured. "
                    "Set GEMINI_API_KEY or OPENAI_API_KEY environment variable to enable AI assistant."
                ),
                model="none",
                provider="stub",
            )

        # Convert internal messages to LangChain message types
        lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(LCAIMessage(content=msg.content))
            elif msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))

        try:
            response = await self._model.ainvoke(lc_messages)

            # Extract usage metadata if available
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                meta = response.usage_metadata
                usage = {
                    "prompt_tokens": meta.get("input_tokens", 0),
                    "completion_tokens": meta.get("output_tokens", 0),
                    "total_tokens": meta.get("total_tokens", 0),
                }

            # Determine which provider/model actually responded
            resp_model = model or getattr(response, "response_metadata", {}).get("model_name", "unknown")
            resp_provider = self._primary_name or "unknown"

            return AIResponse(
                content=response.content,
                model=resp_model,
                provider=resp_provider,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"All AI providers failed: {e}")
            return AIResponse(
                content=f"All AI providers failed. Error: {e}",
                model="none",
                provider="fallback",
            )


# Singleton registry instance
registry = ProviderRegistry()
