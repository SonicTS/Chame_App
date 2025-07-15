# admin_api.py
# Bare Python functions for business logic, callable from other Python code or via FFI for Flutter integration.

from chame_app.database_instance import Database
from chame_app.simple_migrations import SimpleMigrations
import logging
from typing import Dict, List
import traceback

database = None

def run_migrations():
    """Run database migrations - uses simple migrations"""
    print("DEBUG: Running migrations with SimpleMigrations")
    run_simple_migrations()

def run_simple_migrations():
    """Run simple migrations for mobile/Chaquopy environments"""
    print("📦 [SimpleMigrations] Starting simple database migrations")
    try:
        # Get the database engine
        from chame_app.database import _engine
        if _engine is None:
            print("❌ [SimpleMigrations] Database engine not initialized")
            return
        
        migrations = SimpleMigrations(_engine)
        migrations.run_migrations()
        print("✅ [SimpleMigrations] Simple migrations completed successfully")
    except Exception:
        print("❌ [SimpleMigrations] Simple migrations failed")
        traceback.print_exc()

def create_database(apply_migration: bool = True) -> Database:
    global database
    print("DEBUG: create_database called with apply_migration:", apply_migration)
    if database is None:
        print("DEBUG: Creating new Database instance")
        database = Database(apply_migration)
        logging.info("Database instance created and migrations run.")
    else:
        logging.warning("Database instance already exists.")
    return database

def login(username, password):
    if not username:
        raise ValueError("Username and password cannot be empty")
    user = database.get_user_by_username(username)
    if not password:
        password = ""
    if user and user.verify_password(password):
        return user.to_dict(True)
    else:
        raise ValueError("Invalid username or password")

def change_password(user_id, old_password, new_password):
    if not user_id or not old_password or not new_password:
        raise ValueError("Invalid input")
    return database.change_password(user_id, old_password, new_password)



# User management
def add_user(name, balance, role, password=""):
    print("DEBUG: add_user called with:", name, balance, role, password)
    if not name or balance is None or not role:
        raise ValueError("Invalid input")
    if role.lower() in ["admin", "wirt"] and password:
        if role.lower() == "admin" and len(password) < 8:
            raise ValueError("Admin password must be at least 8 characters long")
        if role.lower() == "wirt" and len(password) < 4:    
            raise ValueError("Wirt password must be at least 4 characters long")
    elif role.lower() in ["admin", "wirt"] and not password:
        raise ValueError("Wirt or admin role requires a password")
    if role.lower() not in ["user", "admin", "wirt"]:
        raise ValueError("Role must be 'user', 'admin', or 'wirt'")
    return database.add_user(username=name, password=password, balance=balance, role=role.lower())

def withdraw(user_id, amount):
    if not user_id or not amount:
        raise ValueError("Invalid input")
    return database.withdraw_cash(user_id=user_id, amount=amount)

def deposit(user_id, amount):
    if not user_id or not amount:
        raise ValueError("Invalid input")
    return database.deposit_cash(user_id=user_id, amount=amount)

# Product management
def add_product(name, category, price, ingredients_ids, quantities, toaster_space):
    if not name or not category or not price or not ingredients_ids or not quantities:
        raise ValueError("Invalid input")
    ingredients = database.get_ingredients_by_ids(ingredients_ids)
    ingredient_quantity_pairs = list(zip(ingredients, quantities))
    return database.add_product(name=name, ingredients=ingredient_quantity_pairs, price_per_unit=price, category=category, toaster_space=toaster_space)

# Ingredient management
def add_ingredient(name, price_per_package, stock_quantity, number_ingredients, pfand):
    print("DEBUG: add_ingredient called with:", name, price_per_package, stock_quantity, number_ingredients, pfand)
    if not name or not price_per_package or not number_ingredients:
        print("DEBUG: Invalid input for add_ingredient")
        raise ValueError("Invalid input")
    if not pfand:
        pfand = 0.0
    if not isinstance(stock_quantity, int) or stock_quantity < 0:
        stock_quantity = 0  # Default to 0 if invalid
    return database.add_ingredient(name=name, price_per_package=price_per_package, stock_quantity=stock_quantity, number_ingredients=number_ingredients, pfand=pfand)

