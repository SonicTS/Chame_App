import datetime
from typing import List
from chame_app.database import engine, SessionLocal
from models.ingredient import Ingredient
from models.product_ingredient_table import ProductIngredient
from models.product_table import Product
from models.sales_table import Sale
from models.toast_round import ToastRound
from models.user_table import User
from models.transaction_table import Transaction
from models.bank_table import Bank
from chame_app.database import Base
from sqlalchemy.orm import joinedload

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
    
    def change_password(self, user_id: int, new_password: str, session = None):
        """Change the password of a user."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            user.password_hash = new_password
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
    
    def add_ingredient(self, name: str, price_per_unit: float, stock_quantity: int, session = None):
        """Add an ingredient to the database."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            stock = int(stock_quantity)
            price = float(price_per_unit)
        except:
            raise ValueError("Stock not a integer or price not valid")
        
        ingredient = Ingredient(name=name, price_per_unit=price, stock_quantity=stock)
        if stock > 0:
            bank = self.get_bank(session)
            if not bank:
                raise ValueError("Bank account not found")
            bank.ingredient_value += price * stock
        try:
            session.add(ingredient)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(ingredient)
                session.close()

    def stock_ingredient(self, ingredient_id: int, quantity: int, session = None):
        """Stock an ingredient in the database."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredient = self.get_ingredient_by_id(ingredient_id, session)
            if not ingredient:
                raise ValueError("Ingredient not found")
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid quantity for ingredient {ingredient_id}: {quantity}")
            ingredient.stock_quantity += quantity
            bank = self.get_bank(session)
            if not bank:
                raise ValueError("Bank account not found")
            bank.ingredient_value += ingredient.price_per_unit * quantity
            for product_assoc in ingredient.ingredient_products:
                product = product_assoc.product
                current_stock = product.stock_quantity
                product.update_stock()  # Update the stock of products that use this ingredient
                new_stock = product.stock_quantity
                if new_stock < current_stock:
                    raise RuntimeError(f"This should never happen: {product.name} stock decreased from {current_stock} to {new_stock}")
                if new_stock > current_stock:
                    bank.product_value += (new_stock - current_stock) * product.price_per_unit
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(ingredient)
                session.close()

    def add_product(self, name: str, ingredients: List[tuple[Ingredient, int]], price_per_unit: float = 0.0, 
                    category: str = "raw", toast_round_quantity = None, session = None):
        """Add a product made from a list of ingredients."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        if len(ingredients) == 0:
            raise ValueError("Product must have at least one ingredient")
        elif len(ingredients) > 1 and category == "raw":
            raise ValueError("Raw products can only have one ingredient")
        try:
            try:
                price = float(price_per_unit)
                if toast_round_quantity is not None and not toast_round_quantity == '':
                    toast_round_quantity = int(toast_round_quantity)
                else:
                    toast_round_quantity = 0
            except (ValueError, TypeError):
                raise ValueError(f"Invalid price for product {name}: {price_per_unit}")
            
            product = Product(name=name, price_per_unit=price, category=category, toast_round_quantity=toast_round_quantity)
            session.add(product)
            session.flush()  # Ensure product ID is generated

            for ingredient_obj, quantity in ingredients:
                # Check if the ingredient exists in the database
                try:
                    ingredient_quantity = int(quantity)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid quantity for ingredient {ingredient_obj}: {quantity}")

                existing_ingredient = self.get_ingredient_by_id(ingredient_obj.ingredient_id, session)
                if not existing_ingredient:
                    raise ValueError(f"Ingredient {ingredient_obj.name} not found in the database")

                # Create association object
                association = ProductIngredient(
                    product=product,
                    ingredient=existing_ingredient,
                    ingredient_quantity=ingredient_quantity
                )
                session.add(association)
            product.update_stock()  # Update the stock of ingredients based on the product
            bank = self.get_bank(session)
            if not bank:
                raise ValueError("Bank account not found")
            bank.product_value += product.price_per_unit * product.stock_quantity


        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(product)
                session.close()

    def add_user(self, username: str, password: str, role: str = "user", balance: float = 0.0, session = None):
        """Add a user to the database."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        if username == "bank":
            raise ValueError("Username 'bank' is reserved and cannot be used")
        try:
            balance = float(balance)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid balance for user {username}: {balance}")
        try:
            user = User(name=username, balance=balance, password_hash=password, role=role)
            bank = self.get_bank(session)
            if not bank:
                raise ValueError("Bank account not found")
            bank.total_balance += balance
            session.add(user)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()

    def make_purchase(self, user_id: int, product_id: int, quantity: int, session = None, toast_round_id: int = 0) -> Sale:
        """Make a purchase."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        bank = self.get_bank(session)
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid quantity for product {product_id}: {quantity}")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if not bank:
            raise ValueError("Bank account not found")
        try:
            product = self.get_product_by_id(product_id, session)
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
                for product_assoc in ingredient.ingredient_products:
                    product_assoc.product.update_stock()


            product.update_stock()  # Update the stock of ingredients based on the product
            total_cost = product.price_per_unit * quantity
            user = database.get_user_by_id(user_id, session=session)
            if not user:
                raise ValueError("User not found")
            if user.balance < total_cost:
                raise ValueError("Insufficient balance")

            purchase = Sale(user_id=user_id, product_id=product_id, quantity=quantity, total_price=total_cost,  # Assuming total_price is the cost of the product 
                            timestamp=datetime.datetime.now(), toast_round_id=toast_round_id)
            user.balance -= total_cost
            bank.available_balance += total_cost
            bank.product_value -= total_cost
            session.add(purchase)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(purchase)
                session.close()
        return purchase

    def deposit_cash(self, user_id: int, amount: float, session = None):
        """Deposit cash into a user's account."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        bank = self.get_bank(session)
        if not bank:
            raise ValueError("Bank account not found")
        try:
            user = self.get_user_by_id(user_id, session)
            if not user:
                raise ValueError("User not found")
            user.balance += amount
            bank.total_balance += amount
            transaction = Transaction(user_id=user_id, amount=amount, transaction_type="deposit", timestamp=datetime.now())
            session.add(transaction)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()

    def withdraw_cash(self, user_id: int, amount: float, session = None):
        """Withdraw cash from a user's account."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        bank = self.get_bank(session)
        if not bank:
            raise ValueError("Bank account not found")
        try:
            user = self.get_user_by_id(user_id, session)
            if not user:
                raise ValueError("User not found")
            if user.balance < amount:
                raise ValueError("Insufficient balance")
            user.balance -= amount
            bank.total_balance -= amount
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()

    def add_toast_round(self, product_id: int, user_selection: List[int], session = None):
        """Add a toast round."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            product = self.get_product_by_id(product_id, session)
            if not product:
                raise ValueError("Product not found")
            if product.category != "toast":
                raise ValueError("Product is not a toast product")
            if product.stock_quantity < len(user_selection):
                raise ValueError("Insufficient stock for this product")
            toast_round = ToastRound(product_id=product.product_id)
            session.add(toast_round)
            for user_id in user_selection:
                user = self.get_user_by_id(user_id, session)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                sale = self.make_purchase(user.user_id, product.product_id, 1, session=session)
                toast_round.sales.append(sale)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if close_session:
                session.commit()
                session.close()

    def get_user_balance(self, user_id: int, session = None) -> float:
        """Get the balance of a user."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = self.get_user_by_id(user_id, session)
            if not user:
                raise ValueError("User not found")
            return user.balance
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_bank(self, session = None) -> Bank:
        """Get the bank account."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            bank = session.query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError("Bank account not found")
            return bank
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_users(self, session=None) -> List[User]:
        """Get all users with eager loading."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            users = session.query(User).options(joinedload('*')).all()
            return users
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_products(self, session=None) -> List[Product]:
        """Get all products with eager loading."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = session.query(Product).options(joinedload('*')).all()
            return products
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_ingredients(self, eager_load=False, session=None) -> List[Ingredient]:
        """Get all ingredients, with optional eager loading."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            query = session.query(Ingredient)
            if eager_load:
                query = query.options(joinedload('*'))
            ingredients = query.all()
            return ingredients
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_ingredient_by_id(self, ingredient_id: int, session = None) -> Ingredient:
        """Get an ingredient by its ID."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredient = session.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
            if not ingredient:
                raise ValueError("Ingredient not found")
            return ingredient
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_ingredients_by_ids(self, ingredient_ids: List[int], session = None) -> List[Ingredient]:
        """Get ingredients by their IDs."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredients = session.query(Ingredient).filter(Ingredient.ingredient_id.in_(ingredient_ids)).all()
            if not ingredients:
                raise ValueError("No ingredients found")
            return ingredients
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_user_by_id(self, user_id: int, session = None) -> User:
        """Get a user by its ID."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError("User not found")
            return user
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_product_by_id(self, product_id: int, session = None) -> Product:
        """Get a product by its ID."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            product = session.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                raise ValueError("Product not found")
            return product
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_products_by_category(self, category: str, session = None) -> List[Product]:
        """Get all products by category."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = session.query(Product).options(
                joinedload('*')
            ).filter(Product.category == category).all()
            return products
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_toast_products(self, session = None) -> List[Product]:
        """Get all toast products."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = self.get_all_products_by_category("toast", session)
            return products
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_toast_rounds(self, session=None) -> List[ToastRound]:
        """Get all toast rounds."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            toast_rounds = session.query(ToastRound).options(
                joinedload('*')
            ).all()
            return toast_rounds
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_all_sales(self, session=None) -> List[Sale]:
        """Get all sales with eager loading."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            sales = session.query(Sale).options(
                joinedload(Sale.user),
                joinedload(Sale.product)
            ).all()
            return sales
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()

    def get_sales_with_category(self, category: str, session = None) -> List[Sale]:
        """Get sales with a specific category."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            sales = session.query(Sale).options(
            joinedload('*')
        ).join(Product).filter(Product.category == category).all()
            return sales
        except Exception as e:
            raise e
        finally:
            if close_session:
                session.close()


database = Database()