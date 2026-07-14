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

    def get_business_balance(self) -> float:
        return float(self.total_balance or 0.0) - float(self.customer_funds or 0.0)

    def get_profit_total(self) -> float:
        return float(self.revenue_total or 0.0) - float(self.costs_total or 0.0)

    def get_break_even_remaining(self) -> float:
        return max(float(self.costs_total or 0.0) - float(self.revenue_total or 0.0), 0.0)

    def get_break_even_surplus(self) -> float:
        return max(self.get_profit_total(), 0.0)

    def get_break_even_covered_costs(self) -> float:
        return max(min(float(self.revenue_total or 0.0), float(self.costs_total or 0.0)), 0.0)

    def get_break_even_progress(self) -> float:
        costs_total = float(self.costs_total or 0.0)
        revenue_total = float(self.revenue_total or 0.0)
        if costs_total <= 0:
            return 1.0
        return max(min(revenue_total / costs_total, 1.0), 0.0)

    def is_break_even_reached(self) -> bool:
        return float(self.revenue_total or 0.0) >= float(self.costs_total or 0.0)
 
    def __repr__(self):
        return f"<Bank(account_id={self.account_id}, total_balance={self.total_balance}, " \
               f"customer_funds={self.customer_funds}, revenue_funds={self.revenue_funds}, " \
               f"costs_reserved={self.costs_reserved}, profit_retained={self.profit_retained}, " \
               f"revenue_total={self.revenue_total}, costs_total={self.costs_total}, " \
               f"profit_total={self.profit_total}, ingredient_value={self.ingredient_value}, " \
               f"product_value={self.product_value})>"

    def to_dict(self):
        business_balance = self.get_business_balance()
        break_even_remaining = self.get_break_even_remaining()
        break_even_surplus = self.get_break_even_surplus()
        break_even_covered_costs = self.get_break_even_covered_costs()
        break_even_progress = self.get_break_even_progress()
        profit_total = self.get_profit_total()
        return {
            "account_id": self.account_id,
            "total_balance": self.total_balance,
            "customer_funds": self.customer_funds,
            "revenue_funds": business_balance,
            "costs_reserved": break_even_remaining,
            "profit_retained": break_even_surplus,
            "revenue_total": self.revenue_total,
            "costs_total": self.costs_total,
            "profit_total": profit_total,
            "product_value": self.product_value,
            "ingredient_value": self.ingredient_value,
            "business_balance": business_balance,
            "break_even_remaining": break_even_remaining,
            "break_even_surplus": break_even_surplus,
            "break_even_covered_costs": break_even_covered_costs,
            "break_even_progress": break_even_progress,
            "break_even_reached": self.is_break_even_reached(),
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
        data = {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "description": self.description,
            "salesman_id": self.salesman_id,
        }
        if include_salesman:
            data["salesman"] = self.salesman.to_dict(include_sales=False) if self.salesman else None
        return data