def submit_pfand_return(user_id, product_list):
    print("DEBUG: submit_pfand_return called with user_id:", user_id, "and product_list:", product_list)
    if not user_id or not product_list:
        raise ValueError("Invalid input")
    if not isinstance(product_list, list):
        raise ValueError("Product list must be a list")
    
    return database.return_deposit(user_id=user_id, product_quantity_list=product_list)

def update_stock(ingredient_id: int, amount: int, comment: str = ""):
    print("DEBUG: update_stock called with ingredient_id:", ingredient_id, "amount:", amount, "comment:", comment)
    if not ingredient_id or amount is None:
        raise ValueError("Invalid input")
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    
    return database.update_stock(ingredient_id=ingredient_id, amount=amount, comment=comment)

def get_stock_history(ingredient_id: int):
    print("DEBUG: get_stock_history called with ingredient_id:", ingredient_id)
    if not ingredient_id:
        raise ValueError("Invalid input")
    
    stock_history = database.get_stock_history(ingredient_id=ingredient_id)
    if not stock_history:
        print("DEBUG: No stock history found for ingredient_id:", ingredient_id)
        return []
    
    return [sh.to_dict(include_ingredient=True) for sh in stock_history]

def get_all_stock_history():
    print("DEBUG: get_all_stock_history called")
    stock_history = database.get_all_stock_history()
    if not stock_history:
        print("DEBUG: No stock history found")
        return []
    
    return [sh.to_dict(include_ingredient=True) for sh in stock_history]

def restock_ingredients(_list: List[Dict[int, int]]):
    if not _list or not isinstance(_list, list):
        raise ValueError("Invalid input")
    print("DEBUG: restock_ingredients called with:", _list)
    return database.restock_ingredients(_list=_list)


def restock_ingredient(ingredient_id, quantity):
    if not ingredient_id or not quantity:
        raise ValueError("Invalid input")
    return database.stock_ingredient(ingredient_id=ingredient_id, quantity=quantity)

def make_multiple_purchases(item_list: List[Dict[str, int]]):
    if not item_list or not isinstance(item_list, list):
        raise ValueError("Invalid input")
    if not all(isinstance(item, dict) and 'product_id' in item and 'quantity' in item and 'consumer_id' in item for item in item_list):
        raise ValueError("Each item must be a dict with 'product_id' and 'quantity' and 'consumer_id")
    return database.make_multiple_purchases(item_list=item_list)

# Purchase logic
def make_purchase(consumer_id, product_id, quantity, donator_id=None):
    if not consumer_id or not product_id or not quantity:
        raise ValueError("Invalid input")
    return database.make_purchase(consumer_id=consumer_id, donator_id=donator_id, product_id=product_id, quantity=quantity)

def change_user_role(user_id, new_role):
    if not user_id or not new_role:
        raise ValueError("Invalid input")
    if new_role.lower() not in ["user", "admin", "wirt"]:
        raise ValueError("Role must be 'user', 'admin', or 'wirt'")
    return database.change_user_role(user_id=user_id, new_role=new_role.lower())

# Toast round logic
def add_toast_round(product_ids, consumer_selections, donator_selections):
    print("DEBUG: add_toast_round called with product_ids:", product_ids, "and user_selections:", consumer_selections, "and donator_selections:", donator_selections)
    if not product_ids or not consumer_selections or not donator_selections:
        raise ValueError("Product IDs and user selections cannot be empty.")
    if len(product_ids) != len(consumer_selections) or len(product_ids) != len(donator_selections):
        raise ValueError("Mismatch between product IDs and user selections.")
    product_user_pairs = list(zip(product_ids, consumer_selections, donator_selections))
    return database.add_toast_round(product_user_list=product_user_pairs)

# Bank logic
def bank_withdraw(amount, description):
    if not amount:
        raise ValueError("Invalid input")
    return database.withdraw_cash_from_bank(amount=amount, description=description)

# Data fetchers
def get_all_users():
    return [user.to_dict(True) for user in database.get_all_users()]

def get_all_products():
    return [product.to_dict(True, True, True, True) for product in database.get_all_products()]

def get_all_ingredients():
    result = [ingredient.to_dict(True) for ingredient in database.get_all_ingredients(eager_load=True)]
    # print("DEBUG get_all_ingredients result:", result)
    # print("DEBUG types:", [type(x) for x in result])
    if len(result) == 0:
        print("DEBUG: No ingredients found in the database.")
        return None
    return result

def get_all_sales():
    return [sale.to_dict(True, True, True) for sale in database.get_all_sales()]

