import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.factories import make_register_payload, unique_email, unique_username


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    payload = make_register_payload()
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == payload["email"]
    assert body["data"]["username"] == payload["username"]
    assert "hashed_password" not in body["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User) -> None:
    payload = make_register_payload(email="test@example.com", username=unique_username())
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, test_user: User) -> None:
    payload = make_register_payload(email=unique_email(), username="testuser")
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    payload = make_register_payload(email="not-an-email")
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    payload = make_register_payload(password="short")
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "Test1234!"},
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user: User) -> None:
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test1234!"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    new_data = resp.json()["data"]
    assert "access_token" in new_data
    # Token rotation: new refresh token must differ from the old one
    assert new_data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_reuse_fails(client: AsyncClient, test_user: User) -> None:
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test1234!"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]
    # First use — valid
    await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    # Second use of the same token must fail (rotation invalidated it)
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, test_user: User) -> None:
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "Test1234!"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 200

    # Token should no longer be usable after logout
    resp2 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp2.status_code == 401
