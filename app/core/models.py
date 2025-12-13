from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from uuid import UUID, uuid4
from sqlalchemy import DateTime
from app.db.db_config import Base


class BaseModelMixin(Base):
    __abstract__ = True

    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )