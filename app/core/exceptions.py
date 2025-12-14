from fastapi import HTTPException


class AppHTTPException(HTTPException):
    status_code: int | None = None
    default_detail: str | None = None

    def __init__(self):
        if self.status_code is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define status_code"
            )
        if self.default_detail is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define default_detail"
            )
        super().__init__(
            status_code=self.status_code,
            detail=self.default_detail,
        )