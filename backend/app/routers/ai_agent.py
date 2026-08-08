"""
AI Agent router.

LangChain-powered AI chat endpoint with automatic provider fallback.
Supports Google Gemini, OpenAI, and any OpenAI-compatible endpoint (Ollama, vLLM, etc.).
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.ai import AIMessage
from app.services.ai.registry import registry
from app.auth.dependencies import get_current_user
from app.models.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """Send a chat message to the AI assistant."""

    # Convert request messages to internal format
    messages = [
        AIMessage(role=msg.role, content=msg.content)
        for msg in req.messages
    ]

    # Use the provider registry with automatic fallback
    response = await registry.chat(
        messages=messages,
        provider_name=req.provider,
        model=req.model,
    )

    return ChatResponse(
        reply=response.content,
        model=response.model,
        provider=response.provider,
    )


@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_user)):
    """List available AI providers and their models."""
    return {
        "providers": registry.get_available_providers(),
    }


@router.get("/")
async def root():
    """AI agent status endpoint."""
    providers = registry.get_available_providers()
    any_configured = any(p["available"] for p in providers)
    return {
        "message": "AI Agent router is active",
        "configured": any_configured,
        "providers": providers,
    }