def get_all_toast_products():
    return [tp.to_dict(True, True, True, True) for tp in database.get_all_toast_products()]

def get_all_toast_rounds():
    return [tr.to_dict(True, True) for tr in database.get_all_toast_rounds()]

def get_all_raw_products():
    """Get all products without eager loading ingredients or sales"""
    return [product.to_dict(True, True, True, True) for product in database.get_all_products_by_category('raw')]

def get_filtered_transaction(user_id="all", tx_type="all"):
    return [tx.to_dict(True) for tx in database.get_filtered_transaction(user_id=user_id, tx_type=tx_type)]

def get_bank():
    return database.get_bank().to_dict() if database.get_bank() else None

def get_bank_transaction():
    return [bt.to_dict() for bt in database.get_bank_transaction()]

def get_pfand_history():
    pfand_history = database.get_all_pfand_history()
    if not pfand_history:
        return []
    return [ph.to_dict(include_user=True, include_product=True) for ph in pfand_history]

# ========== BACKUP FUNCTIONS ==========

def create_backup(backup_type="manual", description="", created_by="api"):
    """Create a database backup"""
    try:
        result = database.create_backup(
            backup_type=backup_type,
            description=description,
            created_by=created_by
        )
        
        if result['success']:
            return {
                'success': True,
                'backup_path': result['backup_path'],
                'metadata': result['metadata'],
                'message': result['message']
            }
        else:
            raise RuntimeError(result['message'])
            
    except Exception as e:
        print(f"create_backup error: {e}")
        raise RuntimeError(f"Failed to create backup: {e}") from e

def restore_backup(backup_path, confirm=False):
    """Restore database from backup"""
    try:
        if not confirm:
            raise ValueError("You must set confirm=True to perform restore. This will overwrite your current database!")
        
        result = database.restore_backup(backup_path, confirm=True)
        
        if result['success']:
            return {
                'success': True,
                'restored_from': result['restored_from'],
                'database_path': result['database_path'],
                'message': result['message']
            }
        else:
            raise RuntimeError(result['message'])
            
    except Exception as e:
        print(f"restore_backup error: {e}")
        raise RuntimeError(f"Failed to restore backup: {e}") from e

def list_backups():
    """List all available backups"""
    try:
        backups = database.list_backups()
        return backups
        
    except Exception as e:
        print(f"list_backups error: {e}")
        raise RuntimeError(f"Failed to list backups: {e}") from e

def delete_backup(backup_filename):
    """Delete a specific backup"""
    try:
        result = database.delete_backup(backup_filename)
        
        if result['success']:
            return {
                'success': True,
                'message': result['message']
            }
        else:
            raise RuntimeError(result['message'])
            
    except Exception as e:
        print(f"delete_backup error: {e}")
        raise RuntimeError(f"Failed to delete backup: {e}") from e

# ========== DELETION FUNCTIONS ==========

def check_deletion_dependencies(entity_type, entity_id):
    """Check what depends on an entity before deletion"""
    return database.check_deletion_dependencies(entity_type, entity_id)

def soft_delete_user(user_id, deleted_by="api"):
    """Soft delete a user (marks as deleted, preserves data)"""
    return database.soft_delete_user(user_id, deleted_by)

def soft_delete_product(product_id, deleted_by="api"):
    """Soft delete a product (marks as deleted, preserves data)"""
    return database.soft_delete_product(product_id, deleted_by)

def soft_delete_ingredient(ingredient_id, deleted_by="api"):
    """Soft delete an ingredient (marks as deleted, preserves data)"""
    return database.soft_delete_ingredient(ingredient_id, deleted_by)

def restore_user(user_id):
    """Restore a soft-deleted user - no dependencies to check for users"""
    try:
        from models.user_table import User
        
        # Check if user exists and is soft-deleted
        user = database.session.query(User).filter(
            User.user_id == user_id,
            User.deleted_at.isnot(None)
        ).first()
        
        if not user:
            return "User not found or not deleted"
        
        # Users typically don't have restoration dependencies
        # (sales/transactions are preserved history, not blocking dependencies)
        return database.restore_user(user_id)
        
    except Exception as e:
        print(f"Error in restore_user: {e}")
        return f"Failed to restore user: {str(e)}"

