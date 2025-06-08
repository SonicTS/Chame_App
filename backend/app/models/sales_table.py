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

    def to_dict(self, include_user=False, include_product=False, include_toast_round=False):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        data = {
            "sale_id": self.sale_id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": _round(self.total_price),
            "timestamp": self.timestamp,
            "toast_round_id": self.toast_round_id,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        if include_product and self.product:
            data["product"] = self.product.to_dict()
        if include_toast_round and self.toast_round:
            data["toast_round"] = self.toast_round.to_dict()
        return data
