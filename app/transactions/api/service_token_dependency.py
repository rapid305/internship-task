from typing import Any, Dict
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from starlette.requests import Request

from app.transactions.settings import settings

SECRET_KEY = settings.get("SECRET_KEY")
ALGORITHM = settings.get("ALGORITHM")


async def get_service_token_payload(request: Request) -> Dict[str, Any]:
    """
    Check the service token and return the payload.

    Validates:
     - Token format (Bearer)
     - JWT signature
     - Audience (aud="transactions")
     - Expiration date (exp)

    Returns:
     payload: Token content, including user_id (sub) and other fields

    Raises:
     HTTPException: If the token is invalid or expired
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.replace("Bearer ", "", 1)

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="transactions",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience (expected 'transactions')",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_uuid_from_token(payload: Dict[str, Any] = Depends(get_service_token_payload)) -> UUID:
    """
    Extract the user_id (sub) from a validated service token.

    Returns:
        user_uuid: UUID of user

    Raises:
        HTTPException: if token don't consist 'sub'
    """
    user_uuid = payload.get("sub")
    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' (user_id) claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UUID(user_uuid)
