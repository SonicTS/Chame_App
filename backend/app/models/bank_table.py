from sqlalchemy import Column, ForeignKey, Integer, Float, String, DateTime
from chame_app.database import Base
import datetime
from sqlalchemy.orm import relationship

class Bank(Base):
    __tablename__ = "bank"

    # Enforce a single row by using a constant user_id
    account_id = Column(Integer, primary_key=True, default=1)  # Single row enforced with default 1
    total_balance = Column(Float, default=0.0)
    customer_funds = Column(Float, default=0.0)
    revenue_funds = Column(Float, default=0.0)
    costs_reserved = Column(Float, default=0.0)
    profit_retained = Column(Float, default=0.0)

    revenue_total = Column(Float, default=0.0)
    costs_total = Column(Float, default=0.0)
    profit_total = Column(Float, default=0.0)
    
    product_value = Column(Float, default=0.0)
    ingredient_value = Column(Float, default=0.0)
 
    def __repr__(self):
        return f"<Bank(account_id={self.account_id}, total_balance={self.total_balance}, " \
               f"customer_funds={self.customer_funds}, revenue_funds={self.revenue_funds}, " \
               f"costs_reserved={self.costs_reserved}, profit_retained={self.profit_retained}, " \
               f"revenue_total={self.revenue_total}, costs_total={self.costs_total}, " \
               f"profit_total={self.profit_total}, ingredient_value={self.ingredient_value}, " \
               f"product_value={self.product_value})>"

    def to_dict(self):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        return {
            "account_id": self.account_id,
            "total_balance": _round(self.total_balance),
            "customer_funds": _round(self.customer_funds),
            "revenue_funds": _round(self.revenue_funds),
            "costs_reserved": _round(self.costs_reserved),
            "profit_retained": _round(self.profit_retained),
            "revenue_total": _round(self.revenue_total),
            "costs_total": _round(self.costs_total),
            "profit_total": _round(self.profit_total),
            "product_value": _round(self.product_value),
            "ingredient_value": _round(self.ingredient_value),
        }

class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # e.g., 'withdrawal'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String, nullable=True)  # Optional description field
    salesman_id = Column(Integer, ForeignKey("users.user_id"))  # Required sales person
    
    salesman = relationship('User', foreign_keys=[salesman_id])

    def __repr__(self):
        return f"<BankTransaction(id={self.transaction_id}, amount={self.amount}, type={self.type}, timestamp={self.timestamp}, description={self.description}, salesman_id={self.salesman_id})>"

    def to_dict(self, include_salesman=True):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        data = {
            "transaction_id": self.transaction_id,
            "amount": _round(self.amount),
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "description": self.description,
            "salesman_id": self.salesman_id,
        }
        if include_salesman:
            data["salesman"] = self.salesman.to_dict(include_sales=False) if self.salesman else None
        return data

