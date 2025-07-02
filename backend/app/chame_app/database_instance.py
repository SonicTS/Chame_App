from __future__ import annotations
import datetime
from typing import Any, List, Optional
from models.pfand_table import PfandHistory
from chame_app.database import get_session
from models.ingredient import Ingredient
from models.product_ingredient_table import ProductIngredient
from models.product_table import Product
from models.sales_table import Sale
from models.toast_round import ToastRound
from models.user_table import User
from models.transaction_table import Transaction
from models.bank_table import Bank, BankTransaction
from chame_app.database import Base
from sqlalchemy.orm import joinedload
from sqlalchemy import text
from utils.firebase_logger import log_info, log_warn, log_error, log_debug


BANK_NOT_FOUND_MSG = "Bank account not found"
USER_NOT_FOUND_MSG = "User not found"

class Database:
    def __init__(self, apply_migrations: bool = True):
        self.session = get_session()
        # Run migrations to ensure database is up to date
        if apply_migrations:
            self._ensure_migrations_applied()
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
        
        

    def _ensure_migrations_applied(self):
        """Ensure database migrations are applied if needed"""
        try:
            from chame_app.database import _engine
            from chame_app.simple_migrations import SimpleMigrations
            
            if _engine is None:
                return  # Engine not initialized yet
            
            migrations = SimpleMigrations(_engine)
            # Create backup before migrations (True by default)
            migrations.run_migrations(create_backup=True)
            
        except Exception as e:
            print(f"⚠️ Warning: Migration check failed: {e}")
            # Don't raise - database creation should continue even if migrations fail

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
            user = User.active_only(session.query(User)).options(
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
        
    def change_user_role(self, user_id: int, new_role: str, session=None):
        close_session = False
        user_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            user = self.get_user_by_id(user_id, session)
            if not user:
                raise ValueError(f"{USER_NOT_FOUND_MSG} (user_id={user_id})")
            if new_role.lower() not in ["user", "admin", "wirt"]:
                raise ValueError("Role must be 'user', 'admin', or 'wirt'")
            user.role = new_role.lower()
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
        except Exception as e:
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"change_user_role failed for User={user_name}, new_role={new_role}: {e}") from e

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
            description = "Restock: "
            for item in _list:
                ingredient = self.get_ingredient_by_id(item['id'], session)
                price = item.get('price') if item.get('price') is not None else ingredient.price_per_package
                pfand = ingredient.pfand if ingredient.pfand else 0.0
                print(f"DEBUG: Ingredient {ingredient.name} restock={item['restock']}, price={price}, pfand={pfand}")
                description += f"{ingredient.name} x{item['restock']}: {price}(+{pfand})€ = {item['restock'] * (price + pfand)}\n"
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
            log_debug(f"Adding product {name} with price={price}, category={category}, toaster_space={toaster_space}, ingredients={ingredients}")
            cost_per_unit = 0.0
            for ingredient_obj, quantity in ingredients:
                ingredient_quantity = extend_float_precision(float(quantity))
                if ingredient_quantity <= 0:
                    raise ValueError(f"Ingredient quantity must be greater than 0 (ingredient={ingredient_obj.name})")
                cost_per_unit += ingredient_obj.price_per_unit * ingredient_quantity
                log_debug(f"Ingredient {ingredient_obj.name} contributes {ingredient_obj.price_per_unit} * {ingredient_quantity} = {ingredient_obj.price_per_unit * ingredient_quantity} to cost")
            profit_per_unit = price - cost_per_unit
            log_debug(f"Calculated cost_per_unit={cost_per_unit}, profit_per_unit={profit_per_unit} for product {name}")
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
        print("🔥 [DATABASE] Logging user creation to Firebase...")
        log_info("User creation initiated", {"operation": "add_user", "username": username, "role": role, "balance": balance})
        print("✅ [DATABASE] User creation initiation logged to Firebase")
        
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if username == "bank":
                print("⚠️ [DATABASE] Logging reserved username attempt to Firebase...")
                log_warn("Reserved username attempted", {"operation": "add_user", "username": username, "error": "Username 'bank' is reserved"})
                print("✅ [DATABASE] Reserved username warning logged to Firebase")
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
                
            print("🔥 [DATABASE] Logging successful user creation to Firebase...")
            log_info("User created successfully", {"operation": "add_user", "username": username, "user_id": user.user_id, "role": role, "balance": balance})
            print("✅ [DATABASE] User creation success logged to Firebase")
            
        except Exception as e:
            print("❌ [DATABASE] Logging user creation failure to Firebase...")
            log_error("User creation failed", {"operation": "add_user", "username": username, "role": role, "error": str(e)})
            print("✅ [DATABASE] User creation failure logged to Firebase")
            
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
                pfand_history = self.get_pfand_history(user_id, product.product_id, session=session)
                print(f"DEBUG: Pfand history for user_id={user_id}, product_id={product.product_id}: {pfand_history}")
                if not pfand_history or pfand_history.counter < quantity:
                    raise ValueError(f"Insufficient deposit history for product {product.name} (requested: {quantity}, available: {pfand_history.counter if pfand_history else 0})")
                pfand_history.counter -= quantity
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

    def make_multiple_purchases(self, item_list: List[dict], session=None):
        """Make multiple purchases in a single transaction."""
        close_session = False
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            if not item_list or not isinstance(item_list, list):
                raise ValueError("Invalid input: item_list must be a non-empty list")
            for item in item_list:
                if not isinstance(item, dict) or 'product_id' not in item or 'quantity' not in item or 'consumer_id' not in item:
                    raise ValueError("Each item must be a dict with 'product_id', 'quantity', and 'consumer_id'")
            purchases = []
            for item in item_list:
                purchase = self.make_purchase(item['consumer_id'], item['product_id'], item['quantity'], donator_id=item.get('donator_id', None), session=session)
                purchases.append(purchase)
            if close_session:
                session.commit()
                session.close()
            return purchases
        except Exception as e:           
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"make_multiple_purchases failed: {e}") from e

    def make_purchase(self, consumer_id: int, product_id: int, quantity: int, session=None, toast_round_id: int = 0, donator_id: Optional[int] = None) -> Sale:
        # Firebase logging with debug output
        print("🔥 [DATABASE] Logging purchase initiation to Firebase...")
        log_info("Purchase initiated", {"operation": "make_purchase", "consumer_id": consumer_id, "product_id": product_id, "quantity": quantity})
        print("✅ [DATABASE] Purchase initiation logged to Firebase")
        
        close_session = False
        product_name = "404"
        payer_name = "404"
        try:
            if session is None:
                session = self.get_session()
                close_session = True
            quantity = int(quantity)
            product = self.get_product_by_id(product_id, session)
            product_name = product.name
            if quantity <= 0:
                print("⚠️ [DATABASE] Logging invalid purchase quantity to Firebase...")
                log_warn("Invalid purchase quantity", {"operation": "make_purchase", "consumer_id": consumer_id, "product": product_name, "quantity": quantity})
                print("✅ [DATABASE] Invalid quantity warning logged to Firebase")
                raise ValueError("make_purchase: Quantity must be greater than 0")
            payer_id = consumer_id
            if donator_id is not None:
                payer_id = donator_id
            bank = self.get_bank(session)
            self._check_product_stock(product, quantity)
            self._check_and_update_ingredient_stock(product, quantity, bank)
            product.update_stock()
            total_cost = product.price_per_unit * quantity + product.get_pfand() * quantity
            payer = self.get_user_by_id(payer_id, session=session)
            payer_name = payer.name
            if payer.balance < total_cost:
                print("⚠️ [DATABASE] Logging insufficient balance to Firebase...")
                log_warn("Insufficient balance for purchase", {"operation": "make_purchase", "consumer_id": consumer_id, "product": product_name, "payer": payer_name, "required": total_cost, "balance": payer.balance})
                print("✅ [DATABASE] Insufficient balance warning logged to Firebase")
                raise ValueError(f"Insufficient balance: {payer.balance}")
            purchase = Sale(consumer_id=consumer_id, donator_id=donator_id, product_id=product_id, quantity=quantity, total_price=total_cost, timestamp=datetime.datetime.now().replace(second=0, microsecond=0), toast_round_id=toast_round_id)
            if product.get_pfand() > 0:
                pfand_history = self.get_pfand_history(consumer_id, product_id, session=session)
                if pfand_history:
                    pfand_history.counter += quantity
                else:
                    pfand_history = PfandHistory(user_id=consumer_id, product_id=product_id, counter=quantity)
                    session.add(pfand_history)
            payer.balance -= total_cost
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
            
            print("🔥 [DATABASE] Logging successful purchase to Firebase...")
            log_info("Purchase completed successfully", {"operation": "make_purchase", "consumer_id": consumer_id, "product": product_name, "quantity": quantity, "total_cost": total_cost, "payer": payer_name, "sale_id": purchase.sale_id})
            print("✅ [DATABASE] Purchase success logged to Firebase")
            
            return purchase
        except Exception as e:
            print("❌ [DATABASE] Logging purchase failure to Firebase...")
            log_error("Purchase failed", {"operation": "make_purchase", "consumer_id": consumer_id, "product": product_name, "quantity": quantity, "payer": payer_name, "error": str(e)})
            print("✅ [DATABASE] Purchase failure logged to Firebase")
            
            if session:
                session.rollback()
                if close_session:
                    session.close()
            raise RuntimeError(f"make_purchase failed for User={payer_name}, Product={product_name}, quantity={quantity}: {e}") from e

    def deposit_cash(self, user_id: int, amount: float, session=None):
        print("🔥 [DATABASE] Logging cash deposit to Firebase...")
        log_info("Cash deposit initiated", {"operation": "deposit_cash", "user_id": user_id, "amount": amount})
        print("✅ [DATABASE] Cash deposit initiation logged to Firebase")
        
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
                print("⚠️ [DATABASE] Logging invalid deposit amount to Firebase...")
                log_warn("Invalid deposit amount", {"operation": "deposit_cash", "user_id": user_id, "username": user_name, "amount": amount})
                print("✅ [DATABASE] Invalid amount warning logged to Firebase")
                raise ValueError("Amount must be greater than 0 ")
            
            old_balance = user.balance
            user.balance += amount
            bank.total_balance += amount
            bank.customer_funds += amount
            transaction = Transaction(user_id=user_id, amount=amount, type="deposit", timestamp=datetime.datetime.now().replace(second=0, microsecond=0))
            session.add(transaction)
            if close_session:
                session.commit()
                session.refresh(user)
                session.close()
                
            print("🔥 [DATABASE] Logging successful cash deposit to Firebase...")
            log_info("Cash deposit completed successfully", {"operation": "deposit_cash", "user_id": user_id, "username": user_name, "amount": amount, "old_balance": old_balance, "new_balance": user.balance})
            print("✅ [DATABASE] Cash deposit success logged to Firebase")
            
        except Exception as e:
            print("❌ [DATABASE] Logging cash deposit failure to Firebase...")
            log_error("Cash deposit failed", {"operation": "deposit_cash", "user_id": user_id, "username": user_name, "amount": amount, "error": str(e)})
            print("✅ [DATABASE] Cash deposit failure logged to Firebase")
            
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
   
    def add_toast_round(self, product_user_list: List[tuple[int, int, int]], session=None):
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
            for product_id, consumer_id, donator_id in product_user_list:
                unique_products.add(product_id)
                product = self.get_product_by_id(product_id, session)
                consumer = self.get_user_by_id(consumer_id, session)
                donator = self.get_user_by_id(donator_id, session) if donator_id else None
                sale = self.make_purchase(consumer.user_id, product.product_id, 1, session=session, toast_round_id=toast_round.toast_round_id, donator_id=donator.user_id if donator else None)
                toast_round.sales.append(sale)
                buyer_str = f"{donator.name}({consumer.name})" if donator else f"{consumer.name}"
                name_list.append(f"{buyer_str} bought {product.name}")
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
        try:
            #log_debug("Fetching all active users")
            
            close_session = False
            if session is None:
                session = self.get_session()
                close_session = True
            try:
                users = User.active_only(session.query(User)).options(
                    joinedload(User.sales)
                ).all()
                
                #log_debug(f"Retrieved {len(users)} active users")
                return users
            except Exception as e:
                log_error("Failed to fetch all users", exception=e)
                raise RuntimeError(f"get_all_users failed: {e}") from e
            finally:
                if close_session:
                    session.close()
        except Exception as e:
            log_error("Critical error in get_all_users", exception=e)
            raise

    def get_all_products(self, session=None) -> 'List[Product]':
        """Get all products with ingredients and sales eager loaded."""
        try:
            log_debug("Fetching all active products with relationships")
            
            close_session = False
            if session is None:
                session = self.get_session()
                close_session = True
            try:
                products = Product.active_only(session.query(Product)).options(
                    joinedload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
                    joinedload(Product.sales),
                ).all()
                
                #log_debug(f"Retrieved {len(products)} active products")
                return products
            except Exception as e:
                log_error("Failed to fetch all products", exception=e)
                raise RuntimeError(f"get_all_products failed: {e}") from e
            finally:
                if close_session:
                    session.close()
        except Exception as e:
            log_error("Critical error in get_all_products", exception=e)
            raise

    def get_all_ingredients(self, eager_load=False, session=None) -> 'List[Ingredient]':
        """Get all ingredients, with optional eager loading of products."""
        try:
            #log_debug(f"Fetching all active ingredients (eager_load={eager_load})")
            
            close_session = False
            if session is None:
                session = self.get_session()
                close_session = True
            try:
                query = Ingredient.active_only(session.query(Ingredient))
                if eager_load:
                    query = query.options(
                        joinedload(Ingredient.ingredient_products)
                        .joinedload(ProductIngredient.product)
                        .joinedload(Product.product_ingredients)
                        .joinedload(ProductIngredient.ingredient)
                    )
                ingredients = query.all()
                
                #log_debug(f"Retrieved {len(ingredients)} active ingredients")
                return ingredients
            except Exception as e:
                log_error(f"Failed to fetch all ingredients (eager_load={eager_load})", exception=e)
                raise RuntimeError(f"get_all_ingredients failed (eager_load={eager_load}): {e}") from e
            finally:
                if close_session:
                    session.close()
        except Exception as e:
            log_error("Critical error in get_all_ingredients", exception=e)
            raise


    def get_all_pfand_history(self, session=None) -> 'List[PfandHistory]':
        """Get all pfand history records."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            query = session.query(PfandHistory)
            query = query.options(
                joinedload(PfandHistory.user),
                joinedload(PfandHistory.product)
                    .joinedload(Product.product_ingredients)
                    .joinedload(ProductIngredient.ingredient)
            )
            pfand_history = query.all()
            return pfand_history
        except Exception as e:
            raise RuntimeError(f"get_all_pfand_history failed: {e}") from e
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
            ingredient = Ingredient.active_only(session.query(Ingredient)).filter(Ingredient.ingredient_id == ingredient_id).first()
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
            ingredients = Ingredient.active_only(session.query(Ingredient)).filter(Ingredient.ingredient_id.in_(ingredient_ids)).all()
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
            user = User.active_only(session.query(User)).filter(User.user_id == user_id).first()
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
            product = Product.active_only(session.query(Product)).filter(Product.product_id == product_id).first()
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
            products = Product.active_only(session.query(Product)).options(
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
            products = Product.active_only(session.query(Product)).options(
                joinedload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
                joinedload(Product.sales),
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
                joinedload(ToastRound.sales).joinedload(Sale.consumer),
                joinedload(ToastRound.sales).joinedload(Sale.donator),
                joinedload(ToastRound.sales).joinedload(Sale.product)
                    .joinedload(Product.product_ingredients)
                    .joinedload(ProductIngredient.ingredient),
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
                joinedload(Sale.consumer),
                joinedload(Sale.donator),
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

    def get_pfand_history(self, user_id: int, product_id: int, session=None) -> PfandHistory:
        """Get the pfand history for a user and product."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            pfand_history = session.query(PfandHistory).filter(
                PfandHistory.user_id == user_id,
                PfandHistory.product_id == product_id
            ).all()
            if len(pfand_history) > 1:
                raise ValueError(f"Multiple pfand history records found for user_id={user_id}, product_id={product_id}")
            return pfand_history[0] if pfand_history else None
        except Exception as e:
            raise RuntimeError(f"get_pfand_history failed for user_id={user_id}, product_id={product_id}: {e}") from e
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
            ingredient = Ingredient.active_only(session.query(Ingredient)).filter(Ingredient.name == name).first()
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
            product = Product.active_only(session.query(Product)).filter(Product.name == name).first()
            return product is not None
        except Exception as e:
            raise RuntimeError(f"exists_product_with_name failed for name={name}: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_deleted_users(self, session=None) -> 'List[User]':
        """Get all soft-deleted users."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            users = User.deleted_only(session.query(User)).all()
            return users
        except Exception as e:
            raise RuntimeError(f"get_deleted_users failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_deleted_products(self, session=None) -> 'List[Product]':
        """Get all soft-deleted products."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            products = Product.deleted_only(session.query(Product)).all()
            return products
        except Exception as e:
            raise RuntimeError(f"get_deleted_products failed: {e}") from e
        finally:
            if close_session:
                session.close()

    def get_deleted_ingredients(self, session=None) -> 'List[Ingredient]':
        """Get all soft-deleted ingredients."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        try:
            ingredients = Ingredient.deleted_only(session.query(Ingredient)).all()
            return ingredients
        except Exception as e:
            raise RuntimeError(f"get_deleted_ingredients failed: {e}") from e
        finally:
            if close_session:
                session.close()

# ========== BACKUP FUNCTIONALITY ==========
    
    def create_backup(self, backup_type: str = "manual", description: str = "", created_by: str = "user"):
        """Create a database backup using the backup manager"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            backup_manager = DatabaseBackupManager()
            result = backup_manager.create_backup(
                backup_type=backup_type,
                description=description,
                created_by=created_by
            )
            
            if result['success']:
                print(f"✅ Backup created: {result['message']}")
            else:
                print(f"❌ Backup failed: {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to create backup: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def restore_backup(self, backup_path: str, confirm: bool = False):
        """Restore database from backup"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            if not confirm:
                return {
                    'success': False,
                    'error': 'Restore not confirmed',
                    'message': 'You must set confirm=True to perform restore. This will overwrite your current database!'
                }
            
            backup_manager = DatabaseBackupManager()
            result = backup_manager.restore_backup(backup_path, confirm=True)
            
            if result['success']:
                print(f"✅ Database restored: {result['message']}")
                # Reset database connection after restore
                self._reset_connection()
            else:
                print(f"❌ Restore failed: {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to restore backup: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def list_backups(self):
        """List all available backups"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            backup_manager = DatabaseBackupManager()
            backups = backup_manager.list_backups()
            
            if backups:
                print(f"📦 Found {len(backups)} backup(s):")
                for backup in backups[:10]:  # Show latest 10
                    size_mb = backup['size'] / (1024 * 1024)
                    print(f"  • {backup['filename']} ({backup['type']}) - {size_mb:.1f}MB - {backup['created']}")
            else:
                print("📦 No backups found")
            
            return backups
            
        except Exception as e:
            error_msg = f"Failed to list backups: {e}"
            print(f"❌ {error_msg}")
            return []
    
    def delete_backup(self, backup_filename: str):
        """Delete a specific backup"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            backup_manager = DatabaseBackupManager()
            result = backup_manager.delete_backup(backup_filename)
            
            if result['success']:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to delete backup: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def export_data(self, format: str = "json", include_sensitive: bool = False):
        """Export database data in various formats"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            backup_manager = DatabaseBackupManager()
            result = backup_manager.export_data(format=format, include_sensitive=include_sensitive)
            
            if result['success']:
                print(f"✅ Data exported: {result['message']}")
            else:
                print(f"❌ Export failed: {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to export data: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def cleanup_old_backups(self, daily_keep: int = 7, weekly_keep: int = 4):
        """Clean up old backups based on retention policy"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            backup_manager = DatabaseBackupManager()
            result = backup_manager.cleanup_old_backups(daily_keep=daily_keep, weekly_keep=weekly_keep)
            
            if result['success']:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to cleanup backups: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def _reset_connection(self):
        """Reset database connection after restore"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
            
            # Reset global database state
            from chame_app.database import reset_database
            reset_database()
            
            # Reinitialize session
            self.session = get_session()
            print("🔄 Database connection reset successfully")
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to reset database connection: {e}")

# ========== DELETION METHODS ==========
    
    def check_deletion_dependencies(self, entity_type: str, entity_id: int):
        """Check what depends on an entity before deletion"""
        try:
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            
            if entity_type == "user":
                return deletion_service.check_user_dependencies(entity_id)
            elif entity_type == "product":
                return deletion_service.check_product_dependencies(entity_id)
            elif entity_type == "ingredient":
                return deletion_service.check_ingredient_dependencies(entity_id)
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")
                
        except Exception as e:
            print(f"check_deletion_dependencies error: {e}")
            raise RuntimeError(f"Failed to check dependencies: {e}") from e

    def soft_delete_user(self, user_id: int, deleted_by: str = "api"):
        """Soft delete a user (marks as deleted, preserves data)"""
        try:
            log_info(f"Attempting to soft delete user {user_id}", {"user_id": user_id, "deleted_by": deleted_by})
            
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.soft_delete_user(user_id, deleted_by_user=deleted_by)
            
            if result['success']:
                log_info(f"Successfully soft deleted user {user_id}", {"user_id": user_id, "result": result})
                return {
                    'success': True,
                    'message': result['message'],
                    'details': result['details']
                }
            else:
                log_error(f"Failed to soft delete user {user_id}: {result['message']}", {"user_id": user_id, "result": result})
                raise RuntimeError(result['message'])
                
        except Exception as e:
            log_error(f"Soft delete user {user_id} error", {"user_id": user_id, "deleted_by": deleted_by}, exception=e)
            print(f"soft_delete_user error: {e}")
            raise RuntimeError(f"Failed to soft delete user: {e}") from e

    def soft_delete_product(self, product_id: int, deleted_by: str = "api"):
        """Soft delete a product (marks as deleted, preserves data)"""
        try:
            log_info(f"Attempting to soft delete product {product_id}", {"product_id": product_id, "deleted_by": deleted_by})
            
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.soft_delete_product(product_id, deleted_by_user=deleted_by)
            
            if result['success']:
                log_info(f"Successfully soft deleted product {product_id}", {"product_id": product_id, "result": result})
                return {
                    'success': True,
                    'message': result['message'],
                    'details': result['details']
                }
            else:
                log_error(f"Failed to soft delete product {product_id}: {result['message']}", {"product_id": product_id, "result": result})
                raise RuntimeError(result['message'])
                
        except Exception as e:
            log_error(f"Soft delete product {product_id} error", {"product_id": product_id, "deleted_by": deleted_by}, exception=e)
            print(f"soft_delete_product error: {e}")
            raise RuntimeError(f"Failed to soft delete product: {e}") from e

    def soft_delete_ingredient(self, ingredient_id: int, deleted_by: str = "api"):
        """Soft delete an ingredient (marks as deleted, preserves data)"""
        try:
            log_info(f"Attempting to soft delete ingredient {ingredient_id}", {"ingredient_id": ingredient_id, "deleted_by": deleted_by})
            
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.soft_delete_ingredient(ingredient_id, deleted_by_user=deleted_by)
            
            if result['success']:
                log_info(f"Successfully soft deleted ingredient {ingredient_id}", {"ingredient_id": ingredient_id, "result": result})
                return {
                    'success': True,
                    'message': result['message'],
                    'details': result['details']
                }
            else:
                log_error(f"Failed to soft delete ingredient {ingredient_id}: {result['message']}", {"ingredient_id": ingredient_id, "result": result})
                raise RuntimeError(result['message'])
                
        except Exception as e:
            log_error(f"Soft delete ingredient {ingredient_id} error", {"ingredient_id": ingredient_id, "deleted_by": deleted_by}, exception=e)
            print(f"soft_delete_ingredient error: {e}")
            raise RuntimeError(f"Failed to soft delete ingredient: {e}") from e

    def restore_user(self, user_id: int):
        """Restore a soft-deleted user"""
        try:
            log_info(f"Attempting to restore user {user_id}", {"user_id": user_id})
            
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.restore_user(user_id)
            
            if result['success']:
                log_info(f"Successfully restored user {user_id}", {"user_id": user_id, "result": result})
                return {
                    'success': True,
                    'message': result['message']
                }
            else:
                log_error(f"Failed to restore user {user_id}: {result['message']}", {"user_id": user_id, "result": result})
                raise RuntimeError(result['message'])
                
        except Exception as e:
            log_error(f"Restore user {user_id} error", {"user_id": user_id}, exception=e)
            print(f"restore_user error: {e}")
            raise RuntimeError(f"Failed to restore user: {e}") from e

    def restore_product(self, product_id: int):
        """Restore a soft-deleted product"""
        try:
            log_info(f"Attempting to restore product {product_id}", {"product_id": product_id})
            
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.restore_product(product_id)
            
            if result['success']:
                log_info(f"Successfully restored product {product_id}", {"product_id": product_id, "result": result})
                return {
                    'success': True,
                    'message': result['message']
                }
            else:
                log_error(f"Failed to restore product {product_id}: {result['message']}", {"product_id": product_id, "result": result})
                raise RuntimeError(result['message'])
                
        except Exception as e:
            log_error(f"Restore product {product_id} error", {"product_id": product_id}, exception=e)
            print(f"restore_product error: {e}")
            raise RuntimeError(f"Failed to restore product: {e}") from e

    def restore_ingredient(self, ingredient_id: int):
        """Restore a soft-deleted ingredient"""
        try:
            log_info(f"Attempting to restore ingredient {ingredient_id}", {"ingredient_id": ingredient_id})
            
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.restore_ingredient(ingredient_id)
            
            if result['success']:
                log_info(f"Successfully restored ingredient {ingredient_id}", {"ingredient_id": ingredient_id, "result": result})
                return {
                    'success': True,
                    'message': result['message']
                }
            else:
                log_error(f"Failed to restore ingredient {ingredient_id}: {result['message']}", {"ingredient_id": ingredient_id, "result": result})
                raise RuntimeError(result['message'])
                
        except Exception as e:
            log_error(f"Restore ingredient {ingredient_id} error", {"ingredient_id": ingredient_id}, exception=e)
            print(f"restore_ingredient error: {e}")
            raise RuntimeError(f"Failed to restore ingredient: {e}") from e

    def delete_sale_record(self, sale_id: int, admin_user_id: int):
        """Delete a specific sale record (admin only)"""
        try:
            with self.get_session() as session:
                # Check if sale exists
                sale = session.execute(text(
                    "SELECT * FROM sales WHERE sale_id = :sale_id"
                ), {"sale_id": sale_id}).fetchone()
                
                if not sale:
                    raise ValueError("Sale record not found")
                
                # Delete the sale
                deleted_count = session.execute(text(
                    "DELETE FROM sales WHERE sale_id = :sale_id"
                ), {"sale_id": sale_id}).rowcount
                
                if deleted_count > 0:
                    session.commit()
                    return {
                        'success': True,
                        'message': f'Sale record {sale_id} deleted successfully',
                        'deleted_by': admin_user_id
                    }
                else:
                    raise RuntimeError("Failed to delete sale record")
                    
        except Exception as e:
            print(f"delete_sale_record error: {e}")
            raise RuntimeError(f"Failed to delete sale record: {e}") from e

    def safe_delete_user(self, user_id: int, force: bool = False):
        """Safely delete a user with dependency checks"""
        try:
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.safe_delete_user(user_id, force=force)
            
            if result['success']:
                return {
                    'success': True,
                    'message': result['message'],
                    'details': result['details']
                }
            else:
                raise RuntimeError(result['message'])
                
        except Exception as e:
            print(f"safe_delete_user error: {e}")
            raise RuntimeError(f"Failed to delete user: {e}") from e

    def safe_delete_product(self, product_id: int, force: bool = False):
        """Safely delete a product with dependency checks"""
        try:
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.safe_delete_product(product_id, force=force)
            
            if result['success']:
                return {
                    'success': True,
                    'message': result['message'],
                    'details': result['details']
                }
            else:
                raise RuntimeError(result['message'])
                
        except Exception as e:
            print(f"safe_delete_product error: {e}")
            raise RuntimeError(f"Failed to delete product: {e}") from e

    def safe_delete_ingredient(self, ingredient_id: int, force: bool = False):
        """Safely delete an ingredient with dependency checks"""
        try:
            from services.deletion_service import DeletionService
            
            deletion_service = DeletionService(self.get_session())
            result = deletion_service.safe_delete_ingredient(ingredient_id, force=force)
            
            if result['success']:
                return {
                    'success': True,
                    'message': result['message'],
                    'details': result['details']
                }
            else:
                raise RuntimeError(result['message'])
                
        except Exception as e:
            print(f"safe_delete_ingredient error: {e}")
            raise RuntimeError(f"Failed to delete ingredient: {e}") from e

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

# Initialize database instance when module is imported
# database = Database()