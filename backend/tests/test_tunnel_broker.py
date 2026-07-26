"""Tests for Tunnel Broker endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
import uuid

from app.services.tunnel_broker import TunnelInfo

@pytest.fixture
def mock_tunnel_broker():
    """Mock the TunnelBroker to prevent actual cloudflared processes."""
    with patch("app.routers.tunnels.tunnel_broker") as mock:
        mock.create_tunnel = AsyncMock(return_value=TunnelInfo(
            session_id="mock-session-123",
            user_id="mock-user-123",
            url="https://mock-tunnel.trycloudflare.com",
            local_port=8080,
            created_at=1000.0,
            last_active=1000.0,
            pid=9999
        ))
        mock.get_tunnel = AsyncMock(return_value=TunnelInfo(
            session_id="mock-session-123",
            user_id="mock-user-123",
            url="https://mock-tunnel.trycloudflare.com",
            local_port=8080,
            created_at=1000.0,
            last_active=1000.0,
            pid=9999
        ))
        mock.list_tunnels = AsyncMock(return_value=[])
        mock.close_tunnel = AsyncMock(return_value=True)
        mock.health_check = AsyncMock(return_value=True)
        yield mock


class TestTunnels:
    """Tests for /api/tunnels/ endpoints."""

    def test_create_tunnel_success(self, client, auth_headers, mock_tunnel_broker):
        response = client.post("/api/tunnels/create", json={
            "sessionId": "mock-session-123",
            "localPort": 8080
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sessionId"] == "mock-session-123"
        assert data["tunnelUrl"] == "https://mock-tunnel.trycloudflare.com"
        mock_tunnel_broker.create_tunnel.assert_called_once()

    def test_create_tunnel_quota_exceeded(self, client, auth_headers, mock_tunnel_broker):
        mock_tunnel_broker.create_tunnel.side_effect = RuntimeError("Tunnel quota exceeded")
        
        response = client.post("/api/tunnels/create", json={
            "sessionId": "mock-session-456",
            "localPort": 8080
        }, headers=auth_headers)
        
        assert response.status_code == 429
        assert "quota exceeded" in response.json()["detail"].lower()

    def test_get_tunnel(self, client, mock_tunnel_broker):
        response = client.get("/api/tunnels/mock-session-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tunnelUrl"] == "https://mock-tunnel.trycloudflare.com"

    def test_get_tunnel_not_found(self, client, mock_tunnel_broker):
        mock_tunnel_broker.get_tunnel.return_value = None
        response = client.get("/api/tunnels/ghost-session")
        assert response.status_code == 404

    def test_list_tunnels(self, client, mock_tunnel_broker):
        mock_tunnel_broker.list_tunnels.return_value = [
            TunnelInfo(
                session_id="sess-1", user_id="user-1", url="https://t1",
                local_port=80, created_at=0, last_active=0, pid=1
            )
        ]
        response = client.get("/api/tunnels/")
        assert response.status_code == 200
        assert len(response.json()["tunnels"]) == 1

    def test_close_tunnel(self, client, auth_headers, mock_tunnel_broker):
        response = client.delete("/api/tunnels/mock-session-123", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_health_endpoint(self, client, mock_tunnel_broker):
        mock_tunnel_broker.list_tunnels.return_value = [
            TunnelInfo(
                session_id="sess-1", user_id="user-1", url="https://t1",
                local_port=80, created_at=0, last_active=0, pid=1
            )
        ]
        response = client.get("/api/tunnels/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 1
        assert data["healthy"] == 1
