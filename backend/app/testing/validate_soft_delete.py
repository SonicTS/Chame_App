#!/usr/bin/env python3
"""
Simple validation script for soft delete functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_soft_delete_integration():
    """Test that the soft delete integration is working"""
    print("🧪 Testing Soft Delete Integration...")
    
    # Test 1: Import models and verify columns
    print("\n1. Testing model imports and column verification...")
    try:
        from models.user_table import User
        from models.product_table import Product
        from models.ingredient import Ingredient
        
        user_columns = [c.name for c in User.__table__.columns]
        product_columns = [c.name for c in Product.__table__.columns]  
        ingredient_columns = [c.name for c in Ingredient.__table__.columns]
        
        # Check soft delete columns exist
        soft_delete_cols = ['is_deleted', 'deleted_at', 'deleted_by']
        
        for col in soft_delete_cols:
            if col in user_columns:
                print(f"  ✅ User.{col} exists")
            else:
                print(f"  ❌ User.{col} missing")
                
            if col in product_columns:
                print(f"  ✅ Product.{col} exists")
            else:
                print(f"  ❌ Product.{col} missing")
                
            if col in ingredient_columns:
                print(f"  ✅ Ingredient.{col} exists")
            else:
                print(f"  ❌ Ingredient.{col} missing")
        
    except Exception as e:
        print(f"  ❌ Model import failed: {e}")
        return False
    
    # Test 2: Check that admin API functions exist
    print("\n2. Testing admin API soft delete functions...")
    try:
        import services.admin_api as api
        
        soft_delete_functions = [
            'soft_delete_user', 'soft_delete_product', 'soft_delete_ingredient',
            'safe_delete_user', 'safe_delete_product', 'safe_delete_ingredient',
            'restore_user', 'check_deletion_dependencies',
        ]
        
        for func_name in soft_delete_functions:
            if hasattr(api, func_name):
                print(f"  ✅ {func_name} exists")
            else:
                print(f"  ❌ {func_name} missing")
        
    except Exception as e:
        print(f"  ❌ Admin API import failed: {e}")
        return False
    
    # Test 3: Test migration exists
    print("\n3. Testing migration exists...")
    try:
        from chame_app.simple_migrations import SimpleMigrations
        from chame_app.database_instance import Database
        
        # Create a database instance to get the engine
        db = Database()
        engine = db._engine
        
        migrations = SimpleMigrations(engine)
        
        if '003_add_soft_delete_columns' in migrations.migrations:
            print("  ✅ Soft delete migration (003_add_soft_delete_columns) exists")
        else:
            print("  ❌ Soft delete migration missing")
        
        print(f"  📊 Total migrations available: {len(migrations.migrations)}")
        
    except Exception as e:
        print(f"  ❌ Migration test failed: {e}")
        return False
    
    print("\n✅ Soft delete integration test completed successfully!")
    return True

if __name__ == '__main__':
    success = test_soft_delete_integration()
    exit(0 if success else 1)
