from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.transactions.schemas import TransactionAnalyticsSchema
from app.transactions.tasks.analyze_task import get_transaction_analysis, has_non_zero_metrics


class TestAnalyzeTask:
    """Tests for the background analytics task."""

    def test_has_non_zero_metrics_detects_positive_int_fields(self):
        """Test that has_non_zero_metrics detects positive integer fields only."""
        metrics = TransactionAnalyticsSchema(
            registered_users_count=1,
            registered_and_deposit_users_count=0,
            registered_and_not_rollbacked_deposit_users_count=0,
            not_rollbacked_deposit_amount=Decimal("0"),
            not_rollbacked_withdraw_amount=Decimal("0"),
            transactions_count=0,
            not_rollbacked_transactions_count=0,
        )
        assert has_non_zero_metrics(metrics) is True

        metrics = TransactionAnalyticsSchema(
            registered_users_count=0,
            registered_and_deposit_users_count=0,
            registered_and_not_rollbacked_deposit_users_count=0,
            not_rollbacked_deposit_amount=Decimal("100.50"),
            not_rollbacked_withdraw_amount=Decimal("0"),
            transactions_count=0,
            not_rollbacked_transactions_count=0,
        )
        assert has_non_zero_metrics(metrics) is False

        metrics = TransactionAnalyticsSchema(
            registered_users_count=0,
            registered_and_deposit_users_count=0,
            registered_and_not_rollbacked_deposit_users_count=0,
            not_rollbacked_deposit_amount=Decimal("0"),
            not_rollbacked_withdraw_amount=Decimal("0"),
            transactions_count=5,
            not_rollbacked_transactions_count=0,
        )
        assert has_non_zero_metrics(metrics) is True

    @pytest.mark.asyncio
    async def test_get_transaction_analysis_filters_zero_weeks(self):
        """Test that get_transaction_analysis filters out weeks with zero metrics."""
        with patch("app.transactions.tasks.analyze_task.WEEKS", 4), patch(
            "app.transactions.tasks.analyze_task.DAYS", 7
        ), patch("app.transactions.tasks.analyze_task.async_session_maker") as mock_session_maker, patch(
            "app.transactions.tasks.analyze_task.get_metrics"
        ) as mock_get_metrics, patch(
            "app.transactions.tasks.analyze_task.datetime"
        ) as mock_datetime:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            mock_datetime.now.return_value = datetime(2025, 1, 31, tzinfo=timezone.utc)

            week1_data = TransactionAnalyticsSchema(
                registered_users_count=10,
                registered_and_deposit_users_count=5,
                registered_and_not_rollbacked_deposit_users_count=4,
                not_rollbacked_deposit_amount=Decimal("1000.50"),
                not_rollbacked_withdraw_amount=Decimal("500.25"),
                transactions_count=20,
                not_rollbacked_transactions_count=18,
            )

            week2_data = TransactionAnalyticsSchema(
                registered_users_count=0,
                registered_and_deposit_users_count=0,
                registered_and_not_rollbacked_deposit_users_count=0,
                not_rollbacked_deposit_amount=Decimal("0"),
                not_rollbacked_withdraw_amount=Decimal("0"),
                transactions_count=0,
                not_rollbacked_transactions_count=0,
            )

            week3_data = TransactionAnalyticsSchema(
                registered_users_count=0,
                registered_and_deposit_users_count=0,
                registered_and_not_rollbacked_deposit_users_count=0,
                not_rollbacked_deposit_amount=Decimal("500.75"),
                not_rollbacked_withdraw_amount=Decimal("0"),
                transactions_count=0,
                not_rollbacked_transactions_count=0,
            )

            week4_data = TransactionAnalyticsSchema(
                registered_users_count=0,
                registered_and_deposit_users_count=0,
                registered_and_not_rollbacked_deposit_users_count=0,
                not_rollbacked_deposit_amount=Decimal("0"),
                not_rollbacked_withdraw_amount=Decimal("0"),
                transactions_count=15,
                not_rollbacked_transactions_count=0,
            )

            mock_get_metrics.side_effect = [week1_data, week2_data, week3_data, week4_data]

            result = await get_transaction_analysis()

            assert len(result) == 2
            assert result[0]["week_number"] == 1
            assert result[1]["week_number"] == 4

    @pytest.mark.asyncio
    async def test_get_transaction_analysis_sorts_by_week_number(self):
        """Test that get_transaction_analysis sorts results by week number."""
        with patch("app.transactions.tasks.analyze_task.WEEKS", 3), patch(
            "app.transactions.tasks.analyze_task.DAYS", 7
        ), patch("app.transactions.tasks.analyze_task.async_session_maker") as mock_session_maker, patch(
            "app.transactions.tasks.analyze_task.get_metrics"
        ) as mock_get_metrics, patch(
            "app.transactions.tasks.analyze_task.datetime"
        ) as mock_datetime:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_datetime.now.return_value = datetime(2025, 1, 31, tzinfo=timezone.utc)

            week3_data = TransactionAnalyticsSchema(
                registered_users_count=30,
                registered_and_deposit_users_count=0,
                registered_and_not_rollbacked_deposit_users_count=0,
                not_rollbacked_deposit_amount=Decimal("0"),
                not_rollbacked_withdraw_amount=Decimal("0"),
                transactions_count=0,
                not_rollbacked_transactions_count=0,
            )
            week1_data = TransactionAnalyticsSchema(
                registered_users_count=10,
                registered_and_deposit_users_count=0,
                registered_and_not_rollbacked_deposit_users_count=0,
                not_rollbacked_deposit_amount=Decimal("0"),
                not_rollbacked_withdraw_amount=Decimal("0"),
                transactions_count=0,
                not_rollbacked_transactions_count=0,
            )
            week2_data = TransactionAnalyticsSchema(
                registered_users_count=20,
                registered_and_deposit_users_count=0,
                registered_and_not_rollbacked_deposit_users_count=0,
                not_rollbacked_deposit_amount=Decimal("0"),
                not_rollbacked_withdraw_amount=Decimal("0"),
                transactions_count=0,
                not_rollbacked_transactions_count=0,
            )

            mock_get_metrics.side_effect = [week1_data, week2_data, week3_data]

            result = await get_transaction_analysis()

            week_numbers = [item["week_number"] for item in result]
            assert week_numbers == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_get_transaction_analysis_returns_correct_structure(self):
        """Test that get_transaction_analysis returns data with correct structure."""
        with patch("app.transactions.tasks.analyze_task.WEEKS", 1), patch(
            "app.transactions.tasks.analyze_task.DAYS", 7
        ), patch("app.transactions.tasks.analyze_task.async_session_maker") as mock_session_maker, patch(
            "app.transactions.tasks.analyze_task.get_metrics"
        ) as mock_get_metrics, patch(
            "app.transactions.tasks.analyze_task.datetime"
        ) as mock_datetime:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            test_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
            mock_datetime.now.return_value = test_date

            test_data = TransactionAnalyticsSchema(
                registered_users_count=25,
                registered_and_deposit_users_count=15,
                registered_and_not_rollbacked_deposit_users_count=12,
                not_rollbacked_deposit_amount=Decimal("1250.75"),
                not_rollbacked_withdraw_amount=Decimal("625.50"),
                transactions_count=45,
                not_rollbacked_transactions_count=40,
            )

            mock_get_metrics.return_value = test_data

            result = await get_transaction_analysis()

            assert len(result) == 1
            item = result[0]

            assert item["week_number"] == 1
            assert item["start_date"] == "2025-01-24"
            assert item["end_date"] == "2025-01-31"
            assert item["not_rollbacked_deposit_amount"] == Decimal("1250.75")
            assert item["not_rollbacked_withdraw_amount"] == Decimal("625.50")
            assert item["registered_users_count"] == 25
            assert item["registered_and_deposit_users_count"] == 15
            assert item["registered_and_not_rollbacked_deposit_users_count"] == 12
            assert item["transactions_count"] == 45
            assert item["not_rollbacked_transactions_count"] == 40