def restore_product(product_id):
    """Restore a soft-deleted product - but only if all its ingredients are active"""
    try:
        # Check if product exists and is soft-deleted
        from models.product_table import Product
        
        product = database.session.query(Product).filter(
            Product.product_id == product_id,
            Product.is_deleted.is_(True)
        ).first()
        
        if not product:
            raise RuntimeError("Product not found or not deleted")
        
        # Check if any required ingredients are still soft-deleted
        from models.product_ingredient_table import ProductIngredient
        from models.ingredient import Ingredient
        
        product_ingredients = database.session.query(ProductIngredient).filter(
            ProductIngredient.product_id == product_id
        ).all()
        
        deleted_ingredients = []
        for pi in product_ingredients:
            ingredient = database.session.query(Ingredient).filter(
                Ingredient.ingredient_id == pi.ingredient_id,
                Ingredient.is_deleted.is_(True)
            ).first()
            
            if ingredient:
                deleted_ingredients.append(ingredient.name)
        
        if deleted_ingredients:
            ingredient_list = ", ".join(deleted_ingredients)
            raise RuntimeError(f"Cannot restore product '{product.name}' because required ingredients are still deleted: {ingredient_list}. Restore these ingredients first.")
        
        # All ingredients are active, proceed with restoration
        return database.restore_product(product_id)
        
    except Exception as e:
        raise RuntimeError(str(e)) from e

def restore_ingredient(ingredient_id):
    """Restore a soft-deleted ingredient"""
    return database.restore_ingredient(ingredient_id)

def get_deleted_users():
    """Get all soft-deleted users"""
    try:
        users = database.get_deleted_users()
        return [{
            'user_id': user.user_id,
            'name': user.name,
            'balance': float(user.balance),
            'role': user.role,
            'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None,
            'deleted_by': user.deleted_by
        } for user in users]
    except Exception as e:
        raise RuntimeError(f"Failed to get deleted users: {e}") from e

def get_deleted_products():
    """Get all soft-deleted products"""
    try:
        products = database.get_deleted_products()
        return [{
            'product_id': product.product_id,
            'name': product.name,
            'category': product.category,
            'price_per_unit': float(product.price_per_unit),
            'cost_per_unit': float(product.cost_per_unit),
            'profit_per_unit': float(product.profit_per_unit),
            'stock_quantity': product.stock_quantity,
            'toaster_space': product.toaster_space,
            'deleted_at': product.deleted_at.isoformat() if product.deleted_at else None,
            'deleted_by': product.deleted_by
        } for product in products]
    except Exception as e:
        raise RuntimeError(f"Failed to get deleted products: {e}") from e

def get_deleted_ingredients():
    """Get all soft-deleted ingredients"""
    try:
        ingredients = database.get_deleted_ingredients()
        return [{
            'ingredient_id': ingredient.ingredient_id,
            'name': ingredient.name,
            'price_per_package': float(ingredient.price_per_package),
            'number_of_units': ingredient.number_of_units,
            'price_per_unit': float(ingredient.price_per_unit),
            'stock_quantity': ingredient.stock_quantity,
            'pfand': float(ingredient.pfand),
            'deleted_at': ingredient.deleted_at.isoformat() if ingredient.deleted_at else None,
            'deleted_by': ingredient.deleted_by
        } for ingredient in ingredients]
    except Exception as e:
        raise RuntimeError(f"Failed to get deleted ingredients: {e}") from e
    
def safe_delete_user(user_id, force):
    """Safely delete a user (hard delete if no dependencies)"""
    print("DEBUG: safe_delete_user called with:", user_id, "and force:", force)
    if not user_id:
        raise ValueError("User ID cannot be empty")
    return database.safe_delete_user(user_id, force)

def safe_delete_product(product_id, force):
    """Safely delete a product (hard delete if no dependencies)"""
    print("DEBUG: safe_delete_product called with:", product_id, "and force:", force)
    if not product_id:
        raise ValueError("Product ID cannot be empty")
    return database.safe_delete_product(product_id, force)

def safe_delete_ingredient(ingredient_id, force):
    """Safely delete an ingredient (hard delete if no dependencies)"""
    print("DEBUG: safe_delete_ingredient called with:", ingredient_id, "and force:", force)
    if not ingredient_id:
        raise ValueError("Ingredient ID cannot be empty")
    return database.safe_delete_ingredient(ingredient_id, force)

