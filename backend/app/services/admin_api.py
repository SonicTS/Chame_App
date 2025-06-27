# admin_api.py
# Bare Python functions for business logic, callable from other Python code or via FFI for Flutter integration.


from models.ingredient import Ingredient
from chame_app.database_instance import Database
from chame_app.simple_migrations import SimpleMigrations
import logging
from typing import Dict, List, Optional
import os
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
    if database is None:
        database = Database(apply_migration)
        logging.info("Database instance created and migrations run.")
    else:
        logging.warning("Database instance already exists.")
    return database

def login(username, password):
    if not username or not password:
        raise ValueError("Username and password cannot be empty")
    user = database.get_user_by_username(username)
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

def restock_ingredients(_list: List[Dict[int, int]]):
    if not _list or not isinstance(_list, list):
        raise ValueError("Invalid input")
    print("DEBUG: restock_ingredients called with:", _list)
    return database.restock_ingredients(_list=_list)


def restock_ingredient(ingredient_id, quantity):
    if not ingredient_id or not quantity:
        raise ValueError("Invalid input")
    return database.stock_ingredient(ingredient_id=ingredient_id, quantity=quantity)

# Purchase logic
def make_purchase(consumer_id, product_id, quantity, donator_id=None):
    if not consumer_id or not product_id or not quantity:
        raise ValueError("Invalid input")
    return database.make_purchase(consumer_id=consumer_id, donator_id=donator_id, product_id=product_id, quantity=quantity)

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
    return [product.to_dict(True, True, True, True, True) for product in database.get_all_products()]

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
    return [tp.to_dict(True, True, True, True, True) for tp in database.get_all_toast_products()]

def get_all_toast_rounds():
    return [tr.to_dict(True, True) for tr in database.get_all_toast_rounds()]

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

def export_data(format="json", include_sensitive=False):
    """Export database data in various formats"""
    try:
        result = database.export_data(format=format, include_sensitive=include_sensitive)
        
        if result['success']:
            return {
                'success': True,
                'export_path': result['export_path'],
                'format': result['format'],
                'message': result['message']
            }
        else:
            raise RuntimeError(result['message'])
            
    except Exception as e:
        print(f"export_data error: {e}")
        raise RuntimeError(f"Failed to export data: {e}") from e

def cleanup_old_backups(daily_keep=7, weekly_keep=4):
    """Clean up old backups based on retention policy"""
    try:
        result = database.cleanup_old_backups(daily_keep=daily_keep, weekly_keep=weekly_keep)
        
        if result['success']:
            return {
                'success': True,
                'deleted_count': result['deleted_count'],
                'message': result['message']
            }
        else:
            raise RuntimeError(result['message'])
            
    except Exception as e:
        print(f"cleanup_old_backups error: {e}")
        raise RuntimeError(f"Failed to cleanup backups: {e}") from e

def get_backup_system_info():
    """Get backup system information"""
    try:
        from services.database_backup import DatabaseBackupManager
        
        manager = DatabaseBackupManager()
        backups = manager.list_backups()
        
        # Calculate backup statistics
        backup_counts = {}
        total_size = 0
        
        for backup in backups:
            backup_type = backup['type']
            backup_counts[backup_type] = backup_counts.get(backup_type, 0) + 1
            total_size += backup['size']
        
        db_path = manager._get_database_path()
        
        return {
            'backup_directory': str(manager.backup_dir),
            'database_path': str(db_path),
            'database_exists': db_path.exists(),
            'database_size': db_path.stat().st_size if db_path.exists() else 0,
            'database_version': manager._get_database_version(),
            'backup_counts': backup_counts,
            'total_backup_size': total_size,
            'total_backups': len(backups)
        }
    except Exception as e:
        raise RuntimeError(f"get_backup_system_info failed: {e}") from e

#Create a global database instance

database = create_database()