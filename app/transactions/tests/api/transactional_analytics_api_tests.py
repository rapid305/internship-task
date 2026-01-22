from unittest.mock import AsyncMock, patch

import pytest
from fastapi.exceptions import HTTPException
from taskiq.exceptions import TaskiqResultTimeoutError

from app.transactions.api.v1.analytics import get_transaction_analysis_result, run_analysis


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_run_analysis_success(self):
        """Test successful analysis task submission."""
        with patch("app.transactions.api.v1.analytics.get_transaction_analysis.kiq") as mock_kiq:
            mock_task = AsyncMock()
            mock_task.task_id = "test_task_123"
            mock_kiq.return_value = mock_task

            result = await run_analysis()

            assert result["task_id"] == "test_task_123"
            assert result["status"] == "queued"
            assert "message" in result

    @pytest.mark.asyncio
    async def test_run_analysis_exception_handling(self):
        """Test error handling in run_analysis endpoint."""
        with patch("app.transactions.api.v1.analytics.get_transaction_analysis.kiq") as mock_kiq:
            mock_kiq.side_effect = Exception("Queue error")

            with pytest.raises(HTTPException) as exc_info:
                await run_analysis()

            assert exc_info.value.status_code == 500
            assert "Queue error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_result_completed(self):
        """Test retrieving completed task result."""
        with patch("app.transactions.api.v1.analytics.broker.result_backend.get_result") as mock_get_result:
            test_data = [{"week_number": 1, "users": 10}]
            mock_get_result.return_value = test_data

            result = await get_transaction_analysis_result("task_123")

            assert result["task_id"] == "task_123"
            assert result["status"] == "completed"
            assert result["data"] == test_data

    @pytest.mark.asyncio
    async def test_get_result_processing(self):
        """Test retrieving task result when still processing."""
        with patch("app.transactions.api.v1.analytics.broker.result_backend.get_result") as mock_get_result:
            mock_get_result.side_effect = TaskiqResultTimeoutError()

            result = await get_transaction_analysis_result("task_123")

            assert result["task_id"] == "task_123"
            assert result["status"] == "processing"
            assert "data" not in result

    @pytest.mark.asyncio
    async def test_get_result_backend_error(self):
        """Test backend error when retrieving task result."""
        with patch("app.transactions.api.v1.analytics.broker.result_backend.get_result") as mock_get_result:
            mock_get_result.side_effect = Exception("Backend error")

            with pytest.raises(HTTPException) as exc_info:
                await get_transaction_analysis_result("task_123")

            assert exc_info.value.status_code == 500
            assert "Backend error" in str(exc_info.value.detail)
