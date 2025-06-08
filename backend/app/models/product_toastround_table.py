from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base

class ProductToastround(Base):
    __tablename__ = "product_toast_round"
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True)
    toast_round_id = Column(Integer, ForeignKey("toast_round.toast_round_id", ondelete="CASCADE"), primary_key=True)

    product = relationship("Product", back_populates="product_toast_rounds")
    toast_round = relationship("ToastRound", back_populates="toast_round_products")

    def to_dict(self, include_product=False, include_toast_round=False):
        data = {
            "product_id": self.product_id,
            "toast_round_id": self.toast_round_id,
        }
        if include_product and self.product:
            data["product"] = self.product.to_dict()
        if include_toast_round and self.toast_round:
            data["toast_round"] = self.toast_round.to_dict()
        return data
