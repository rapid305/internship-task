import typing
from uuid import UUID

from fastapi import APIRouter, Depends, Security, status

from app.core.security import service_token_scheme
from app.transactions.api.service_token_dependency import (
    get_service_token_payload,
    get_user_uuid_from_token,
)
from app.transactions.api.transactions_dependencies import get_transaction_service
from app.transactions.schemas import RequestTransactionModel, TransactionModel
from app.transactions.service.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get(
    "/",
    response_model=typing.Optional[list[TransactionModel]] | None,
    status_code=status.HTTP_200_OK,
    dependencies=[Security(service_token_scheme), Depends(get_service_token_payload)],
)
async def get_transactions(
    user_uuid: typing.Optional[UUID] = None,
    transactions_service: TransactionService = Depends(get_transaction_service),
) -> typing.List[TransactionModel]:
    return await transactions_service.get_user_transactions(user_uuid=user_uuid)


@router.post(
    "/",
    response_model=typing.Optional[TransactionModel] | None,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Security(service_token_scheme), Depends(get_service_token_payload)],
)
async def post_transaction(
    transaction_data: RequestTransactionModel,
    user_uuid: UUID = Depends(get_user_uuid_from_token),
    transactions_service: TransactionService = Depends(get_transaction_service),
):
    return await transactions_service.create_transaction(user_uuid=user_uuid, transaction_data=transaction_data)


@router.patch(
    "/{transaction_uuid}",
    response_model=typing.Optional[TransactionModel] | None,
    dependencies=[Security(service_token_scheme), Depends(get_service_token_payload)],
)
async def patch_rollback_transaction(
    transaction_uuid: UUID,
    user_uuid: UUID = Depends(get_user_uuid_from_token),
    transactions_service: TransactionService = Depends(get_transaction_service),
):
    return await transactions_service.update_transaction(user_uuid=user_uuid, transaction_uuid=transaction_uuid)
