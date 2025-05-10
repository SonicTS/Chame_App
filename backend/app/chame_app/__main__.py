
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
        bread = Ingredient(name="bread")
        db.add(bread)
        print("Ingredient 'bread' added.")

    cheese = db.query(Ingredient).filter_by(name="cheese").first()
    if not cheese:
        cheese = Ingredient(name="cheese")
        db.add(cheese)
        print("Ingredient 'cheese' added.")

    # Check if 'speed' exists as an ingredient, add if not
    speed_ingredient = db.query(Ingredient).filter_by(name="speed").first()
    if not speed_ingredient:
        speed_ingredient = Ingredient(name="speed")
        db.add(speed_ingredient)
        print("Ingredient 'speed' added.")

    # Check if 'speed' exists as a product, add if not
    speed_product = db.query(Product).filter_by(name="speed").first()
    if not speed_product:
        speed_product = Product(name="speed")
        db.add(speed_product)
        print("Product 'speed' added.")

    # Check if 'cheese toast' exists as a product, add if not
    cheese_toast = db.query(Product).filter_by(name="cheese toast").first()
    if not cheese_toast:
        cheese_toast = Product(name="cheese toast")
        db.add(cheese_toast)
        cheese_toast.ingredients.extend([bread, cheese])
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