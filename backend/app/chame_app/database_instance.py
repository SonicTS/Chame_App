from __future__ import annotations
import datetime
from typing import Any, List, Optional
from chame_app.database import get_session
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


BANK_NOT_FOUND_MSG = "Bank account not found"
USER_NOT_FOUND_MSG = "User not found"

class Database:
    def __init__(self):
        self.session = get_session()
        bank = self.session.query(Bank).filter_by(account_id=1).first()
        if not bank:
            bank = Bank()
            self.session.add(bank)
            self.session.commit()
            self.session.refresh(bank)
        if not self.session.query(User).filter_by(role="admin").first():
            admin_user = User(name="admin", balance=0, password_hash="password", role="admin")
            self.session.add(admin_user)
            self.session.commit()
            self.session.refresh(admin_user)
        for product in self.session.query(Product).all():
            product.update_stock()
        self.session.close()

    def get_session(self):
        """Create a new session."""
        try:
            return self.session
        except Exception as e:
            raise RuntimeError(f"get_session failed: {e}") from e
        
    def get_user_by_username(self, username: str, session=None) -> Optional[User]:
        """Get a user by username."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            user = session.query(User).options(
                joinedload(User.sales)
            ).filter(User.name == username).first()
            if not user:
                raise ValueError(f"{USER_NOT_FOUND_MSG} (username={username})")
            return user
        except Exception as e:
            raise RuntimeError(f"get_user_by_username failed for username={username}: {e}") from e
        finally:
            if close_session:
                session.close()

    def change_password(self, user_id: int, old_password: str, new_password: str, session=None):
        close_session = False
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            user = self.get_user_by_id(user_id, session)
            if not user:
                raise ValueError(f"{USER_NOT_FOUND_MSG} (user_id={user_id})")
            if user.verify_password(old_password):
                user.password_hash = user.hash_password(new_password)
            else:
                raise ValueError("Old password is incorrect")
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

    def add_ingredient(self, name: str, price_per_package: float, stock_quantity: int, number_ingredients: int, pfand: float = 0.0, session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if self.exists_ingredient_with_name(name, session):
                print(f"DEBUG: Ingredient with name '{name}' already exists")
                raise ValueError(f"Ingredient with name '{name}' already exists")
            stock = int(stock_quantity)
            price = float(price_per_package)
            number_ingredients = int(number_ingredients)
            print(f"DEBUG: Adding ingredient {name} with price={price}, stock={stock}, number_ingredients={number_ingredients}")
            if number_ingredients <= 0:
                print("DEBUG: Number of ingredients must be greater than 0")
                raise ValueError("Number of ingredients must be greater than 0")
            price_per_unit = price / number_ingredients
            stock = stock * number_ingredients
            print(f"DEBUG: Calculated price_per_unit={price_per_unit} for ingredient {name}")
            ingredient = Ingredient(name=name, price_per_package=price, number_of_units=number_ingredients, price_per_unit=price_per_unit, stock_quantity=stock, pfand=pfand)
            print(f"DEBUG: Created ingredient {ingredient}")
            if stock > 0:
                bank = self.get_bank(session)
                bank.ingredient_value += price_per_unit * stock + pfand * stock
                bank.costs_total += price_per_unit * stock + pfand * stock
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

    def restock_ingredients(self, _list: List[dict[int, int]], session=None):
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if not _list or not isinstance(_list, list):
                raise ValueError("Invalid input: _list must be a non-empty list")
            total_cost = 0.0
            for item in _list:
                print(f"DEBUG: Restocking item: {item}")
                if not isinstance(item, dict) or 'id' not in item or 'restock' not in item:
                    raise ValueError("Invalid input: each item must be a dictionary with 'id' and 'restock' keys")
                ingredient_id = item['id']
                quantity = item['restock']
                price = item.get('price', None)
                print(f"DEBUG: Restocking ingredient_id={ingredient_id}, quantity={quantity}, price={price}")
                total_cost += self.stock_ingredient(ingredient_id, quantity, price=price, session=session)
            
            bank = self.get_bank(session)
            if bank.total_balance < total_cost:
                raise ValueError(f"Insufficient balance {bank.total_balance}")
            bank.total_balance -= total_cost
            if bank.revenue_funds < total_cost:
                print("DEBUG: Not enough revenue funds, draining customer_funds")
                bank.revenue_funds -= total_cost
                bank.profit_retained = 0
                bank.costs_reserved = 0
            elif bank.costs_reserved < total_cost:
                # Assuming first draining cost_reserves, then profit_retained
                bank.profit_retained -= (total_cost - bank.costs_reserved)
                bank.costs_reserved = 0
                bank.revenue_funds -= total_cost
            else:
                bank.costs_reserved -= total_cost
                bank.revenue_funds -= total_cost
            bank.profit_total = bank.revenue_total - bank.costs_total
            description = "Restock: " + ", ".join([f"{self.get_ingredient_by_id(item['id'], session).name} ({item['restock']}): {item.get('price', self.get_ingredient_by_id(item['id'], session).price_per_package)}€" for item in _list])
            transaction = BankTransaction(amount=total_cost, type="withdraw", description=description)
            session.add(transaction)
            if close_session:
                session.commit()
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"restock_ingredients failed: {e}") from e

    def stock_ingredient(self, ingredient_id: int, quantity: int, price: Optional[float] = None, session=None) -> float:
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
            if price is None:
                price = ingredient.price_per_unit
            else:
                price = float(price) / ingredient.number_of_units
                if price <= 0:
                    raise ValueError("Price must be greater than 0")
            print(f"DEBUG: Stocking ingredient {ingredient_name} with price={price}, quantity={quantity}")
            bank.costs_total += price * quantity + ingredient.pfand * quantity
            bank.ingredient_value += price * quantity + ingredient.pfand * quantity
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
            return price * quantity + ingredient.pfand * quantity
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"stock_ingredient failed for ingredient={ingredient_name}, quantity={quantity}: {e}") from e

    def add_product(self, name: str, ingredients: List[tuple[Ingredient, float]], price_per_unit: float = 0.0, category: str = "raw", toaster_space: Optional[int] = None, session=None):
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
                print(f"DEBUG: ingredients: {ingredients}")
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
                ingredient_quantity = extend_float_precision(float(quantity))
                if ingredient_quantity <= 0:
                    raise ValueError(f"Ingredient quantity must be greater than 0 (ingredient={ingredient_obj.name})")
                cost_per_unit += ingredient_obj.price_per_unit * ingredient_quantity
            profit_per_unit = price - cost_per_unit
            product = Product(name=name, price_per_unit=price, category=category, 
                              toaster_space=toaster_space, cost_per_unit=cost_per_unit, profit_per_unit=profit_per_unit)
            session.add(product)
            session.flush()
            for ingredient_obj, quantity in ingredients:
                ingredient_quantity = extend_float_precision(float(quantity))
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
            user = User(name=username, balance=balance, password_hash=password, role=role.lower())
            bank = self.get_bank(session)
            bank.total_balance += balance
            bank.customer_funds += balance
            session.add(user)
            session.flush()
            if balance > 0:
                transaction = Transaction(user_id=user.user_id, amount=balance, type="deposit", timestamp=datetime.datetime.now().replace(second=0, microsecond=0))
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

    def return_deposit(self, user_id: int, product_quantity_list: List[Any], session=None):
        """Return deposit for a list of products."""
        print(f"DEBUG: Returning deposit for user_id={user_id}, product_quantity_list={product_quantity_list}")
        close_session = False
        product_name = "404"
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            total_pfand = 0.0
            for item in product_quantity_list:
                print(f"DEBUG: Returning deposit for item: {item}")
                quantity = int(item['amount'])
                product = self.get_product_by_id(item['id'], session)
                product_name = product.name
                if quantity <= 0:
                    raise ValueError("return_deposit: Quantity must be greater than 0")
                bank = self.get_bank(session)
                user = self.get_user_by_id(user_id, session=session)
                user_name = user.name
                pfand = product.get_pfand() * quantity
                user.balance += pfand
                bank.customer_funds += pfand
                bank.revenue_funds -= pfand
                if bank.revenue_funds < 0:
                    bank.costs_reserved = 0
                    bank.profit_retained = 0
                else:
                    if bank.profit_retained > pfand:
                        bank.profit_retained -= pfand
                    else:
                        bank.costs_reserved -= pfand
                        bank.costs_reserved += bank.profit_retained
                        bank.profit_retained = 0
                total_pfand += pfand
            comment = f"User {user_name} returned deposit for " + ", ".join([f"{item['amount']}x {self.get_product_by_id(item['id'], session).name}" for item in product_quantity_list])
            transaction = Transaction(user_id=user_id, amount=total_pfand, type="deposit", timestamp=datetime.datetime.now().replace(second=0, microsecond=0), comment=comment)
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
            raise RuntimeError(f"return_deposit failed for User={user_name}, Product={product_name}, quantity={quantity}: {e}") from e

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
            total_cost = product.price_per_unit * quantity + product.get_pfand() * quantity
            user = self.get_user_by_id(user_id, session=session)
            user_name = user.name
            if user.balance < total_cost:
                raise ValueError(f"Insufficient balance: {user.balance}")
            purchase = Sale(user_id=user_id, product_id=product_id, quantity=quantity, total_price=total_cost, timestamp=datetime.datetime.now().replace(second=0, microsecond=0), toast_round_id=toast_round_id)
            user.balance -= total_cost
            bank.customer_funds -= total_cost
            bank.revenue_total += total_cost
            if bank.revenue_funds < 0 and total_cost > abs(bank.revenue_funds):
                if product.cost_per_unit * quantity + product.get_pfand() * quantity >= bank.revenue_funds + total_cost:
                    bank.costs_reserved = bank.revenue_funds + total_cost
                    bank.profit_retained = 0
                else:
                    bank.costs_reserved = product.cost_per_unit * quantity + product.get_pfand() * quantity
                    bank.profit_retained = bank.revenue_funds + total_cost - bank.costs_reserved
            bank.revenue_funds += total_cost
            bank.profit_total = bank.revenue_total - bank.costs_total
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
            bank.customer_funds += amount
            transaction = Transaction(user_id=user_id, amount=amount, type="deposit", timestamp=datetime.datetime.now().replace(second=0, microsecond=0))
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
            bank.customer_funds -= amount
            transaction = Transaction(user_id=user_id, amount=amount, type="withdraw", timestamp=datetime.datetime.now().replace(second=0, microsecond=0))
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
            if bank.total_balance < amount:
                raise ValueError(f"Insufficient balance {bank.total_balance}")
            bank.total_balance -= amount
            if bank.revenue_funds < amount:
                print("DEBUG: Not enough revenue funds, draining customer_funds")
                bank.revenue_funds -= amount
                bank.profit_retained = 0
                bank.costs_reserved = 0
            elif bank.costs_reserved < amount:
                # Assuming first draining cost_reserves, then profit_retained
                bank.profit_retained -= (amount - bank.costs_reserved)
                bank.costs_reserved = 0
                bank.revenue_funds -= amount
            else:
                bank.costs_reserved -= amount
                bank.revenue_funds -= amount
            bank.costs_total += amount
            bank.profit_total = bank.revenue_total - bank.costs_total
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

    def get_all_users(self, session=None) -> 'List[User]':
        """Get all users with eager loading of sales."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            users = session.query(User).options(
                joinedload(User.sales)
            ).all()
            return users
        except Exception as e:
            raise RuntimeError(f"get_all_users failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_products(self, session=None) -> 'List[Product]':
        """Get all products with ingredients and sales eager loaded."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = session.query(Product).options(
                joinedload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
                joinedload(Product.sales),
                joinedload(Product.product_toast_rounds).joinedload(ProductToastround.toast_round)
            ).all()
            return products
        except Exception as e:
            raise RuntimeError(f"get_all_products failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_ingredients(self, eager_load=False, session=None) -> 'List[Ingredient]':
        """Get all ingredients, with optional eager loading of products."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            query = session.query(Ingredient)
            if eager_load:
                query = query.options(
                    joinedload(Ingredient.ingredient_products)
                    .joinedload(ProductIngredient.product)
                    .joinedload(Product.product_ingredients)
                    .joinedload(ProductIngredient.ingredient)
                )
            ingredients = query.all()
            return ingredients
        except Exception as e:
            raise RuntimeError(f"get_all_ingredients failed (eager_load={eager_load}): {e}") from e
        finally:
            if close_session:
                session.close()

    def get_ingredient_by_id(self, ingredient_id: int, session=None) -> 'Ingredient':
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

    def get_ingredients_by_ids(self, ingredient_ids: List[int], session=None) -> 'List[Ingredient]':
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

    def get_user_by_id(self, user_id: int, session=None) -> 'User':
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

    def get_product_by_id(self, product_id: int, session=None) -> 'Product':
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

    def get_all_products_by_category(self, category: str, session=None) -> 'List[Product]':
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

    def get_all_toast_products(self, session=None) -> 'List[Product]':
        """Get all toast products with ingredients, sales, and toast round relationships eager loaded."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = session.query(Product).options(
                joinedload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
                joinedload(Product.sales),
                joinedload(Product.product_toast_rounds).joinedload(ProductToastround.toast_round)
            ).filter(Product.category == "toast").all()
            return products
        except Exception as e:
            raise RuntimeError(f"get_all_toast_products failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_toast_rounds(self, session=None) -> 'List[ToastRound]':
        """Get all toast rounds with sales, user, product, and toast_round_products eager loaded."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            toast_rounds = session.query(ToastRound).options(
                joinedload(ToastRound.sales).joinedload(Sale.user),
                joinedload(ToastRound.sales).joinedload(Sale.product),
                joinedload(ToastRound.toast_round_products).joinedload(ProductToastround.product)
            ).all()
            return toast_rounds
        except Exception as e:
            raise RuntimeError(f"get_all_toast_rounds failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_all_sales(self, session=None) -> 'List[Sale]':
        """Get all sales with eager loading of user, product, toast_round, and product ingredients."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            sales = session.query(Sale).options(
                joinedload(Sale.user),
                joinedload(Sale.product)
                .joinedload(Product.product_ingredients)
                .joinedload(ProductIngredient.ingredient),
                joinedload(Sale.toast_round)
            ).all()
            return sales
        except Exception as e:
            raise RuntimeError(f"get_all_sales failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_sales_with_category(self, category: str, session=None) -> 'List[Sale]':
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

    def get_filtered_transaction(self, user_id: int, tx_type: str, session=None) -> 'List[Transaction]':
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

    def get_bank_transaction(self, session=None) -> 'List[BankTransaction]':
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

def extend_float_precision(value: float, precision: int = 16) -> float:
    """
    Extends the last digit of a float's decimal part to the specified precision.
    E.g., 0.33 -> 0.3333333333333333
    """
    s = str(value)
    if '.' not in s:
        return value
    int_part, dec_part = s.split('.')
    if len(dec_part) <= 1:
        return value
    last_digit = dec_part[-1]
    extended_dec = dec_part + last_digit * (precision - len(dec_part))
    extended_str = f"{int_part}.{extended_dec[:precision]}"
    return float(extended_str)


#database = Database()