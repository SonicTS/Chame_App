from typing import List
from models.ingredient import Ingredient
from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # 'raw ingredient' or 'toast'
    price_per_unit = Column(Float)
    cost_per_unit = Column(Float)  # Cost price per unit	
    profit_per_unit = Column(Float)  # Profit per unit
    stock_quantity = Column(Integer, default=0)
    toaster_space = Column(Integer, default=0)  # For toast products
    sales = relationship("Sale", back_populates="product")

    product_toast_rounds = relationship("ProductToastround", back_populates="product")
    product_ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")

    def update_stock(self):
        """
        Update the stock of the product based on the stock of its ingredients and the quantity required.
        """
        self.stock_quantity = float('inf')  # Assume infinite until limited by ingredients

        for assoc in self.product_ingredients:
            ingredient = assoc.ingredient
            quantity_needed = assoc.ingredient_quantity

            if not ingredient:
                print(f"Ingredient with ID {assoc.ingredient_id} not found.")
                continue

            if quantity_needed <= 0:
                print(f"Invalid quantity needed for ingredient {ingredient.name}")
                continue

            # Calculate how many products can be made from this ingredient
            ingredient_stock = ingredient.stock_quantity
            max_product_qty = ingredient_stock // quantity_needed

            self.stock_quantity = min(self.stock_quantity, max_product_qty)

        print(f"Stock updated for product: {self.name} -> {self.stock_quantity}")

    def __init__(self, name: str, category: str, price_per_unit: float = 0, cost_per_unit: float = 0, profit_per_unit: float = 0, stock_quantity: int = 0, toaster_space: int = 0):
        self.name = name
        self.category = category
        self.price_per_unit = price_per_unit
        self.cost_per_unit = cost_per_unit
        self.profit_per_unit = profit_per_unit
        self.stock_quantity = stock_quantity
        self.toaster_space = toaster_space

    def __repr__(self):
        return f"<Product(name={self.name}, category={self.category}, price={self.price_per_unit}, stock={self.stock_quantity}, ingredients={self.ingredients})>"

    def to_dict(self, include_ingredients=False, include_sales=False, include_toast_rounds=False, include_product_ingredients=False, include_product_toast_rounds=False):
        data = {
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "price_per_unit": self.price_per_unit,
            "cost_per_unit": self.cost_per_unit,
            "profit_per_unit": self.profit_per_unit,
            "stock_quantity": self.stock_quantity,
            "toaster_space": self.toaster_space,
        }
        if include_ingredients:
            data["ingredients"] = [pi.ingredient.to_dict() for pi in self.product_ingredients]
        if include_product_ingredients:
            data["product_ingredients"] = [pi.to_dict() for pi in self.product_ingredients]
        if include_sales:
            data["sales"] = [sale.to_dict() for sale in self.sales]
        if include_toast_rounds:
            data["toast_rounds"] = [ptr.toast_round.to_dict() for ptr in self.product_toast_rounds]
        if include_product_toast_rounds:
            data["product_toast_rounds"] = [ptr.to_dict() for ptr in self.product_toast_rounds]
        return data

