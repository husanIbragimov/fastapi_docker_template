import uuid


def make_register_payload(
    email: str | None = None,
    username: str | None = None,
    password: str = "Password123!",
) -> dict:
    return {
        "email": email or unique_email(),
        "username": username or unique_username(),
        "password": password,
    }


def unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


def unique_username() -> str:
    return f"user_{uuid.uuid4().hex[:8]}"
