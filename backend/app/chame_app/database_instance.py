import datetime
from typing import List, Optional
from chame_app.database import engine, SessionLocal
from models.ingredient import Ingredient
from models.product_ingredient_table import ProductIngredient
from models.product_table import Product
from models.product_toastround_table import ProductToastround
from models.sales_table import Sale
from models.toast_round import ToastRound
from models.user_table import User
from models.transaction_table import Transaction
from models.bank_table import Bank, BankTransaction
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
            bank = Bank(total_balance=0.0, available_balance=0.0, ingredient_value=0.0, restocking_cost=0.0, profit_balance=0.0)
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
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"{USER_NOT_FOUND_MSG} (user_id={user_id})")
            user_name = user.name
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
            raise RuntimeError(f"change_password failed for User={user_name}: {e}") from e

    def add_ingredient(self, name: str, price_per_package: float, stock_quantity: int, number_ingredients: int, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if self.exists_ingredient_with_name(name, session):
                raise ValueError(f"Ingredient with name '{name}' already exists")
            stock = int(stock_quantity)
            price = float(price_per_package)
            number_ingredients = int(number_ingredients)
            if number_ingredients <= 0:
                raise ValueError("Number of ingredients must be greater than 0")
            price_per_unit = price / number_ingredients
            stock = stock * number_ingredients
            ingredient = Ingredient(name=name, price_per_package=price, number_of_units=number_ingredients, price_per_unit=price_per_unit, stock_quantity=stock)
            if stock > 0:
                bank = self.get_bank(session)
                bank.ingredient_value += price_per_unit * stock
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
            raise RuntimeError(f"add_ingredient failed for ingredient={name}: {e}") from e

    def stock_ingredient(self, ingredient_id: int, quantity: int, session=None):
        close_session = False
        ingredient_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            ingredient = self.get_ingredient_by_id(ingredient_id, session)
            ingredient_name = ingredient.name
            quantity = int(quantity)
            quantity = quantity * ingredient.number_of_units
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
            if close_session:
                session.commit()
                session.refresh(ingredient)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"stock_ingredient failed for ingredient={ingredient_name}, quantity={quantity}: {e}") from e

    def add_product(self, name: str, ingredients: List[tuple[Ingredient, int]], price_per_unit: float = 0.0, category: str = "raw", toaster_space: Optional[int] = None, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if self.exists_product_with_name(name, session):
                raise ValueError(f"Product with name '{name}' already exists")
            if len(ingredients) == 0:
                raise ValueError("Product must have at least one ingredient")
            if len(ingredients) > 1 and category == "raw":
                raise ValueError("Raw products can only have one ingredient")
            price = float(price_per_unit)
            if toaster_space:
                toaster_space = int(toaster_space)
                if toaster_space < 1:
                    raise ValueError("Toaster space must be at least 1")
            else:
                toaster_space = 0
            cost_per_unit = 0.0
            for ingredient_obj, quantity in ingredients:
                ingredient_quantity = int(quantity)
                if ingredient_quantity <= 0:
                    raise ValueError(f"Ingredient quantity must be greater than 0 (ingredient={ingredient_obj.name})")
                cost_per_unit += ingredient_obj.price_per_unit * ingredient_quantity
            profit_per_unit = price - cost_per_unit
            product = Product(name=name, price_per_unit=price, category=category, 
                              toaster_space=toaster_space, cost_per_unit=cost_per_unit, profit_per_unit=profit_per_unit)
            session.add(product)
            session.flush()
            for ingredient_obj, quantity in ingredients:
                ingredient_quantity = int(quantity)
                existing_ingredient = self.get_ingredient_by_id(ingredient_obj.ingredient_id, session)
                association = ProductIngredient(product=product, ingredient=existing_ingredient, ingredient_quantity=ingredient_quantity)
                session.add(association)
            product.update_stock()
            if close_session:
                session.commit()
                session.refresh(product)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"add_product failed for Product={name}: {e}") from e

    def add_user(self, username: str, password: str, role: str = "user", balance: float = 0.0, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if username == "bank":
                raise ValueError("Username 'bank' is reserved and cannot be used")
            balance = float(balance)
            user = User(name=username, balance=balance, password_hash=password, role=role)
            bank = self.get_bank(session)
            bank.total_balance += balance
            session.add(user)
            session.flush()
            if balance > 0:
                transaction = Transaction(user_id=user.user_id, amount=balance, type="deposit", timestamp=datetime.datetime.now())
                session.add(transaction)
            if close_session:
                session.commit()
                if balance > 0:
                    session.refresh(transaction)
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
            raise ValueError("Insufficient stock for this product)")

    def _check_and_update_ingredient_stock(self, product, quantity, bank):
        for assoc in product.product_ingredients:
            ingredient = assoc.ingredient
            required_qty = assoc.ingredient_quantity * quantity
            if ingredient.stock_quantity < required_qty:
                raise ValueError(f"Insufficient stock for ingredient {ingredient.name}, required_qty={required_qty})")
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
        product_name = "404"
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            quantity = int(quantity)
            product = self.get_product_by_id(product_id, session)
            product_name = product.name
            if quantity <= 0:
                raise ValueError("make_purchase: Quantity must be greater than 0")
            bank = self.get_bank(session)
            self._check_product_stock(product, quantity)
            self._check_and_update_ingredient_stock(product, quantity, bank)
            product.update_stock()
            total_cost = product.price_per_unit * quantity
            user = self.get_user_by_id(user_id, session=session)
            user_name = user.name
            if user.balance < total_cost:
                raise ValueError(f"Insufficient balance: {user.balance}")
            purchase = Sale(user_id=user_id, product_id=product_id, quantity=quantity, total_price=total_cost, timestamp=datetime.datetime.now(), toast_round_id=toast_round_id)
            user.balance -= total_cost
            bank.available_balance += total_cost
            bank.restocking_cost += total_cost - product.profit_per_unit * quantity
            bank.profit_balance += product.profit_per_unit * quantity
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
            raise RuntimeError(f"make_purchase failed for User={user_name}, Product={product_name}, quantity={quantity}: {e}") from e

    def deposit_cash(self, user_id: int, amount: float, session=None):
        close_session = False
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            bank = self.get_bank(session)
            user = self.get_user_by_id(user_id, session)
            user_name = user.name
            amount = float(amount)
            user.balance += amount
            bank.total_balance += amount
            transaction = Transaction(user_id=user_id, amount=amount, type="deposit", timestamp=datetime.datetime.now())
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
            raise RuntimeError(f"deposit_cash failed for User={user_name}, amount={amount}: {e}") from e

    def withdraw_cash(self, user_id: int, amount: float, session=None):
        close_session = False
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            bank = self.get_bank(session)
            user = self.get_user_by_id(user_id, session)
            user_name = user.name
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0 ")
            if user.balance < amount:
                raise ValueError(f"Insufficient balance {user.balance}")
            user.balance -= amount
            bank.total_balance -= amount
            transaction = Transaction(user_id=user_id, amount=amount, type="withdraw", timestamp=datetime.datetime.now())
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
            raise RuntimeError(f"withdraw_cash failed for User={user_name}, amount={amount}: {e}") from e

    def withdraw_cash_from_bank(self, amount: float, description: str = "Withdrawal from bank", session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            bank = self.get_bank(session)
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0 ")
            if bank.available_balance < amount:
                raise ValueError(f"Insufficient balance {bank.available_balance}")
            bank.total_balance -= amount
            bank.available_balance -= amount
            if bank.restocking_cost < amount:
                bank.profit_balance -= (amount - bank.restocking_cost)
                bank.restocking_cost = 0
            else:
                bank.restocking_cost -= amount
            transaction = BankTransaction(amount=amount, type="withdraw", description=description)
            session.add(transaction)
            if close_session:
                session.commit()
                session.refresh(bank)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"withdraw_cash_from_bank failed for amount={amount}: {e}") from e
   
    def add_toast_round(self, product_user_list: List[tuple[int, int]], session=None):
        close_session = False
        name_list = ["404"]
        try:
            if session is None:
                session = self.get_session()
                close_session = True

            toast_round = ToastRound()
            session.add(toast_round)
            session.flush()
            unique_products = set()
            name_list = []
            for product_id, user_id in product_user_list:
                unique_products.add(product_id)
                product = self.get_product_by_id(product_id, session)
                user = self.get_user_by_id(user_id, session)
                sale = self.make_purchase(user.user_id, product.product_id, 1, session=session, toast_round_id=toast_round.toast_round_id)
                toast_round.sales.append(sale)
                name_list.append(f"{user.name} bought {product.name}")
            for product_id in unique_products:
                product_toast_round = ProductToastround(product_id=product_id, toast_round_id=toast_round.toast_round_id)
                session.add(product_toast_round)
            if close_session:
                session.commit()
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"add_toast_round failed for round={name_list}: {e}") from e

    def get_user_balance(self, user_id: int, session=None) -> float:
        """Get the balance of a user."""
        close_session = False
        user_name = "404"
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = self.get_user_by_id(user_id, session)
            user_name = user.name
            return user.balance
        except Exception as e:
            raise RuntimeError(f"get_user_balance failed for User={user_name}: {e}") from e
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
        """Get all users."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            users = session.query(User).all()
            return users
        except Exception as e:
            raise RuntimeError(f"get_all_users failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_products(self, session=None) -> List[Product]:
        """Get all products with ingredients eager loaded."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = session.query(Product).options(
                joinedload(Product.product_ingredients).joinedload(ProductIngredient.ingredient)
            ).all()
            return products
        except Exception as e:
            raise RuntimeError(f"get_all_products failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_ingredients(self, eager_load=False, session=None) -> List[Ingredient]:
        """Get all ingredients, with optional eager loading of products."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            query = session.query(Ingredient)
            if eager_load:
                query = query.options(joinedload(Ingredient.ingredient_products).joinedload(ProductIngredient.product))
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
        """Get all products by category, with ingredients eager loaded."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = session.query(Product).options(
                joinedload(Product.product_ingredients).joinedload(ProductIngredient.ingredient)
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
        """Get all toast rounds with sales, user, and product eager loaded."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            toast_rounds = session.query(ToastRound).options(
                joinedload(ToastRound.sales).joinedload(Sale.user),
                joinedload(ToastRound.sales).joinedload(Sale.product)
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
                joinedload(Sale.user),
                joinedload(Sale.product)
            ).join(Product).filter(Product.category == category).all()
            return sales
        except Exception as e:
            raise RuntimeError(f"get_sales_with_category failed for category={category}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_filtered_transaction(self, user_id: int, tx_type: str, session=None) -> List[Transaction]:
        """Get filtered transactions."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            query = session.query(Transaction).options(
                joinedload(Transaction.user),
            )
            if user_id != "all":
                user_id = int(user_id)
                query = query.filter(Transaction.user_id == user_id)
            if tx_type != "all":
                query = query.filter(Transaction.type == tx_type)
            transactions = query.all()
            return transactions
        except Exception as e:
            raise RuntimeError(f"get_filtered_transaction failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_bank_transaction(self, session=None) -> List[BankTransaction]:
        """Get filtered transactions."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            transactions = session.query(BankTransaction).all()
            return transactions
        except Exception as e:
            raise RuntimeError(f"get_bank_transaction failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def exists_ingredient_with_name(self, name: str, session=None) -> bool:
        """Check if an ingredient exists by name."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredient = session.query(Ingredient).filter(Ingredient.name == name).first()
            return ingredient is not None
        except Exception as e:
            raise RuntimeError(f"exists_ingredient_with_name failed for name={name}: {e}") from e
        finally:
            if close_session:
                session.close()

    def exists_product_with_name(self, name: str, session=None) -> bool:
        """Check if a product exists by name."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            product = session.query(Product).filter(Product.name == name).first()
            return product is not None
        except Exception as e:
            raise RuntimeError(f"exists_product_with_name failed for name={name}: {e}") from e
        finally:
            if close_session:
                session.close()


database = Database()