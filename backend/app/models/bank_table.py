from sqlalchemy import Column, Integer, Float
from chame_app.database import Base

class Bank(Base):
    __tablename__ = "bank"

    # Enforce a single row by using a constant user_id
    account_id = Column(Integer, primary_key=True, default=1)  # Single row enforced with default 1
    total_balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)
    ingredient_value = Column(Float, default=0.0)
    product_value = Column(Float, default=0.0)

    def __repr__(self):
        return f"<Bank(user_id={self.user_id}, total_balance={self.total_balance}, " \
               f"available_balance={self.available_balance}, ingredient_value={self.ingredient_value}, " \
               f"product_value={self.product_value})>"
