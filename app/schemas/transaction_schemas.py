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
    amount: float


class TransactionModel(BaseModel):
    uuid: typing.Optional[UUID]
    user_uuid: typing.Optional[UUID] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[float] = None
    status: typing.Optional[TransactionStatusEnum] = None
    created: typing.Optional[datetime] = None


class CreateTransactionModel(BaseModel):
    user_uuid: typing.Optional[UUID] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[Decimal] = None
    status: typing.Optional[TransactionStatusEnum] = None
    created: typing.Optional[datetime] = None
