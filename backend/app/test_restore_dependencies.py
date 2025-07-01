#!/usr/bin/env python3
"""
Test script for the enhanced restore dependency checking
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from services.admin_api import create_database, analyze_deletion_impact, execute_deletion, restore_product, restore_ingredient
    import json
    
    print("🧪 Testing Enhanced Restore with Dependency Checking")
    print("=" * 60)
    
    # Initialize the database
    print("📋 Initializing database...")
    db = create_database(apply_migration=True)
    print("✅ Database initialized")
    
    # Test 1: Try to restore a product that was cascaded from ingredient deletion
    print("\n🔍 Test 1: Attempt to restore product before restoring ingredient")
    try:
        # This should fail because ingredient 1 is likely soft-deleted and product 1 depends on it
        result = restore_product(1)
        print(f"❌ Unexpected success: {result}")
    except RuntimeError as e:
        if "required ingredients are still deleted" in str(e):
            print(f"✅ Correctly blocked restoration: {e}")
        else:
            print(f"❌ Unexpected error: {e}")
    except Exception as e:
        print(f"❓ Other error: {e}")
    
    # Test 2: Try to restore the ingredient first
    print("\n🔍 Test 2: Restore ingredient first")
    try:
        result = restore_ingredient(1)
        print(f"✅ Ingredient restored: {result}")
    except Exception as e:
        print(f"❌ Error restoring ingredient: {e}")
    
    # Test 3: Now try to restore the product again
    print("\n🔍 Test 3: Now attempt to restore product after ingredient")
    try:
        result = restore_product(1)
        print(f"✅ Product restored successfully: {result}")
    except Exception as e:
        print(f"❌ Error restoring product: {e}")
    
    print("\n✅ Enhanced restore dependency checking test completed")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the backend/app directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
