from fastapi import status

from app.core.exceptions import AppHTTPException


class UserAlreadyExistsException(AppHTTPException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "User already exists"


class UserNotExistsException(AppHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "User does not exist"


class UserAlreadyBlockedException(AppHTTPException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "User is already blocked"


class UserAlreadyActiveException(AppHTTPException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "User is already active"


class CreateTransactionForBlockedUserException(AppHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Cannot create transaction for blocked user"


class UpdateTransactionForBlockedUserException(AppHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Cannot update transaction for blocked user"
