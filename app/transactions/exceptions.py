from fastapi import status

from app.core.exceptions import AppHTTPException


class NegativeBalanceException(AppHTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Negative balance"


class TransactionNotExistsException(AppHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Transaction does not exist"


class TransactionDoesNotBelongToUserException(AppHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Transaction does not belong to user"


class TransactionAlreadyRollbackedException(AppHTTPException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Transaction already rolled back"
