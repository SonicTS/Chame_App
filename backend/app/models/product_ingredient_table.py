from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base

class ProductIngredient(Base):
    __tablename__ = "product_ingredient"
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.ingredient_id", ondelete="CASCADE"), primary_key=True)
    ingredient_quantity = Column(Integer, default=0)

    product = relationship("Product", back_populates="product_ingredients")
    ingredient = relationship("Ingredient", back_populates="ingredient_products")
