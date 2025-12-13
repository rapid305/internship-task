from fastapi import HTTPException, status


class AppHTTPException(HTTPException):
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_detail: str = "Application error"

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.default_detail,
        )
