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

    def to_dict(self, include_ingredient=False):
        data = {
            # No single product_ingredient_id; use composite or omit
            "product_id": self.product_id,
            "ingredient_id": self.ingredient_id,
            "ingredient_quantity": self.ingredient_quantity,
        }
        # if include_ingredient and hasattr(self, 'ingredient'):
        #     data["ingredient"] = self.ingredient.to_dict()
        return data
