from fastapi.security import HTTPBearer

oauth2_scheme = HTTPBearer(
    scheme_name="AccessToken",
    description="Insert user JWT из /v1/auth/token",
)

service_token_scheme = HTTPBearer(
    scheme_name="ServiceToken",
    description="Insert service JWT",
)
