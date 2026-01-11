import typing
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.transactions.api.transactions_dependencies import get_transaction_service
from app.transactions.schemas import RequestTransactionModel, TransactionModel
from app.transactions.service.transaction_service import TransactionService

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])


@router.get("/", response_model=typing.Optional[list[TransactionModel]] | None, status_code=status.HTTP_200_OK)
async def get_transactions(
    user_uuid: UUID = None,
    service: TransactionService = Depends(get_transaction_service),
) -> typing.List[TransactionModel]:
    return await service.get_user_transactions(user_uuid=user_uuid)


@router.post(
    "/{user_id}/transactions", response_model=typing.Optional[TransactionModel] | None, status_code=status.HTTP_200_OK
)
async def post_transaction(
    user_uuid: UUID,
    transaction_data: RequestTransactionModel,
    service: TransactionService = Depends(get_transaction_service),
):
    return await service.create_transaction(user_uuid=user_uuid, transaction_data=transaction_data)


@router.patch("/{user_id}/transactions/{transaction_id}", response_model=typing.Optional[TransactionModel] | None)
async def patch_rollback_transaction(
    user_uuid: UUID,
    transaction_uuid: UUID,
    service: TransactionService = Depends(get_transaction_service),
):
    return await service.update_transaction(user_uuid=user_uuid, transaction_uuid=transaction_uuid)