def get_deletion_impact_analysis(entity_type, entity_id):
    """Get impact analysis for deletion - what will be affected"""
    try:
        from services.flexible_deletion_service import FlexibleDeletionService
        deletion_service = FlexibleDeletionService(database.session)
        plan = deletion_service.analyze_deletion_impact(entity_type, entity_id)
        
        # Convert the plan to a serializable format
        result = {
            'can_proceed': True,
            'dependencies': [],
            'warnings': plan.warnings,
            'errors': plan.errors
        }
        
        for dep in plan.dependencies:
            dep_data = {
                'relationship_name': dep.relationship_name,
                'table_name': dep.table_name,
                'count': dep.count,
                'is_critical': dep.is_critical,
                'description': dep.description,
                'available_actions': [action.value for action in dep.available_actions],
                'default_action': dep.default_action.value if dep.default_action else None,
                'sample_records': dep.sample_records
            }
            result['dependencies'].append(dep_data)
        
        return result
    except Exception as e:
        print(f"Error in get_deletion_impact_analysis: {e}")
        return {
            'can_proceed': False,
            'dependencies': [],
            'warnings': [],
            'errors': [str(e)]
        }

def enhanced_delete_user(user_id, deleted_by_user="admin", hard_delete=False, cascade_choices=None):
    """
    Enhanced deletion with user-configurable cascade options.
    
    Args:
        user_id: ID of user to delete
        deleted_by_user: Who is performing the deletion
        hard_delete: Whether to hard delete or soft delete
        cascade_choices: Dict mapping dependency relationship_name to action ("hard", "soft", "nullify")
    """
    try:
        from services.flexible_deletion_service import FlexibleDeletionService, CascadeAction
        deletion_service = FlexibleDeletionService(database.session)
        plan = deletion_service.analyze_deletion_impact('user', user_id)
        plan.deletion_type = 'hard' if hard_delete else 'soft'
        
        # Apply user choices for cascade actions
        if cascade_choices:
            try:
                # Handle different types of input (dict, HashMap from Java/Kotlin, etc.)
                choices_dict = {}
                if hasattr(cascade_choices, 'items'):
                    # Standard dict or dict-like object
                    choices_dict = dict(cascade_choices.items())
                elif hasattr(cascade_choices, '__iter__'):
                    # Handle iterables like lists of tuples
                    choices_dict = dict(cascade_choices)
                else:
                    # Try to convert to dict directly
                    choices_dict = dict(cascade_choices)
                
                # Process the choices
                for relationship_name, action_str in choices_dict.items():
                    try:
                        action = CascadeAction(action_str)
                        plan.user_choices[relationship_name] = action
                    except ValueError:
                        plan.warnings.append(f"Unknown cascade action: {action_str}")
            except Exception as convert_error:
                print(f"Warning: Failed to process cascade_choices: {convert_error}")
                print(f"Type of cascade_choices: {type(cascade_choices)}")
                # Try to inspect the object
                try:
                    print(f"cascade_choices attributes: {dir(cascade_choices)}")
                except Exception:
                    pass
                    
        # Enforce soft delete reversibility
        if not hard_delete:
            for dep in plan.dependencies:
                if dep.relationship_name not in plan.user_choices:
                    # Default: soft delete or nullify+broken for soft delete
                    if CascadeAction.soft_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.soft_delete
                    elif CascadeAction.nullify in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.nullify
                        
        # For hard delete, allow more aggressive actions
        if hard_delete:
            for dep in plan.dependencies:
                if dep.relationship_name not in plan.user_choices:
                    if CascadeAction.hard_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.hard_delete
                    elif CascadeAction.soft_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.soft_delete
                    elif CascadeAction.nullify in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.nullify
        
        # Execute the deletion
        result = deletion_service.execute_deletion_plan(plan, deleted_by_user)
        return result
    except Exception as e:
        print(f"Error in enhanced_delete_user: {e}")
        return {"success": False, "message": str(e)}

