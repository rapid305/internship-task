from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import BaseModelMixin
from app.transactions.db.db_config import Base


class Transaction(BaseModelMixin, Base):
    __tablename__ = "transaction"

    user_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)
