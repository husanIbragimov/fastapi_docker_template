import uuid
from typing import Any

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, verify_password
from app.cache.backend import redis_delete, redis_get, redis_set
from app.cache.decorator import cache
from app.core.config import settings
from app.core.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    NotFoundException,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserUpdate
from app.utils.pagination import PaginationParams, build_pagination_meta

_REFRESH_TOKEN_PREFIX = "refresh_token"


def _refresh_key(jti: str) -> str:
    return f"{_REFRESH_TOKEN_PREFIX}:{jti}"


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def register(self, email: str, username: str, password: str) -> User:
        if await self._repo.email_exists(email):
            raise AlreadyExistsException("Email already registered")
        if await self._repo.username_exists(username):
            raise AlreadyExistsException("Username already taken")
        return await self._repo.create(
            email=email,
            username=username,
            hashed_password=hash_password(password),
        )

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        user = await self._repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        if not user.is_active:
            raise InactiveUserException()
        return await self._issue_tokens(str(user.id))

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidTokenException("Not a refresh token")

        jti: str = payload["jti"]
        stored = await redis_get(_refresh_key(jti))
        if stored is None:
            raise InvalidTokenException("Refresh token has been revoked")

        await redis_delete(_refresh_key(jti))
        return await self._issue_tokens(payload["sub"])

    @staticmethod
    async def logout(refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                await redis_delete(_refresh_key(jti))
        except InvalidTokenException:
            pass  # already invalid — logout is idempotent

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    @cache(ttl=300, namespace="user_list")
    async def list_users(self, page: int, size: int) -> dict[str, Any]:
        params = PaginationParams(page=page, size=size)
        users = await self._repo.get_all(offset=params.offset, limit=params.limit)
        total = await self._repo.count()
        meta = build_pagination_meta(page=page, size=size, total=total)
        return {
            "users": [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "username": u.username,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat(),
                }
                for u in users
            ],
            "meta": meta.model_dump(),
        }

    async def update_user(
        self, user_id: uuid.UUID, data: UserUpdate, requester: User
    ) -> User:
        if not requester.is_superuser and requester.id != user_id:
            raise ForbiddenException()
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        if (
            data.email
            and data.email != user.email
            and await self._repo.email_exists(data.email)
        ):
            raise AlreadyExistsException("Email already in use")
        if (
            data.username
            and data.username != user.username
            and await self._repo.username_exists(data.username)
        ):
            raise AlreadyExistsException("Username already taken")
        updated = await self._repo.update_by_id(
            user_id, **data.model_dump(exclude_none=True)
        )
        return updated  # type: ignore[return-value]

    async def delete_user(self, user_id: uuid.UUID, requester: User) -> None:
        if not requester.is_superuser and requester.id != user_id:
            raise ForbiddenException()
        deleted = await self._repo.delete_by_id(user_id)
        if not deleted:
            raise NotFoundException("User not found")

    @staticmethod
    async def _issue_tokens(user_id: str) -> TokenResponse:
        access_token = create_access_token(subject=user_id)
        refresh_token, jti = create_refresh_token(subject=user_id)
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await redis_set(_refresh_key(jti), {"user_id": user_id}, ttl=ttl)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
