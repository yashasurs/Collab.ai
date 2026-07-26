"""Tests for container operations with mocked orchestrator."""

import pytest
from unittest.mock import AsyncMock, patch
import uuid

from app.schemas.schemas import CreateContainerRequest, ExecCommandRequest, SnapshotContainerRequest, WriteFileRequest
from app.services.orchestrator import ContainerInfo, ExecResult, FileInfo, SnapshotInfo


@pytest.fixture
def mock_orchestrator():
    """Mock the orchestrator to prevent actual Docker/K8s calls during tests."""
    with patch("app.routers.containers.orchestrator") as mock:
        mock.create = AsyncMock(return_value=ContainerInfo(
            id="mock-container-123",
            status="running",
            image="alpine:latest",
            labels={},
        ))
        mock.get = AsyncMock(return_value=ContainerInfo(
            id="mock-container-123",
            status="running",
            image="alpine:latest",
            labels={},
        ))
        mock.remove = AsyncMock(return_value=True)
        mock.exec = AsyncMock(return_value=ExecResult(exit_code=0, output="test output"))
        mock.snapshot = AsyncMock(return_value=SnapshotInfo(
            snapshot_id="mock-snapshot-123",
            image_id="mock-image-123",
            name="Test Snapshot",
        ))
        mock.list_files = AsyncMock(return_value=[
            FileInfo(name="file1.txt", path="/file1.txt", is_dir=False),
            FileInfo(name="dir1", path="/dir1", is_dir=True),
        ])
        mock.read_file = AsyncMock(return_value="file content")
        mock.write_file = AsyncMock(return_value=True)
        yield mock


class TestContainers:
    """Tests for POST /api/containers/ endpoints."""

    def test_create_container_success(self, client, auth_headers, mock_orchestrator):
        response = client.post("/api/containers/", json={
            "osType": "alpine"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["containerId"] == "mock-container-123"
        mock_orchestrator.create.assert_called_once()

    def test_create_container_unauthenticated(self, client, mock_orchestrator):
        response = client.post("/api/containers/", json={
            "osType": "alpine"
        })
        assert response.status_code == 401

    def test_get_container(self, client, mock_orchestrator):
        response = client.get("/api/containers/mock-container-123")
        assert response.status_code == 200
        data = response.json()
        assert data["containerId"] == "mock-container-123"

    def test_remove_container_success(self, client, auth_headers, mock_orchestrator):
        response = client.delete("/api/containers/mock-container-123", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_exec_command(self, client, mock_orchestrator):
        response = client.post("/api/containers/mock-container-123/exec", json={
            "command": "echo test"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["output"] == "test output"

    def test_snapshot_container(self, client, mock_orchestrator):
        response = client.post("/api/containers/mock-container-123/snapshot", json={
            "name": "Test Snapshot"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["snapshotId"] == "mock-snapshot-123"

    def test_list_files(self, client, mock_orchestrator):
        response = client.get("/api/containers/mock-container-123/files")
        assert response.status_code == 200
        assert len(response.json()["files"]) == 2

    def test_read_file(self, client, mock_orchestrator):
        response = client.get("/api/containers/mock-container-123/files/read?path=/file1.txt")
        assert response.status_code == 200
        assert response.json()["content"] == "file content"

    def test_write_file(self, client, mock_orchestrator):
        response = client.post("/api/containers/mock-container-123/files/write", json={
            "path": "/file1.txt",
            "content": "new content"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True
