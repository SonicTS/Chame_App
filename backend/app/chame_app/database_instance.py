
import datetime
from typing import List
from chame_app.database import engine, SessionLocal
from models.ingredient import Ingredient
from models.product_ingredient_table import ProductIngredient
from models.product_table import Product
from models.sales_table import Sale
from models.user_table import User
from models.transaction_table import Transaction
from models.bank_table import Bank
from chame_app.database import Base

Base.metadata.create_all(bind=engine)


class Database:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        session = self.SessionLocal()
        bank = session.query(Bank).filter_by(account_id=1).first()
        if not bank:
            bank = Bank(total_balance=0.0, available_balance=0.0, ingredient_value=0.0, product_value=0.0)
            session.add(bank)
            session.commit()
            session.refresh(bank)
        session.close()

    def get_session(self):
        """Create a new session."""
        return self.SessionLocal()
    
    def change_password(self, user_id: int, new_password: str):
        """Change the password of a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            user.password_hash = new_password
            session.commit()
            session.refresh(user)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_ingredient(self, name: str, price_per_unit: float, stock_quantity: int):
        """Add an ingredient to the database."""
        ingredient = Ingredient(name=name, price_per_unit=price_per_unit, stock_quantity=stock_quantity)
        if stock_quantity > 0:
            bank = self.get_session().query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError("Bank account not found")
            bank.ingredient_value += price_per_unit * stock_quantity
        session = self.get_session()
        try:
            session.add(ingredient)
            session.commit()
            session.refresh(ingredient)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def stock_ingredient(self, ingredient_id: int, quantity: int):
        """Stock an ingredient in the database."""
        session = self.get_session()
        try:
            ingredient = session.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
            if not ingredient:
                raise ValueError("Ingredient not found")
            ingredient.stock_quantity += quantity
            bank = session.query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError("Bank account not found")
            bank.ingredient_value += ingredient.price_per_unit * quantity
            for product in ingredient.products:
                current_stock = product.stock_quantity
                product.update_stock()  # Update the stock of products that use this ingredient
                new_stock = product.stock_quantity
                if new_stock < current_stock:
                    raise RuntimeError(f"This should never happen: {product.name} stock decreased from {current_stock} to {new_stock}")
                if new_stock > current_stock:
                    bank.product_value += (new_stock - current_stock) * product.price_per_unit
            session.commit()
            session.refresh(ingredient)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_product(self, name: str, ingredients: List[tuple[Ingredient, int]], price_per_unit: float = 0.0, category: str = "raw"):
        """Add a product made from a list of ingredients."""
        if len(ingredients) == 0:
            raise ValueError("Product must have at least one ingredient")
        elif len(ingredients) > 1 and category == "raw":
            raise ValueError("Raw products can only have one ingredient")
        
        session = self.get_session()
        try:
            try:
                price = int(price_per_unit)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid price for product {name}: {price_per_unit}")
            
            product = Product(name=name, price_per_unit=price, category=category)
            session.add(product)
            session.flush()  # Ensure product ID is generated

            for ingredient_obj, quantity in ingredients:
                # Check if the ingredient exists in the database
                try:
                    ingredient_quantity = int(quantity)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid quantity for ingredient {ingredient_obj}: {quantity}")

                existing_ingredient = session.query(Ingredient).filter_by(ingredient_id=ingredient_obj.ingredient_id).first()
                if not existing_ingredient:
                    raise ValueError(f"Ingredient {ingredient_obj.name} not found in the database")

                # Create association object
                association = ProductIngredient(
                    product=product,
                    ingredient=existing_ingredient,
                    ingredient_quantity=ingredient_quantity
                )

                # Add the association to the product
                product.product_ingredients.append(association)
            product.update_stock()  # Update the stock of ingredients based on the product
            bank = session.query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError("Bank account not found")
            bank.product_value += product.price_per_unit * product.stock_quantity

            session.commit()
            session.refresh(product)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_user(self, username: str, password: str, role: str = "user", balance: float = 0.0):
        """Add a user to the database."""
        if username == "bank":
            raise ValueError("Username 'bank' is reserved and cannot be used")
        session = self.get_session()
        try:
            user = User(username=username, balance=balance, password_hash=password, role=role)
            bank = session.query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError("Bank account not found")
            bank.total_balance += balance
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def make_purchase(self, user_id: int, product_id: int, quantity: int):
        """Make a purchase."""
        session = self.get_session()
        bank = session.query(Bank).filter_by(account_id=1).first()
        if not bank:
            raise ValueError("Bank account not found")
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError("Product not found")
            if product.stock_quantity < quantity:
                raise ValueError("Insufficient stock for this product")
            for assoc in product.product_ingredients:
                ingredient = assoc.ingredient
                required_qty = assoc.ingredient_quantity * quantity

                if ingredient.stock_quantity < required_qty:
                    raise ValueError(f"Insufficient stock for ingredient {ingredient.name}")

                # Deduct the used quantity from ingredient stock
                ingredient.stock_quantity -= required_qty

                # Adjust bank value
                bank.ingredient_value -= required_qty * ingredient.price_per_unit

            product.update_stock()  # Update the stock of ingredients based on the product
            total_cost = product.price * quantity
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            if user.balance < total_cost:
                raise ValueError("Insufficient balance")

            purchase = Sale(user_id=user_id, product_id=product_id, quantity=quantity, 
                            total_price=total_cost, timestamp=datetime.now())
            user.balance -= total_cost
            bank.available_balance += total_cost
            bank.product_value -= total_cost
            session.add(purchase)
            session.commit()
            session.refresh(purchase)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def deposit_cash(self, user_id: int, amount: float):
        """Deposit cash into a user's account."""
        session = self.get_session()
        bank = session.query(Bank).filter_by(account_id=1).first()
        if not bank:
            raise ValueError("Bank account not found")
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            user.balance += amount
            bank.total_balance += amount
            transaction = Transaction(user_id=user_id, amount=amount, transaction_type="deposit", timestamp=datetime.now())
            session.add(transaction)
            session.commit()
            session.refresh(user)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def withdraw_cash(self, user_id: int, amount: float):
        """Withdraw cash from a user's account."""
        session = self.get_session()
        bank = session.query(Bank).filter_by(account_id=1).first()
        if not bank:
            raise ValueError("Bank account not found")
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            if user.balance < amount:
                raise ValueError("Insufficient balance")
            user.balance -= amount
            bank.total_balance -= amount
            session.commit()
            session.refresh(user)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_balance(self, user_id: int) -> float:
        """Get the balance of a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            return user.balance
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_bank(self) -> Bank:
        """Get the bank account."""
        session = self.get_session()
        try:
            bank = session.query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError("Bank account not found")
            return bank
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_all_users(self) -> List[User]:
        """Get all users."""
        session = self.get_session()
        try:
            users = session.query(User).all()
            return users
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_all_products(self) -> List[Product]:
        """Get all products."""
        session = self.get_session()
        try:
            products = session.query(Product).all()
            return products
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_all_ingredients(self) -> List[Ingredient]:
        """Get all ingredients."""
        session = self.get_session()
        try:
            ingredients = session.query(Ingredient).all()
            return ingredients
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_ingredient_by_id(self, ingredient_id: int) -> Ingredient:
        """Get an ingredient by its ID."""
        session = self.get_session()
        try:
            ingredient = session.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
            if not ingredient:
                raise ValueError("Ingredient not found")
            return ingredient
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_ingredients_by_ids(self, ingredient_ids: List[int]) -> List[Ingredient]:
        """Get ingredients by their IDs."""
        session = self.get_session()
        try:
            ingredients = session.query(Ingredient).filter(Ingredient.ingredient_id.in_(ingredient_ids)).all()
            if not ingredients:
                raise ValueError("No ingredients found")
            return ingredients
        except Exception as e:
            raise e
        finally:
            session.close()


database = Database()