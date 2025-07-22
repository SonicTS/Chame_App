from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    amount = Column(Float)
    type = Column(String)  # 'deposit', 'withdraw'
    timestamp = Column(String)  # For simplicity, this can be a string (you can use datetime for a more complex setup)
    comment = Column(String, nullable=True)  # Optional comment for the transaction
    salesman_id = Column(Integer, ForeignKey("users.user_id"))  # Optional sales person

    user = relationship("User", foreign_keys=[user_id], backref="transactions")
    salesman = relationship('User', foreign_keys=[salesman_id])

    def __init__(self, user_id: int, amount: float, type: str, timestamp: str, salesman_id: int, comment: str = None, ):
        self.user_id = user_id
        self.amount = amount
        self.type = type
        self.comment = comment
        self.timestamp = timestamp
        self.salesman_id = salesman_id
        
    def __repr__(self):
        return f"<Transaction(user_id={self.user_id}, amount={self.amount}, type={self.type}, timestamp={self.timestamp}, comment={self.comment}, salesman_id={self.salesman_id})>"
    
    def to_dict(self):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        data = {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": _round(self.amount),
            "type": self.type,
            "timestamp": self.timestamp,
            "comment": self.comment,
            "salesman_id": self.salesman_id
        }
        data["user"] = self.user.to_dict()
        data["salesman"] = self.salesman.to_dict()
        return data
