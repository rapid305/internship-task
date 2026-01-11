from typing import Any

from fastapi import HTTPException, status


class AppHTTPException(HTTPException):
    status_code: int | None = None
    default_detail: str | None = None

    def __init__(self):
        if self.status_code is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define status_code")
        if self.default_detail is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define default_detail")
        super().__init__(
            status_code=self.status_code,
            detail=self.default_detail,
        )


class BadRequestDataException(AppHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad Request"


class DaoNotFoundError(Exception):
    def __init__(self, resource_name: str, identifier: Any) -> None:
        self.resource_name = resource_name
        self.identifier = identifier
        super().__init__(f"{resource_name} with id {identifier} not found")


class DaoAttributeError(Exception):
    def __init__(self, model_name: str, attribute: str) -> None:
        self.model_name = model_name
        self.attribute = attribute
        super().__init__(f"'{model_name}' object has no attribute '{attribute}'")
