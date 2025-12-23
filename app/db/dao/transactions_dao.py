from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.db.dao.base_dao import BaseDAO
from app.db.models import Transaction


class TransactionsDAO(BaseDAO[Transaction]):
    model = Transaction

    async def get(self, user_uuid: Optional[UUID] = None, **kwargs) -> List[Transaction]:
        if user_uuid is not None:
            kwargs["user_uuid"] = user_uuid
        return await super().get(**kwargs)

    async def get_all_ordered(self) -> list[Transaction]:
        stmt = select(self.model).order_by(self.model.created.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
