from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.orm import relationship
from chame_app.database import Base

class PfandHistory(Base):
    __tablename__ = "pfand_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    counter = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="pfand_history")
    product = relationship("Product", back_populates="pfand_history")

    def __init__(self, user_id: int, product_id: int, counter: int):
        self.user_id = user_id
        self.product_id = product_id
        self.counter = counter

    def __repr__(self):
        return f"<PfandHistory(user_id={self.user_id}, product_id={self.product_id}, counter={self.counter})>"

    def to_dict(self, include_user=False, include_product=False):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        data = {
            "user_id": self.user_id,
            "product_id": self.product_id,
            "counter": self.counter,
        }
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        if include_product and self.product:
            data["product"] = self.product.to_dict()
        return data
