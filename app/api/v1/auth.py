from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.background.tasks import send_welcome_email
from app.core.responses import success_response
from app.dependencies.auth import get_current_active_user, get_user_service
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service),
):
    user = await service.register(
        email=data.email, username=data.username, password=data.password
    )
    background_tasks.add_task(send_welcome_email, user.email, user.username)
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Registration successful",
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login")
async def login(
    data: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    access_token, refresh_token = await service.authenticate(data.email, data.password)
    return success_response(
        data=TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        ).model_dump(),
        message="Login successful",
    )


@router.post("/refresh")
async def refresh_tokens(
    data: RefreshRequest,
    service: UserService = Depends(get_user_service),
):
    access_token, refresh_token = await service.refresh_tokens(data.refresh_token)
    return success_response(
        data=TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        ).model_dump(),
        message="Tokens refreshed",
    )


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    service: UserService = Depends(get_user_service),
):
    await service.logout(data.refresh_token)
    return success_response(message="Logged out successfully")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(),
        message="Current user retrieved",
    )
