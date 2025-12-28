from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import BaseModelMixin
from app.db.db_config import Base


class User(BaseModelMixin, Base):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String, nullable=True)

    user_balance: Mapped[list["UserBalance"]] = relationship("UserBalance", back_populates="owner")
    user_transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="transaction_owner")


class UserBalance(BaseModelMixin, Base):
    __tablename__ = "user_balance"

    user_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.uuid", ondelete="CASCADE"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String, nullable=True)
    amount: Mapped[Decimal] = mapped_column(nullable=True, default=0)

    table_args = (UniqueConstraint("user_uuid", "currency", name="user_balance_user_currency_unique"),)

    owner: Mapped["User"] = relationship("User", back_populates="user_balance")


class Transaction(BaseModelMixin, Base):
    __tablename__ = "transaction"

    user_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.uuid", ondelete="CASCADE"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)
    transaction_owner: Mapped["User"] = relationship("User", back_populates="user_transactions")
