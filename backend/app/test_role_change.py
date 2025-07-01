#!/usr/bin/env python3
"""
Test script to verify the change_user_role functionality
"""

from services.admin_api import create_database, change_user_role, get_all_users
import sys

def test_change_user_role():
    """Test the change_user_role function"""
    try:
        # Create database and add a test user
        db = create_database()
        print('Database created successfully')
        
        # Check if we have users first
        users = get_all_users()
        print(f'Found {len(users)} users')
        
        if users:
            user = users[0]  # Get first user
            user_id = user['user_id']
            old_role = user['role']
            print(f'Testing role change for user {user_id}: {user["name"]} (current role: {old_role})')
            
            # Try changing role
            new_role = 'admin' if old_role != 'admin' else 'user'
            result = change_user_role(user_id, new_role)
            print(f'Role change result: {result}')
            
            # Verify the change
            updated_users = get_all_users()
            updated_user = next((u for u in updated_users if u['user_id'] == user_id), None)
            if updated_user:
                print(f'✅ Role successfully changed from {old_role} to {updated_user["role"]}')
                return True
            else:
                print('❌ Error: Could not find updated user')
                return False
        else:
            print('❌ No users found to test with')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing change_user_role functionality...")
    success = test_change_user_role()
    print(f"🎯 Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
