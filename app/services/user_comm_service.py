from typing import Any, Dict
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

from app.core.schemas import ServiceTokenRequest
from app.transactions.settings import settings


class UserService:
    """
    Service for communicating with users-service to exchange user tokens for service tokens.
    """

    def __init__(self) -> None:
        self.users_service_path = settings.USERS_SERVICE_PATH
        self.default_users_service_url = settings.USERS_SERVICE_URL

    def users_service_url(self) -> str:
        return urljoin(self.default_users_service_url, self.users_service_path)

    @staticmethod
    def _raise_http_exception_for_response(response: httpx.Response) -> None:
        """Raise an HTTPException based on users-service response."""
        try:
            error_detail = response.json()
        except ValueError:
            error_detail = {"error": response.text or "Unknown error"}

        raise HTTPException(status_code=response.status_code, detail=error_detail)

    def _handle_users_service_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process the response from users-service."""
        if response.status_code != 200:
            self._raise_http_exception_for_response(response)

        data = response.json()

        if "service_token" not in data:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Invalid response from users service",
                    "message": "Missing required field: service_token",
                },
            )

        return data

    async def get_service_token(self, payload: ServiceTokenRequest) -> Dict[str, Any]:
        """
        Exchange a user token for a service token.

        Calls users-service /token/service endpoint to obtain a service token
        that can be used for inter-service communication.

        Args:
            payload: ServiceTokenRequest with user_token and target_service

        Returns:
            Dictionary with service_token and metadata (e.g., for_service, user_id)

        Raises:
            HTTPException: If users-service is unavailable or returns an error
        """
        async with httpx.AsyncClient() as client:
            url = self.users_service_url()
            response = await client.post(
                url,
                json={"user_token": payload.user_token, "target_service": payload.target_service},
            )
            return self._handle_users_service_response(response)

    async def get_service_token_for_request(self, user_token: str, target_service: str = "transactions") -> str:
        """
        Convenience method: exchange user token for service token and return just the token string.

        Args:
            user_token: User's JWT token from Authorization header (without "Bearer " prefix)
            target_service: Name of the target service (default: "transactions")

        Returns:
            Service token string ready to use in Authorization header

        Raises:
            HTTPException: If exchange fails
        """
        token_data = await self.get_service_token(
            ServiceTokenRequest(user_token=user_token, target_service=target_service)
        )
        return token_data["service_token"]


user_server_token_service = UserService()
