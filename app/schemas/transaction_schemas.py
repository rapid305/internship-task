import typing
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import CurrencyEnum


class TransactionStatusEnum(StrEnum):
    processed = "PROCESSED"
    roll_backed = "ROLLBACKED"


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnum
    amount: Decimal


class TransactionModel(BaseModel):
    uuid: typing.Optional[UUID]
    user_uuid: typing.Optional[UUID] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[Decimal] = None
    status: typing.Optional[TransactionStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None


class CreateTransactionModel(BaseModel):
    user_uuid: UUID
    currency: CurrencyEnum
    amount: Decimal
    status: TransactionStatusEnum


class TaskReturn(BaseModel):
    registered_users_count: int
    registered_and_deposit_users_count: int
    registered_and_not_rollbacked_deposit_users_count: int
    not_rollbacked_deposit_amount: Decimal
    not_rollbacked_withdraw_amount: Decimal
    transactions_count: int
    not_rollbacked_transactions_count: int
