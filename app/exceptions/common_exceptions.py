from fastapi import status

from app.core.exceptions import AppHTTPException


class BadRequestDataException(AppHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad Request"
