from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base, engine, SessionLocal


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # 'raw ingredient' or 'toast'
    price_per_unit = Column(Float)
    stock_quantity = Column(Integer, default=0)

    sales = relationship("Sale", back_populates="product")

    ingredients = relationship("Ingredient", secondary="product_ingredient", back_populates="products")

    def update_stock(self):
        """
        Update the stock of ingredients based on the quantity of the product sold.
        """
        self.stock_quantity = float('inf')  # Start with a large number
        for ingredient in self.ingredients:
           self.stock_quantity = min(self.stock_quantity, ingredient.stock_quantity)
        print(f"Stock updated for product: {self.name}")


    def __repr__(self):
        return f"<Product(name={self.name}, category={self.category}, price={self.price_per_unit}, stock={self.stock_quantity}, ingredients={self.ingredients})>"

