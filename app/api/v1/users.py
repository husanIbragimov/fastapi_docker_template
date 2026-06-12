import uuid

from fastapi import APIRouter, Depends, status

from app.core.responses import success_response
from app.dependencies.auth import get_current_active_user, get_user_service, require_superuser
from app.dependencies.pagination import pagination_params
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(
    pagination: PaginationParams = Depends(pagination_params),
    _: User = Depends(require_superuser),
    service: UserService = Depends(get_user_service),
):
    result = await service.list_users(page=pagination.page, size=pagination.size)
    return success_response(data=result, message="Users retrieved")


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(),
        message="Profile retrieved",
    )


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    _: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    user = await service.get_by_id(user_id)
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="User retrieved",
    )


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    user = await service.update_user(user_id, data, requester=current_user)
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="User updated",
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    await service.delete_user(user_id, requester=current_user)
