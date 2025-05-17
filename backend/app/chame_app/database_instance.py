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

BANK_NOT_FOUND_MSG = "Bank account not found"
USER_NOT_FOUND_MSG = "User not found"

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
        try:
            return self.SessionLocal()
        except Exception as e:
            raise RuntimeError(f"get_session failed: {e}") from e

    def change_password(self, user_id: int, new_password: str, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"{USER_NOT_FOUND_MSG} (user_id={user_id})")
            user.password_hash = new_password
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"change_password failed for user_id={user_id}: {e}") from e

    def add_ingredient(self, name: str, price_per_unit: float, stock_quantity: int, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            stock = int(stock_quantity)
            price = float(price_per_unit)
            ingredient = Ingredient(name=name, price_per_unit=price, stock_quantity=stock)
            if stock > 0:
                bank = self.get_bank(session)
                bank.ingredient_value += price * stock
            session.add(ingredient)
            if close_session:
                session.commit()
                session.refresh(ingredient)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"add_ingredient failed for name={name}: {e}") from e

    def stock_ingredient(self, ingredient_id: int, quantity: int, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            ingredient = self.get_ingredient_by_id(ingredient_id, session)
            quantity = int(quantity)
            ingredient.stock_quantity += quantity
            bank = self.get_bank(session)
            bank.ingredient_value += ingredient.price_per_unit * quantity
            for product_assoc in ingredient.ingredient_products:
                product = product_assoc.product
                current_stock = product.stock_quantity
                product.update_stock()
                new_stock = product.stock_quantity
                if new_stock < current_stock:
                    raise RuntimeError(f"This should never happen: {product.name} stock decreased from {current_stock} to {new_stock}")
                if new_stock > current_stock:
                    bank.product_value += (new_stock - current_stock) * product.price_per_unit
            if close_session:
                session.commit()
                session.refresh(ingredient)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"stock_ingredient failed for ingredient_id={ingredient_id}, quantity={quantity}: {e}") from e

    def add_product(self, name: str, ingredients: List[tuple[Ingredient, int]], price_per_unit: float = 0.0, category: str = "raw", toast_round_quantity=None, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if len(ingredients) == 0:
                raise ValueError(f"add_product: Product must have at least one ingredient (name={name})")
            if len(ingredients) > 1 and category == "raw":
                raise ValueError(f"add_product: Raw products can only have one ingredient (name={name})")
            price = float(price_per_unit)
            toast_round_quantity = int(toast_round_quantity) if toast_round_quantity not in (None, "") else 0
            product = Product(name=name, price_per_unit=price, category=category, toast_round_quantity=toast_round_quantity)
            session.add(product)
            session.flush()
            for ingredient_obj, quantity in ingredients:
                ingredient_quantity = int(quantity)
                existing_ingredient = self.get_ingredient_by_id(ingredient_obj.ingredient_id, session)
                association = ProductIngredient(product=product, ingredient=existing_ingredient, ingredient_quantity=ingredient_quantity)
                session.add(association)
            product.update_stock()
            bank = self.get_bank(session)
            bank.product_value += product.price_per_unit * product.stock_quantity
            if close_session:
                session.commit()
                session.refresh(product)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"add_product failed for name={name}: {e}") from e

    def add_user(self, username: str, password: str, role: str = "user", balance: float = 0.0, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if username == "bank":
                raise ValueError("add_user: Username 'bank' is reserved and cannot be used")
            balance = float(balance)
            user = User(name=username, balance=balance, password_hash=password, role=role)
            bank = self.get_bank(session)
            bank.total_balance += balance
            session.add(user)
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"add_user failed for username={username}: {e}") from e

    def _check_product_stock(self, product, quantity):
        if product.stock_quantity < quantity:
            raise ValueError(f"make_purchase: Insufficient stock for this product (product_id={product.product_id}, quantity={quantity})")

    def _check_and_update_ingredient_stock(self, product, quantity, bank):
        for assoc in product.product_ingredients:
            ingredient = assoc.ingredient
            required_qty = assoc.ingredient_quantity * quantity
            if ingredient.stock_quantity < required_qty:
                raise ValueError(f"make_purchase: Insufficient stock for ingredient {ingredient.name} (ingredient_id={ingredient.ingredient_id}, required_qty={required_qty})")
        # If all checks pass, update stock
        for assoc in product.product_ingredients:
            ingredient = assoc.ingredient
            required_qty = assoc.ingredient_quantity * quantity
            ingredient.stock_quantity -= required_qty
            bank.ingredient_value -= required_qty * ingredient.price_per_unit
            for product_assoc in ingredient.ingredient_products:
                product_assoc.product.update_stock()

    def make_purchase(self, user_id: int, product_id: int, quantity: int, session=None, toast_round_id: int = 0) -> Sale:
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError(f"make_purchase: Quantity must be greater than 0 (product_id={product_id}, quantity={quantity})")
            bank = self.get_bank(session)
            product = self.get_product_by_id(product_id, session)
            self._check_product_stock(product, quantity)
            self._check_and_update_ingredient_stock(product, quantity, bank)
            product.update_stock()
            total_cost = product.price_per_unit * quantity
            user = self.get_user_by_id(user_id, session=session)
            if user.balance < total_cost:
                raise ValueError("Insufficient balance")
            purchase = Sale(user_id=user_id, product_id=product_id, quantity=quantity, total_price=total_cost, timestamp=datetime.datetime.now(), toast_round_id=toast_round_id)
            user.balance -= total_cost
            bank.available_balance += total_cost
            bank.product_value -= total_cost
            session.add(purchase)
            if close_session:
                session.commit()
                session.refresh(purchase)
                session.close()
            return purchase
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"make_purchase failed for user_id={user_id}, product_id={product_id}, quantity={quantity}: {e}") from e

    def deposit_cash(self, user_id: int, amount: float, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            bank = self.get_bank(session)
            user = self.get_user_by_id(user_id, session)
            user.balance += amount
            bank.total_balance += amount
            transaction = Transaction(user_id=user_id, amount=amount, transaction_type="deposit", timestamp=datetime.now())
            session.add(transaction)
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"deposit_cash failed for user_id={user_id}, amount={amount}: {e}") from e

    def withdraw_cash(self, user_id: int, amount: float, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            bank = self.get_bank(session)
            user = self.get_user_by_id(user_id, session)
            if user.balance < amount:
                raise ValueError(f"withdraw_cash: Insufficient balance (user_id={user_id}, amount={amount})")
            user.balance -= amount
            bank.total_balance -= amount
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"withdraw_cash failed for user_id={user_id}, amount={amount}: {e}") from e

    def add_toast_round(self, product_id: int, user_selection: List[int], session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            product = self.get_product_by_id(product_id, session)
            if product.category != "toast":
                raise ValueError(f"add_toast_round: Product is not a toast product (product_id={product_id})")
            if product.stock_quantity < len(user_selection):
                raise ValueError(f"add_toast_round: Insufficient stock for this product (product_id={product_id}, needed={len(user_selection)})")
            toast_round = ToastRound(product_id=product.product_id)
            session.add(toast_round)
            for user_id in user_selection:
                user = self.get_user_by_id(user_id, session)
                sale = self.make_purchase(user.user_id, product.product_id, 1, session=session)
                toast_round.sales.append(sale)
            if close_session:
                session.commit()
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"add_toast_round failed for product_id={product_id}, user_selection={user_selection}: {e}") from e

    def get_user_balance(self, user_id: int, session=None) -> float:
        """Get the balance of a user."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = self.get_user_by_id(user_id, session)
            return user.balance
        except Exception as e:
            raise RuntimeError(f"get_user_balance failed for user_id={user_id}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_bank(self, session=None) -> Bank:
        """Get the bank account."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            bank = session.query(Bank).filter_by(account_id=1).first()
            if not bank:
                raise ValueError(BANK_NOT_FOUND_MSG)
            return bank
        except Exception as e:
            raise RuntimeError(f"get_bank failed: {e}") from e
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
            raise RuntimeError(f"get_all_users failed: {e}") from e
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
            raise RuntimeError(f"get_all_products failed: {e}") from e
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
            raise RuntimeError(f"get_all_ingredients failed (eager_load={eager_load}): {e}") from e
        finally:
            if close_session:
                session.close()

    def get_ingredient_by_id(self, ingredient_id: int, session=None) -> Ingredient:
        """Get an ingredient by its ID."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredient = session.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
            if not ingredient:
                raise ValueError(f"Ingredient not found (ingredient_id={ingredient_id})")
            return ingredient
        except Exception as e:
            raise RuntimeError(f"get_ingredient_by_id failed for ingredient_id={ingredient_id}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_ingredients_by_ids(self, ingredient_ids: List[int], session=None) -> List[Ingredient]:
        """Get ingredients by their IDs."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredients = session.query(Ingredient).filter(Ingredient.ingredient_id.in_(ingredient_ids)).all()
            if not ingredients:
                raise ValueError(f"No ingredients found (ingredient_ids={ingredient_ids})")
            return ingredients
        except Exception as e:
            raise RuntimeError(f"get_ingredients_by_ids failed for ingredient_ids={ingredient_ids}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_user_by_id(self, user_id: int, session=None) -> User:
        """Get a user by its ID."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"{USER_NOT_FOUND_MSG} (user_id={user_id})")
            return user
        except Exception as e:
            raise RuntimeError(f"get_user_by_id failed for user_id={user_id}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_product_by_id(self, product_id: int, session=None) -> Product:
        """Get a product by its ID."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            product = session.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                raise ValueError(f"Product not found (product_id={product_id})")
            return product
        except Exception as e:
            raise RuntimeError(f"get_product_by_id failed for product_id={product_id}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_products_by_category(self, category: str, session=None) -> List[Product]:
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
            raise RuntimeError(f"get_all_products_by_category failed for category={category}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_toast_products(self, session=None) -> List[Product]:
        """Get all toast products."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = self.get_all_products_by_category("toast", session)
            return products
        except Exception as e:
            raise RuntimeError(f"get_all_toast_products failed: {e}") from e
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
            raise RuntimeError(f"get_all_toast_rounds failed: {e}") from e
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
            raise RuntimeError(f"get_all_sales failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_sales_with_category(self, category: str, session=None) -> List[Sale]:
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
            raise RuntimeError(f"get_sales_with_category failed for category={category}: {e}") from e
        finally:
            if close_session:
                session.close()


database = Database()