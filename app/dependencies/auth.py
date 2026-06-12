import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.core.exceptions import ForbiddenException, InactiveUserException, InvalidTokenException
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.user import UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: UserService = Depends(get_user_service),
) -> User:
    if not credentials:
        raise InvalidTokenException("No token provided")
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise InvalidTokenException("Not an access token")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise InvalidTokenException("Invalid token subject")
    return await service.get_by_id(user_id)


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise InactiveUserException()
    return user


async def require_superuser(
    user: User = Depends(get_current_active_user),
) -> User:
    if not user.is_superuser:
        raise ForbiddenException("Superuser access required")
    return user
