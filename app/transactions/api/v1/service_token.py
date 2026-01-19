from typing import Any, Dict
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.schemas import ServiceTokenRequest, oauth2_scheme
from app.transactions.settings import settings

USERS_SERVICE_PATH = settings.USERS_SERVICE_PATH
DEFAULT_USERS_SERVICE_URL = settings.USERS_SERVICE_URL


def users_service_url():
    return urljoin(DEFAULT_USERS_SERVICE_URL, USERS_SERVICE_PATH)


async def _call_users_service(client: httpx.AsyncClient, url: str, payload: ServiceTokenRequest) -> httpx.Response:
    """Calling the users-service to obtain a service token"""
    return await client.post(url, json={"user_token": payload.user_token, "target_service": payload.target_service})


def _handle_users_service_response(response: httpx.Response) -> Dict[str, Any]:
    """Processing the response from the users service"""
    if response.status_code != 200:
        _raise_http_exception_for_response(response)

    data = response.json()

    if "service_token" not in data:
        raise HTTPException(
            status_code=500,
            detail={"error": "Invalid response from users service", "message": "Missing required field: service_token"},
        )

    return data


def _raise_http_exception_for_response(response: httpx.Response) -> None:
    """Creating an HTTPException based on a response from the users-service"""
    try:
        error_detail = response.json()
    except ValueError:
        error_detail = {"error": response.text or "Unknown error"}

    raise HTTPException(status_code=response.status_code, detail=error_detail)


router = APIRouter(prefix="/transaction-auth", tags=["transaction-auth"])


@router.get("/me-token")
async def read_token(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return {"token": token}


@router.post("/service-token")
async def get_service_token(payload: ServiceTokenRequest) -> Dict[str, Any]:
    """
    Getting a service token for inter-service communication.

    This endpoint proxies a request to the users service to convert
     the client token into a service token.

    Args:
     payload: A request object with the following fields:
     - user_token: A valid JWT of the client from the users service
     - target_service: The name of the target service (for example, "transactions")

    Returns:
     A dictionary with a service token and metadata:
     - service_token: JWT for inter-service communication
     - for_service: Target service
     - user_id: User ID

    Raises:
     HTTPException:
         - 401: Invalid user_token
         - 503: Users-service is unavailable
         - 500: Incorrect response from users-service
    """

    url = users_service_url()

    try:
        async with httpx.AsyncClient() as client:
            response = await _call_users_service(client, url, payload)
            return _handle_users_service_response(response)

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=503,
            detail={"error": "Users service unavailable", "message": str(error), "service_url": users_service_url},
        )
