from fastapi import status


class AppException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "Resource not found"


class AlreadyExistsException(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "ALREADY_EXISTS"
    message = "Resource already exists"


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action"


class InvalidCredentialsException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"


class InvalidTokenException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_TOKEN"
    message = "Token is invalid or expired"


class InactiveUserException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "INACTIVE_USER"
    message = "User account is inactive"


class DatabaseException(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "DATABASE_ERROR"
    message = "A database error occurred"
