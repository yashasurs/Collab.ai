"""Tests for authentication endpoints."""

import pytest


class TestRegister:
    """Tests for POST /api/auth/register."""

    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepassword123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should not be exposed

    def test_register_duplicate_username(self, client, test_user):
        response = client.post("/api/auth/register", json={
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client, test_user):
        response = client.post("/api/auth/register", json={
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123",
        })
        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        response = client.post("/api/auth/register", json={
            "username": "incomplete",
        })
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client, test_user):
        response = client.post("/api/auth/login", data={
            "username": test_user.username,
            "password": "testpassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/api/auth/login", data={
            "username": test_user.username,
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", data={
            "username": "ghostuser",
            "password": "password123",
        })
        assert response.status_code == 401


class TestMe:
    """Tests for GET /api/auth/me."""

    def test_me_authenticated(self, client, test_user, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_me_unauthenticated(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client):
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token-here"
        })
        assert response.status_code == 401


class TestPasswordSecurity:
    """Tests for password hashing and verification."""

    def test_password_hash_is_different(self):
        from app.auth.security import get_password_hash
        hash1 = get_password_hash("samepassword")
        hash2 = get_password_hash("samepassword")
        # bcrypt generates unique salts, so hashes differ
        assert hash1 != hash2

    def test_verify_correct_password(self):
        from app.auth.security import get_password_hash, verify_password
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        from app.auth.security import get_password_hash, verify_password
        hashed = get_password_hash("mypassword")
        assert verify_password("wrongpassword", hashed) is False


class TestJWT:
    """Tests for JWT token creation and validation."""

    def test_create_token(self):
        from app.auth.security import create_access_token
        token = create_access_token(subject="user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self):
        from app.auth.security import create_access_token, SECRET_KEY, ALGORITHM
        from jose import jwt
        token = create_access_token(subject="user-123")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user-123"
        assert "exp" in payload
