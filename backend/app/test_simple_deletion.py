#!/usr/bin/env python3
"""
Test script for the new simple deletion system
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from services.admin_api import create_database, analyze_deletion_impact, execute_deletion
    import json
    
    print("🧪 Testing Simple Deletion System")
    print("=" * 50)
    
    # Initialize the database
    print("📋 Initializing database...")
    db = create_database(apply_migration=True)
    print("✅ Database initialized")
    
    # Test 1: Analyze ingredient deletion impact
    print("\n🔍 Test 1: Analyzing ingredient deletion impact")
    try:
        result = analyze_deletion_impact('ingredient', 1)
        print(f"✅ Result: {result}")
        if isinstance(result, str):
            result_data = json.loads(result)
            print(f"   Type: {result_data.get('deletion_type', 'unknown')}")
            print(f"   Dependencies: {len(result_data.get('dependencies', []))}")
            print(f"   Warnings: {result_data.get('warnings', [])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Analyze product deletion impact
    print("\n🔍 Test 2: Analyzing product deletion impact")
    try:
        result = analyze_deletion_impact('product', 1)
        print(f"✅ Result: {result}")
        if isinstance(result, str):
            result_data = json.loads(result)
            print(f"   Type: {result_data.get('deletion_type', 'unknown')}")
            print(f"   Dependencies: {len(result_data.get('dependencies', []))}")
            print(f"   Warnings: {result_data.get('warnings', [])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Analyze user deletion impact
    print("\n🔍 Test 3: Analyzing user deletion impact")
    try:
        result = analyze_deletion_impact('user', 1)
        print(f"✅ Result: {result}")
        if isinstance(result, str):
            result_data = json.loads(result)
            print(f"   Type: {result_data.get('deletion_type', 'unknown')}")
            print(f"   Dependencies: {len(result_data.get('dependencies', []))}")
            print(f"   Warnings: {result_data.get('warnings', [])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ Simple deletion system test completed")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the backend/app directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
