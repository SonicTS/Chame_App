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
    user = relationship("User", backref="transactions")
    def __init__(self, user_id: int, amount: float, type: str, timestamp: str):
        self.user_id = user_id
        self.amount = amount
        self.type = type
        self.timestamp = timestamp
        
    def __repr__(self):
        return f"<Transaction(user_id={self.user_id}, amount={self.amount}, type={self.type})>"
    
    def to_dict(self, include_user=False):
        data = {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "type": self.type,
            "timestamp": self.timestamp,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        return data
