from typing import Any, Optional
from uuid import UUID

from app.db.dao.base_dao import BaseDAO, ModelT
from app.db.models import Transaction
from app.schemas.transaction_schemas import CreateTransactionModel


class TransactionsDAO(BaseDAO[Transaction]):
    model = Transaction

    async def get(self, user_uuid: UUID) -> list[Transaction]:
        return await super().get(user_uuid=user_uuid)

    async def create(
        self,
        transaction: CreateTransactionModel,
        should_commit: bool = True,
    ) -> Transaction:
        return await super().create(transaction, should_commit=should_commit)

    async def update_by_uuid(self, obj_uuid: Any, should_commit: bool = True, **payload: Any) -> Transaction:
        return await super().update_by_uuid(obj_uuid, should_commit=should_commit, **payload)

    async def get_by_uuid(self, _uuid: Any, raise_not_found: bool = False) -> Optional[ModelT]:
        return await super().get_by_uuid(_uuid, raise_not_found=raise_not_found)
