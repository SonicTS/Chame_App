
from sqlalchemy import Column, Integer, ForeignKey, Float, Table, String
from sqlalchemy.orm import relationship
from chame_app.database import Base
from .ingredient import Ingredient
from .product_table import Product

class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, default=1)
    total_price = Column(Float)
    timestamp = Column(String)  # This can be a datetime field, but we'll keep it simple for now

    # Relationships
    user = relationship("User", back_populates="sales")
    product = relationship("Product", back_populates="sales")

    def __repr__(self):
        return f"<Sale(user={self.user.name}, product={self.product.name}, quantity={self.quantity}, total_price={self.total_price})>"

product_ingredient = Table(
    "product_ingredient", Base.metadata,
    Column("product_id", Integer, ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("ingredients.ingredient_id", ondelete="CASCADE"), primary_key=True)
)