def enhanced_delete_product(product_id, deleted_by_user="admin", hard_delete=False, cascade_choices=None):
    """Enhanced deletion with user-configurable cascade options (see enhanced_delete_user for logic)"""
    try:
        from services.flexible_deletion_service import FlexibleDeletionService, CascadeAction
        deletion_service = FlexibleDeletionService(database.session)
        plan = deletion_service.analyze_deletion_impact('product', product_id)
        plan.deletion_type = 'hard' if hard_delete else 'soft'
        
        if cascade_choices:
            try:
                # Handle different types of input (dict, HashMap from Java/Kotlin, etc.)
                choices_dict = {}
                if hasattr(cascade_choices, 'items'):
                    # Standard dict or dict-like object
                    choices_dict = dict(cascade_choices.items())
                elif hasattr(cascade_choices, '__iter__'):
                    # Handle iterables like lists of tuples
                    choices_dict = dict(cascade_choices)
                else:
                    # Try to convert to dict directly
                    choices_dict = dict(cascade_choices)
                
                # Process the choices
                for relationship_name, action_str in choices_dict.items():
                    try:
                        action = CascadeAction(action_str)
                        plan.user_choices[relationship_name] = action
                    except ValueError:
                        plan.warnings.append(f"Unknown cascade action: {action_str}")
            except Exception as convert_error:
                print(f"Warning: Failed to process cascade_choices: {convert_error}")
                print(f"Type of cascade_choices: {type(cascade_choices)}")
                # Try to inspect the object
                try:
                    print(f"cascade_choices attributes: {dir(cascade_choices)}")
                except Exception:
                    pass
                    
        # Enforce soft delete reversibility
        if not hard_delete:
            for dep in plan.dependencies:
                if dep.relationship_name not in plan.user_choices:
                    if CascadeAction.soft_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.soft_delete
                    elif CascadeAction.nullify in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.nullify
                        
        # For hard delete, allow more aggressive actions
        if hard_delete:
            for dep in plan.dependencies:
                if dep.relationship_name not in plan.user_choices:
                    if CascadeAction.hard_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.hard_delete
                    elif CascadeAction.soft_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.soft_delete
                    elif CascadeAction.nullify in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.nullify
        
        result = deletion_service.execute_deletion_plan(plan, deleted_by_user)
        return result
    except Exception as e:
        print(f"Error in enhanced_delete_product: {e}")
        return {"success": False, "message": str(e)}

def enhanced_delete_ingredient(ingredient_id, deleted_by_user="admin", hard_delete=False, cascade_choices=None):
    """Enhanced deletion with user-configurable cascade options (see enhanced_delete_user for logic)"""
    try:
        from services.flexible_deletion_service import FlexibleDeletionService, CascadeAction
        deletion_service = FlexibleDeletionService(database.session)
        plan = deletion_service.analyze_deletion_impact('ingredient', ingredient_id)
        plan.deletion_type = 'hard' if hard_delete else 'soft'
        
        if cascade_choices:
            try:
                # Handle different types of input (dict, HashMap from Java/Kotlin, etc.)
                choices_dict = {}
                if hasattr(cascade_choices, 'items'):
                    # Standard dict or dict-like object
                    choices_dict = dict(cascade_choices.items())
                elif hasattr(cascade_choices, '__iter__'):
                    # Handle iterables like lists of tuples
                    choices_dict = dict(cascade_choices)
                else:
                    # Try to convert to dict directly
                    choices_dict = dict(cascade_choices)
                
                # Process the choices
                for relationship_name, action_str in choices_dict.items():
                    try:
                        action = CascadeAction(action_str)
                        plan.user_choices[relationship_name] = action
                    except ValueError:
                        plan.warnings.append(f"Unknown cascade action: {action_str}")
            except Exception as convert_error:
                print(f"Warning: Failed to process cascade_choices: {convert_error}")
                print(f"Type of cascade_choices: {type(cascade_choices)}")
                # Try to inspect the object
                try:
                    print(f"cascade_choices attributes: {dir(cascade_choices)}")
                except Exception:
                    pass
                    
        # Enforce soft delete reversibility
        if not hard_delete:
            for dep in plan.dependencies:
                if dep.relationship_name not in plan.user_choices:
                    if CascadeAction.soft_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.soft_delete
                    elif CascadeAction.nullify in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.nullify
                        
        # For hard delete, allow more aggressive actions
        if hard_delete:
            for dep in plan.dependencies:
                if dep.relationship_name not in plan.user_choices:
                    if CascadeAction.hard_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.hard_delete
                    elif CascadeAction.soft_delete in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.soft_delete
                    elif CascadeAction.nullify in dep.available_actions:
                        plan.user_choices[dep.relationship_name] = CascadeAction.nullify
        
        result = deletion_service.execute_deletion_plan(plan, deleted_by_user)
        return result
    except Exception as e:
        print(f"Error in enhanced_delete_ingredient: {e}")
        return {"success": False, "message": str(e)}

