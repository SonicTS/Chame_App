from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base

class ProductToastround(Base):
    __tablename__ = "product_toast_round"
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True)
    toast_round_id = Column(Integer, ForeignKey("toast_round.toast_round_id", ondelete="CASCADE"), primary_key=True)

    product = relationship("Product", back_populates="product_toast_rounds")
    toast_round = relationship("ToastRound", back_populates="toast_round_products")
