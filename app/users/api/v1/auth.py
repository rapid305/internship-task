from datetime import timedelta
from typing import Any, Dict

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import ServiceTokenRequest
from app.core.security import oauth2_scheme
from app.users.dao.users_dao import UsersDAO
from app.users.db.db_config import get_async_session
from app.users.schemas.auth_schemas import LoginRequest, Token
from app.users.service.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_service_jwt,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/read-access-token")
async def read_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return {"token": token}


@router.post("/token", response_model=Token)
async def login_for_access_token(payload: LoginRequest):
    """
    Accessing token by email field

    Args:
        email field

    Return:
        Access token by specific email
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload.email, "aud": "client"},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token)


@router.post("/service-token")
async def get_service_token(
    payload: ServiceTokenRequest,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Endpoint for receive service token
    1. We are sending request for another service with our user token.
    2. Decode received token to get data, handle if exception ect.
    3. From token we are take user info and sending request to database for finding if it real email or not
    4. After this we pack our data id, what service , email ... and creating service token
    5. Return service token

    Args:
        payload: user access token , target-service ( in our app its "transactions" )
        session: to make request to UsersDao (to find if email is real)

    Return:
        service-token
        for_service (data from token)
        user_id
    """
    try:
        user_payload = jwt.decode(
            payload.user_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="client",
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid user token: {str(e)}")

    user_email = user_payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid user token: no subject (user_email)")

    users_dao = UsersDAO(session)
    user = await users_dao.get_by_email(user_email)

    if not user:
        raise HTTPException(status_code=404, detail=f"User with email '{user_email}' not found")

    service_token = create_service_jwt(
        original_user_id=str(user.uuid),
        requesting_service="users",
        target_service=payload.target_service,
        user_context={
            "email": user_email,
            "user_uuid": str(user.uuid),
        },
    )

    return {
        "service_token": service_token,
        "for_service": payload.target_service,
        "user_id": str(user.uuid),
    }