def analyze_deletion_impact(entity_type, entity_id):
    """
    Analyze what would be impacted by deleting an entity
    Returns information about whether hard or soft deletion will be used
    """
    try:
        import json
        from services.flexible_deletion_service import FlexibleDeletionService
        
        deletion_service = FlexibleDeletionService(database.session)
        plan = deletion_service.analyze_deletion_impact(entity_type, entity_id)
        
        result = {
            'entity_type': plan.entity_type,
            'entity_id': plan.entity_id,
            'entity_name': plan.entity_name,
            'deletion_type': plan.deletion_type,  # 'hard' or 'soft'
            'can_proceed': plan.can_proceed,
            'warnings': plan.warnings,
            'errors': plan.errors,
            'dependencies': [
                {
                    'table_name': dep.table_name,
                    'relationship_name': dep.relationship_name,
                    'count': dep.count,
                    'sample_records': dep.sample_records[:3],  # Limit samples for API
                    'description': dep.description,
                    'is_critical': dep.is_critical
                }
                for dep in plan.dependencies
            ]
        }
        return json.dumps(result)
    except Exception as e:
        print(f"analyze_deletion_impact error: {e}")
        raise RuntimeError(f"Failed to analyze deletion impact: {e}") from e

def execute_deletion(entity_type, entity_id, deleted_by="api"):
    """
    Execute deletion with simplified logic:
    - Hard delete if no dependencies
    - Soft delete if dependencies exist
    - For ingredients: soft delete cascades to products
    """
    try:
        import json
        from services.flexible_deletion_service import FlexibleDeletionService
        
        deletion_service = FlexibleDeletionService(database.session)
        
        # First analyze the impact
        plan = deletion_service.analyze_deletion_impact(entity_type, entity_id)
        
        if not plan.can_proceed:
            result = {
                'success': False,
                'message': f"Cannot delete {entity_type}: {'; '.join(plan.errors)}",
                'deletion_type': plan.deletion_type,
                'affected_records': {}
            }
            return json.dumps(result)
        
        # Execute the deletion
        result = deletion_service.execute_deletion_plan(plan, deleted_by)
        result['deletion_type'] = plan.deletion_type  # Add deletion type to result
        
        return json.dumps(result)
        
    except Exception as e:
        print(f"execute_deletion error: {e}")
        raise RuntimeError(f"Failed to execute deletion: {e}") from e

def test_firebase_logging():
    """Test Firebase logging functionality from Python backend"""
    try:
        from utils.firebase_logger import log_info, log_warn, log_error, test_firebase_bridge, diagnose_release_issues, test_bridge_from_python
        
        print("🧪 [PYTHON-TEST] Starting Firebase logging test from Python backend...")
        
        # Run diagnostic first
        print("🔍 [PYTHON-TEST] Running Firebase bridge diagnostics...")
        diagnose_release_issues()
        
        # Test different log levels
        print("📝 [PYTHON-TEST] Testing different log levels...")
        log_info("🧪 Python Firebase test - INFO level", {
            "test_type": "python_backend_test",
            "log_level": "info",
            "timestamp": str(__import__('datetime').datetime.now()),
            "source": "admin_api.test_firebase_logging"
        })
        
        log_warn("🧪 Python Firebase test - WARNING level", {
            "test_type": "python_backend_test", 
            "log_level": "warning",
            "timestamp": str(__import__('datetime').datetime.now()),
            "source": "admin_api.test_firebase_logging"
        })
        
        log_error("🧪 Python Firebase test - ERROR level", {
            "test_type": "python_backend_test",
            "log_level": "error", 
            "timestamp": str(__import__('datetime').datetime.now()),
            "source": "admin_api.test_firebase_logging"
        })
        
        # Test Python to Flutter bridge
        print("🔄 [PYTHON-TEST] Testing Python to Flutter bridge...")
        bridge_success = test_bridge_from_python()
        
        # Run comprehensive test
        print("🚀 [PYTHON-TEST] Running comprehensive Firebase bridge test...")
        test_firebase_bridge()
        
        print("✅ [PYTHON-TEST] Firebase logging test completed successfully")
        return {
            "success": True, 
            "message": "Firebase logging test completed",
            "bridge_test": bridge_success
        }
        
    except Exception as e:
        print(f"❌ [PYTHON-TEST] Firebase logging test failed: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e), "message": f"Firebase logging test failed: {e}"}