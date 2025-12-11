from app.db.db_config import Base
from sqlalchemy import Column, Integer, String, Numeric, DateTime

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    currency = Column(String, nullable=True)
    amount = Column(Numeric, nullable=True)
    status = Column(String, nullable=True)
    created = Column(DateTime, nullable=True)