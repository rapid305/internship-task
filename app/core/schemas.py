from enum import StrEnum

from fastapi.security import HTTPBearer
from pydantic import BaseModel


class CurrencyEnum(StrEnum):
    USD = "USD"
    EUR = "EUR"
    AUD = "AUD"
    CAD = "CAD"
    ARS = "ARS"
    PLN = "PLN"
    BTC = "BTC"
    ETH = "ETH"
    DOGE = "DOGE"
    USDT = "USDT"


class ServiceTokenRequest(BaseModel):
    user_token: str
    target_service: str


oauth2_scheme = HTTPBearer(
    scheme_name="AccessToken",
    description="Insert user JWT из /v1/auth/token",
)

service_token_scheme = HTTPBearer(
    scheme_name="ServiceToken",
    description="Insert service JWT из /v1/transaction-auth/service-token",
)
