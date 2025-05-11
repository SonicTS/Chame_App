
from models.product_ingredient_table import ProductIngredient
from sqlalchemy import inspect
from models.bank_table import Bank
from models.user_table import User
from models.ingredient import Ingredient
from models.product_table import Product
from models.sales_table import Sale
from services.admin_webpage import app
from chame_app.database_instance import Database

from chame_app.database import engine, Base, SessionLocal



def main():

    db = SessionLocal()

    # Check if an admin user already exists

    # Check if 'bread' and 'cheese' exist as ingredients, add if not
    bread = db.query(Ingredient).filter_by(name="bread").first()
    if not bread:
        bread = Ingredient(name="bread", price_per_unit=0.5, stock_quantity=100)
        db.add(bread)
        print("Ingredient 'bread' added.")

    cheese = db.query(Ingredient).filter_by(name="cheese").first()
    if not cheese:
        cheese = Ingredient(name="cheese", price_per_unit=1.2, stock_quantity=50)
        db.add(cheese)
        print("Ingredient 'cheese' added.")

    # Check if 'speed' exists as an ingredient, add if not
    speed_ingredient = db.query(Ingredient).filter_by(name="speed").first()
    if not speed_ingredient:
        speed_ingredient = Ingredient(name="speed", price_per_unit=0.2, stock_quantity=200)
        db.add(speed_ingredient)
        print("Ingredient 'speed' added.")

    # Check if 'speed' exists as a product, add if not
    speed_product = db.query(Product).filter_by(name="speed").first()
    if not speed_product:
        speed_product = Product(name="speed", category="raw ingredient", price_per_unit=0.5)
        db.add(speed_product)
        print("Product 'speed' added.")

    # Check if 'cheese toast' exists as a product, add if not
    cheese_toast = db.query(Product).filter_by(name="cheese toast").first()
    if not cheese_toast:
        cheese_toast = Product(name="cheese toast", category="toast", price_per_unit=5)
        db.add(cheese_toast)

        # Create ProductIngredient associations with quantities
        assoc_bread = ProductIngredient(ingredient=bread, product=cheese_toast, ingredient_quantity=2)
        assoc_cheese = ProductIngredient(ingredient=cheese, product=cheese_toast, ingredient_quantity=1)

        # Add to the relationship
        cheese_toast.product_ingredients.extend([assoc_bread, assoc_cheese])

        print("Product 'cheese toast' added with ingredients 'bread' and 'cheese'.")

    if not db.query(User).filter_by(role="admin").first():
        # Add an admin user
        admin_user = User(name="admin", balance=0, password_hash="12345678", role="admin")
        db.add(admin_user)
        db.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
    
    db.commit()
    # Close the session
    db.close()

    

    app.run()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()