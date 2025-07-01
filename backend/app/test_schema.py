#!/usr/bin/env python3
"""
Quick test script to check if the database schema is correct
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chame_app.database_instance import get_database
from chame_app.simple_migrations import SimpleMigrations
from sqlalchemy import inspect

def test_schema():
    """Test if the database schema includes all required columns"""
    print("🔍 Testing database schema...")
    
    # Get database engine
    engine = get_database()
    
    # Run migrations to ensure schema is up to date
    print("🔄 Running migrations...")
    migrations = SimpleMigrations(engine)
    migration_success = migrations.run_migrations(create_backup=False)
    
    if not migration_success:
        print("❌ Migrations failed!")
        return False
    
    print("✅ Migrations completed successfully")
    
    # Check schema
    inspector = inspect(engine)
    
    # Check users table
    print("\n📋 Checking users table schema...")
    users_columns = {col['name']: col['type'] for col in inspector.get_columns('users')}
    required_users_columns = [
        'user_id', 'name', 'balance', 'password_hash', 'role',
        'is_deleted', 'deleted_at', 'deleted_by', 
        'is_disabled', 'disabled_reason'
    ]
    
    users_missing = [col for col in required_users_columns if col not in users_columns]
    if users_missing:
        print(f"❌ Users table missing columns: {users_missing}")
        return False
    else:
        print("✅ Users table has all required columns")
    
    # Check products table
    print("\n📋 Checking products table schema...")
    products_columns = {col['name']: col['type'] for col in inspector.get_columns('products')}
    required_products_columns = [
        'product_id', 'name', 'category', 'price', 'toaster_space',
        'is_deleted', 'deleted_at', 'deleted_by',
        'is_disabled', 'disabled_reason'
    ]
    
    products_missing = [col for col in required_products_columns if col not in products_columns]
    if products_missing:
        print(f"❌ Products table missing columns: {products_missing}")
        return False
    else:
        print("✅ Products table has all required columns")
    
    # Check ingredients table
    print("\n📋 Checking ingredients table schema...")
    ingredients_columns = {col['name']: col['type'] for col in inspector.get_columns('ingredients')}
    required_ingredients_columns = [
        'ingredient_id', 'name', 'price_per_package', 'stock_quantity', 'number_ingredients', 'pfand',
        'is_deleted', 'deleted_at', 'deleted_by',
        'is_disabled', 'disabled_reason'
    ]
    
    ingredients_missing = [col for col in required_ingredients_columns if col not in ingredients_columns]
    if ingredients_missing:
        print(f"❌ Ingredients table missing columns: {ingredients_missing}")
        return False
    else:
        print("✅ Ingredients table has all required columns")
    
    print("\n🎉 All tables have the correct schema!")
    return True

def test_simple_query():
    """Test a simple query to see if the models work correctly"""
    print("\n🔍 Testing simple database query...")
    
    try:
        from services.admin_api import get_all_users
        
        # This should work without errors now
        users = get_all_users()
        print(f"✅ Successfully queried users table: {len(users)} users found")
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Schema Test")
    print("=" * 50)
    
    schema_ok = test_schema()
    query_ok = test_simple_query()
    
    if schema_ok and query_ok:
        print("\n🎯 All tests passed! Database schema is correct.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)
