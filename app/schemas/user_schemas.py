import typing
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.schemas import CurrencyEnum


class UserStatusEnum(StrEnum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class RequestUserModel(BaseModel):
    email: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("email must be a string")
        return v.strip().replace(" ", "")


class RequestUserUpdateModel(BaseModel):
    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ResponseUserModel(BaseModel):
    uuid: typing.Optional[UUID]
    email: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None
    user_balance: typing.Optional[typing.List[ResponseUserBalanceModel]] = None

    model_config = ConfigDict(from_attributes=True)


class CreateUserModel(BaseModel):
    email: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None
    user_balance: typing.Optional[typing.List[ResponseUserBalanceModel]] = None


class UserModel(BaseModel):
    uuid: typing.Optional[UUID]
    email: typing.Optional[str] = None
    status: typing.Optional[UserStatusEnum] = None
    created: typing.Optional[datetime] = None
    updated: typing.Optional[datetime] = None


class UserBalanceModel(BaseModel):
    uuid: typing.Optional[UUID]
    user_uuid: typing.Optional[UUID] = None
    currency: typing.Optional[CurrencyEnum] = None
    amount: typing.Optional[float] = None

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
