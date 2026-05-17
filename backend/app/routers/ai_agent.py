import os
import logging
from fastapi import APIRouter, HTTPException
import requests

from app.schemas.schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
SYSTEM_PROMPT = (
    "You are an AI coding assistant integrated into Colab.ai, a collaborative Linux lab platform. "
    "Help users with programming questions, debugging, and shell commands. "
    "Be concise and practical."
)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        # Return a helpful stub response when no key is configured
        return ChatResponse(
            reply=(
                "AI assistant is not configured yet. "
                "Set the GEMINI_API_KEY environment variable to enable it."
            ),
            model="stub",
        )

    # Convert OpenAI style messages to Gemini style
    gemini_messages = []
    for msg in req.messages:
        role = "model" if msg.role == "assistant" else "user"
        gemini_messages.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })

    model = req.model or "gemini-1.5-pro"
    url = GEMINI_API_URL.format(model=model, api_key=api_key)

    payload = {
        "contents": gemini_messages,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        }
    }

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Gemini API request timed out")
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e.response.text}")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Could not reach Gemini API: {e}")

    data = response.json()
    try:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected response format from Gemini API")

    return ChatResponse(reply=reply, model=model)


@router.get("/")
async def root():
    configured = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "message": "AI Agent router is active",
        "configured": configured,
    }
