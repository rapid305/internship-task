from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.users.settings import settings

SECRET_KEY = settings.get("SECRET_KEY")
ALGORITHM = settings.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = settings.get("ACCESS_TOKEN_EXPIRE_MINUTES")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_truncated = password[:72]
    password_bytes = password_truncated.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create access token

    Args:
        data: Data which supposed to be included in token
        expires_delta: Expiring time of token

    Returns:
        encoded access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": int(expire.timestamp()), "iat": int(datetime.now(timezone.utc).timestamp())})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_service_jwt(
    original_user_id: str,
    requesting_service: str,
    target_service: str,
    user_context: dict,
    expires_delta: timedelta = timedelta(minutes=15),
) -> str:
    """
    Create service jwt for communicating between services

    Args:
        original_user_id: ID of user (its UUID field from db)
        requesting_service: Name of service (usually "users")
        target_service: Name of target service (for example transactions)
        user_context: Context of data (email and others fields)
        expires_delta: Time of expire token

    Returns:
        Encoded token for service
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(original_user_id),
        "aud": target_service,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "from_service": requesting_service,
        "user_context": user_context,
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
