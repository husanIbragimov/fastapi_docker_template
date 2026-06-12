import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password
from app.models.user import User
from tests.factories import make_register_payload, unique_email, unique_username


@pytest.mark.asyncio
async def test_get_my_profile(client: AsyncClient, auth_headers: dict, test_user: User) -> None:
    resp = await client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_id(
    client: AsyncClient, auth_headers: dict, test_user: User
) -> None:
    resp = await client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_nonexistent_user(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get(f"/api/v1/users/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_list_users_requires_superuser(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.get("/api/v1/users", headers=auth_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_list_users_as_superuser(
    client: AsyncClient, superuser_headers: dict, test_user: User
) -> None:
    resp = await client.get("/api/v1/users", headers=superuser_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "users" in body["data"]
    assert "meta" in body["data"]
    assert body["data"]["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_list_users_pagination(
    client: AsyncClient, superuser_headers: dict, test_user: User
) -> None:
    resp = await client.get("/api/v1/users?page=1&size=5", headers=superuser_headers)
    assert resp.status_code == 200
    meta = resp.json()["data"]["meta"]
    assert meta["page"] == 1
    assert meta["size"] == 5


@pytest.mark.asyncio
async def test_update_own_profile(
    client: AsyncClient, auth_headers: dict, test_user: User
) -> None:
    new_email = unique_email()
    resp = await client.patch(
        f"/api/v1/users/{test_user.id}",
        json={"email": new_email},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == new_email


@pytest.mark.asyncio
async def test_update_other_user_forbidden(
    client: AsyncClient, auth_headers: dict, superuser: User
) -> None:
    resp = await client.patch(
        f"/api/v1/users/{superuser.id}",
        json={"username": unique_username()},
        headers=auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_superuser_can_update_any_user(
    client: AsyncClient, superuser_headers: dict, test_user: User
) -> None:
    new_username = unique_username()
    resp = await client.patch(
        f"/api/v1/users/{test_user.id}",
        json={"username": new_username},
        headers=superuser_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == new_username


@pytest.mark.asyncio
async def test_delete_own_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    disposable = User(
        id=uuid.uuid4(),
        email=unique_email(),
        username=unique_username(),
        hashed_password=hash_password("Temp1234!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(disposable)
    await db_session.flush()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": disposable.email, "password": "Temp1234!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.delete(f"/api/v1/users/{disposable.id}", headers=headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_other_user_forbidden(
    client: AsyncClient, auth_headers: dict, superuser: User
) -> None:
    resp = await client.delete(f"/api/v1/users/{superuser.id}", headers=auth_headers)
    assert resp.status_code == 403
