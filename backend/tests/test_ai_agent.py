"""Tests for AI agent endpoint with mocked registry."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.ai import AIResponse

@pytest.fixture
def mock_ai_registry():
    """Mock the AI provider registry."""
    with patch("app.routers.ai_agent.registry") as mock:
        mock.chat = AsyncMock(return_value=AIResponse(
            content="Mocked AI response",
            model="mock-model",
            provider="mock-provider",
            usage={"total_tokens": 42}
        ))
        mock.get_available_providers.return_value = [
            {"name": "mock-provider", "available": True, "models": ["mock-model"]}
        ]
        yield mock


class TestAIAgent:
    """Tests for AI agent API."""

    def test_chat_success(self, client, auth_headers, mock_ai_registry):
        response = client.post("/api/ai/chat", json={
            "messages": [
                {"role": "user", "content": "Hello AI"}
            ]
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Mocked AI response"
        assert data["model"] == "mock-model"
        assert data["provider"] == "mock-provider"
        mock_ai_registry.chat.assert_called_once()

    def test_chat_unauthenticated(self, client, mock_ai_registry):
        response = client.post("/api/ai/chat", json={
            "messages": [
                {"role": "user", "content": "Hello AI"}
            ]
        })
        assert response.status_code == 401

    def test_list_providers(self, client, auth_headers, mock_ai_registry):
        response = client.get("/api/ai/providers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) == 1
        assert data["providers"][0]["name"] == "mock-provider"
