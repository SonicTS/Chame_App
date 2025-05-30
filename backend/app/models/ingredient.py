from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer
from chame_app.database import Base, engine, SessionLocal

class Ingredient(Base):
    __tablename__ = "ingredients"

    ingredient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price_per_package = Column(Float)  # Purchasing price per package
    number_of_units = Column(Integer)  # Number of units in a package
    price_per_unit = Column(Float)  # Purchasing price per unit
    stock_quantity = Column(Integer, default=0)

    # Relationship back to Product (via the ProductIngredient table)
    ingredient_products = relationship("ProductIngredient", back_populates="ingredient")
    def __init__(self, name, price_per_package=None, number_of_units=None, price_per_unit=None, stock_quantity=0):
        self.name = name
        self.price_per_package = price_per_package
        self.number_of_units = number_of_units
        self.price_per_unit = price_per_unit
        self.stock_quantity = stock_quantity
        
    def __repr__(self):
        return f"<Ingredient(name={self.name}, price={self.price_per_unit}, stock={self.stock_quantity})>"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create some ingredients
    bread = Ingredient(name="Bread", price_per_unit=0.5, stock_quantity=100)
    cheese = Ingredient(name="Cheese", price_per_unit=1.2, stock_quantity=50)
    speed = Ingredient(name="Speed", price_per_unit=0.2, stock_quantity=200)

    # Add ingredients to the session
    db.add(bread)
    db.add(cheese)
    db.add(speed)


    # Commit to the database
    db.commit()

    # Close the session
    db.close()

if __name__ == "__main__":
    main()