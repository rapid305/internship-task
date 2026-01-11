import pytest
from fastapi import status

from app.users.exceptions import UserAlreadyExistsException, UserNotExistsException


class TestUsersAPI:
    """Users API tests."""

    @pytest.mark.asyncio
    async def test_get_users_success(self, client, mock_user_service, sample_user_data):
        """Test GET /users returns users successfully."""
        mock_user_service.get_users.return_value = [sample_user_data]

        response = await client.get("/v1/users")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["email"] == "test@example.com"
        assert data[0]["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_get_users_with_query_params(self, client, mock_user_service, sample_user_data, test_uuid):
        """Test GET /users with query parameters."""
        user_uuid = test_uuid
        mock_user_service.get_users.return_value = [sample_user_data]

        response = await client.get(f"/v1/users?user_uuid={user_uuid}&email=test@example.com&status=ACTIVE")

        assert response.status_code == status.HTTP_200_OK
        assert mock_user_service.get_users.called

    @pytest.mark.asyncio
    async def test_get_users_empty_response(self, client, mock_user_service):
        """Test GET /users returns empty list."""
        mock_user_service.get_users.return_value = []

        response = await client.get("/v1/users")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_post_user_success(self, client, mock_user_service, sample_user_data):
        """Test POST /users creates user successfully."""
        request_data = {"email": "new@example.com"}
        mock_user_service.create_user.return_value = sample_user_data

        response = await client.post("/v1/users", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        assert "email" in response.json()
        assert mock_user_service.create_user.called

    @pytest.mark.asyncio
    async def test_post_user_missing_email(self, client, mock_user_service):
        """Test POST /users without email field."""
        request_data = {}

        response = await client.post("/v1/users", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_user_service.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_patch_user_success(self, client, mock_user_service, sample_user_data, test_uuid):
        """Test PATCH /users/{uuid} updates status successfully."""
        user_uuid = test_uuid
        request_data = {"status": "BLOCKED"}
        sample_user_data["status"] = "BLOCKED"
        mock_user_service.change_status.return_value = sample_user_data

        response = await client.patch(f"/v1/users/{user_uuid}", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "BLOCKED"
        assert mock_user_service.change_status.called

    @pytest.mark.asyncio
    async def test_patch_user_invalid_uuid(self, client, mock_user_service):
        """Test PATCH /users/{uuid} with invalid UUID format."""
        invalid_uuid = "not-a-uuid"
        request_data = {"status": "ACTIVE"}

        response = await client.patch(f"/v1/users/{invalid_uuid}", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_user_service.change_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_patch_user_invalid_status_value(self, client, mock_user_service, test_uuid):
        """Test PATCH /users/{uuid} with invalid status value."""
        user_uuid = test_uuid
        request_data = {"status": "INVALID_STATUS"}

        response = await client.patch(f"/v1/users/{user_uuid}", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_user_service.change_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_patch_user_empty_status(self, client, mock_user_service, test_uuid):
        """Test PATCH /users/{uuid} with empty status string."""
        user_uuid = test_uuid
        request_data = {"status": ""}

        response = await client.patch(f"/v1/users/{user_uuid}", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_user_service.change_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_patch_user_not_found(self, client, mock_user_service, test_uuid):
        """Test PATCH /users/{uuid} when user doesn't exist."""
        user_uuid = test_uuid
        request_data = {"status": "ACTIVE"}

        mock_user_service.change_status.side_effect = UserNotExistsException()

        response = await client.patch(f"/v1/users/{user_uuid}", json=request_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_post_user_already_exists(self, client, mock_user_service):
        """Test POST /users when user already exists."""
        request_data = {"email": "existing@example.com"}

        mock_user_service.create_user.side_effect = UserAlreadyExistsException()

        response = await client.post("/v1/users", json=request_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_users_response_structure(self, client, mock_user_service, sample_user_data):
        """Test GET /users response has correct structure."""
        mock_user_service.get_users.return_value = [sample_user_data]

        response = await client.get("/v1/users")

        data = response.json()[0]
        expected_fields = {"uuid", "email", "status", "created", "updated", "user_balance"}
        assert set(data.keys()) == expected_fields
        assert isinstance(data["user_balance"], list)
