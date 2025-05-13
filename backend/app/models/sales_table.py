from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.orm import relationship
from chame_app.database import Base

class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, default=1)
    total_price = Column(Float)
    timestamp = Column(String)  # This can be a datetime field, but we'll keep it simple for now
    toast_round_id = Column(Integer, ForeignKey("toast_round.toast_round_id"), nullable=True)  # Make optional

    # Relationships
    user = relationship("User", back_populates="sales")
    product = relationship("Product", back_populates="sales")
    toast_round = relationship("ToastRound", back_populates="sales")

    def __init__(self, user_id: int, product_id: int, quantity: int, total_price: float, timestamp: str, toast_round_id: int = None):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.total_price = total_price
        self.timestamp = timestamp
        self.toast_round_id = toast_round_id

    def __repr__(self):
        return f"<Sale(user={self.user.name}, product={self.product.name}, quantity={self.quantity}, total_price={self.total_price}, toast_round={self.toast_round.id if self.toast_round else 'None'})>"
