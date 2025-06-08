from sqlalchemy import Column, Integer, Float, String, DateTime
from chame_app.database import Base
import datetime

class Bank(Base):
    __tablename__ = "bank"

    # Enforce a single row by using a constant user_id
    account_id = Column(Integer, primary_key=True, default=1)  # Single row enforced with default 1
    total_balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)
    restocking_cost = Column(Float, default=0.0)
    profit_balance = Column(Float, default=0.0)
    ingredient_value = Column(Float, default=0.0)

    def __repr__(self):
        return f"<Bank(user_id={self.user_id}, total_balance={self.total_balance}, " \
               f"available_balance={self.available_balance}, ingredient_value={self.ingredient_value}, " \
               f"product_value={self.product_value})>"

    def to_dict(self):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        return {
            "account_id": self.account_id,
            "total_balance": _round(self.total_balance),
            "available_balance": _round(self.available_balance),
            "restocking_cost": _round(self.restocking_cost),
            "profit_balance": _round(self.profit_balance),
            "ingredient_value": _round(self.ingredient_value),
        }

class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # e.g., 'withdrawal'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String, nullable=True)  # Optional description field

    def __repr__(self):
        return f"<BankTransaction(id={self.transaction_id}, amount={self.amount}, type={self.type}, timestamp={self.timestamp}, description={self.description})>"

    def to_dict(self):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        return {
            "transaction_id": self.transaction_id,
            "amount": _round(self.amount),
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "description": self.description,
        }
