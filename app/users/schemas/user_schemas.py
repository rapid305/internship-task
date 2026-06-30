import typing
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.schemas import CurrencyEnum


class UserStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class RequestUserModel(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("email must be a string")
        return v.strip().replace(" ", "").lower()

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("password must be a string")
        password_bytes = v.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("password cannot be longer than 72 bytes when encoded in UTF-8")
        if len(password_bytes) < 8:
            raise ValueError("password must be at least 8 bytes when encoded in UTF-8")
        return v


class RequestUserUpdateModel(BaseModel):
    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class ResponseUserModel(BaseModel):
    uuid: typing.Optional[UUID]
    email: typing.Optional[str] = None
    password: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None
    user_balance: typing.Optional[typing.List[ResponseUserBalanceModel]] = None

    model_config = ConfigDict(from_attributes=True)


class CreateUserModel(BaseModel):
    email: typing.Optional[str] = None
    password: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None
    user_balance: typing.Optional[typing.List[ResponseUserBalanceModel]] = None


class UserModel(BaseModel):
    uuid: typing.Optional[UUID]
    password: typing.Optional[str] = None
    email: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserBalanceModel(BaseModel):
    uuid: typing.Optional[UUID]
    user_uuid: typing.Optional[UUID] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    def validate_not_negative(self, values):
        if "amount" in values and values.get("amount"):
            if values["amount"] < 0:
                raise ValueError("Amount cannot be negative")

        return values


class UserFilters(BaseModel):
    uuid: typing.Optional[UUID] = None
    email: typing.Optional[str] = None
    status: typing.Optional[str] = None
