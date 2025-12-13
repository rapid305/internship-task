from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.models import BaseModelMixin


class User(BaseModelMixin):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String, nullable=True)

    user_balance: Mapped[list["UserBalance"]] = relationship(
        "UserBalance",
        back_populates="owner"
    )


class UserBalance(BaseModelMixin):
    __tablename__ = "user_balance"

    user_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.uuid", ondelete="CASCADE"),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(
        nullable=True,
        default=0
    )

    table_args = (
        UniqueConstraint("user_uuid", "currency", name="user_balance_user_currency_unique"),
    )

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="user_balance"
    )


class Transaction(BaseModelMixin):
    __tablename__ = "transaction"

    user_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.uuid", ondelete="CASCADE"),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(
        nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=True)