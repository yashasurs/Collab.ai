"""Tests for session management endpoints."""

import pytest
import uuid


class TestCreateSession:
    """Tests for POST /api/sessions/create."""

    def test_create_session_success(self, client):
        response = client.post("/api/sessions/create", json={
            "osType": "alpine",
            "userId": str(uuid.uuid4()),
            "username": "testuser",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session" in data
        assert data["session"]["osType"] == "alpine"
        assert len(data["session"]["participants"]) == 1

    def test_create_session_with_snapshot(self, client):
        response = client.post("/api/sessions/create", json={
            "osType": "ubuntu",
            "snapshotId": "snapshot-123",
            "userId": str(uuid.uuid4()),
            "username": "user2",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["snapshotId"] == "snapshot-123"

    def test_create_session_default_os(self, client):
        response = client.post("/api/sessions/create", json={
            "userId": str(uuid.uuid4()),
            "username": "user3",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["osType"] == "alpine"


class TestGetSession:
    """Tests for GET /api/sessions/{session_id}."""

    def test_get_session_success(self, client, test_session):
        response = client.get(f"/api/sessions/{test_session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["id"] == test_session.id

    def test_get_session_not_found(self, client):
        response = client.get(f"/api/sessions/{uuid.uuid4()}")
        assert response.status_code == 404


class TestJoinSession:
    """Tests for POST /api/sessions/{session_id}/join."""

    def test_join_session_success(self, client, test_session):
        new_user_id = str(uuid.uuid4())
        response = client.post(f"/api/sessions/{test_session.id}/join", json={
            "userId": new_user_id,
            "username": "joiner",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should now have 2 participants
        assert len(data["session"]["participants"]) == 2

    def test_join_nonexistent_session(self, client):
        response = client.post(f"/api/sessions/{uuid.uuid4()}/join", json={
            "userId": str(uuid.uuid4()),
            "username": "ghost",
        })
        assert response.status_code == 404


class TestListSessions:
    """Tests for GET /api/sessions."""

    def test_list_sessions_empty(self, client):
        response = client.get("/api/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_sessions_with_data(self, client, test_session):
        response = client.get("/api/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestDeleteSession:
    """Tests for DELETE /api/sessions/{session_id}."""

    def test_delete_session_success(self, client, test_session):
        response = client.delete(f"/api/sessions/{test_session.id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it's gone
        response = client.get(f"/api/sessions/{test_session.id}")
        assert response.status_code == 404

    def test_delete_nonexistent_session(self, client):
        response = client.delete(f"/api/sessions/{uuid.uuid4()}")
        assert response.status_code == 404


class TestOsOptions:
    """Tests for GET /api/sessions/os-options."""

    def test_os_options(self, client):
        response = client.get("/api/sessions/os-options")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["osOptions"]) >= 5
        os_ids = [opt["id"] for opt in data["osOptions"]]
        assert "alpine" in os_ids
        assert "ubuntu" in os_ids
