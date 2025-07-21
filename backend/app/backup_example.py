#!/usr/bin/env python3
# backup_example.py
# Example script demonstrating backup functionality

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chame_app.database_instance import Database
import services.admin_api as api

def main():
    print("🔧 Chame Database Backup Example")
    print("=" * 40)
    
    try:
        # Initialize database
        db = Database()
        print("✅ Database initialized")
        
        # Example 1: Create a manual backup
        print("\n📦 Creating manual backup...")
        backup_result = db.create_backup(
            backup_type="manual",
            description="Example backup from script",
            created_by="example_script"
        )
        
        if backup_result['success']:
            print(f"✅ Backup created: {backup_result['backup_path']}")
            metadata = backup_result['metadata']
            print(f"   📊 Size: {metadata['file_size'] / (1024*1024):.1f} MB")
            print(f"   🏷️ Version: {metadata['database_version']}")
        else:
            print(f"❌ Backup failed: {backup_result['message']}")
            return 1
        
        # Example 2: List existing backups
        print("\n📋 Listing existing backups...")
        backups = db.list_backups()
        
        if backups:
            print(f"Found {len(backups)} backup(s):")
            for i, backup in enumerate(backups[:5], 1):  # Show first 5
                size_mb = backup['size'] / (1024 * 1024)
                print(f"  {i}. {backup['filename']}")
                print(f"     Type: {backup['backup_type']}, Size: {size_mb:.1f} MB")
                print(f"     Created: {backup['created_at']}")
        else:
            print("No backups found")
        
        # Example 3: Export data to JSON
        print("\n📤 Exporting data to JSON...")
        export_result = db.export_data(
            format="json",
            include_sensitive=False  # Don't include passwords
        )
        
        if export_result['success']:
            print(f"✅ Data exported: {export_result['export_path']}")
        else:
            print(f"❌ Export failed: {export_result['message']}")
        
        # Example 4: Using admin API
        print("\n🔧 Using Admin API...")
        try:
            # Get all users to show data is accessible
            users = api.get_all_users()
            print(f"📊 Database contains {len(users)} users")
            
            # Create backup via API
            api_backup = api.create_backup(
                backup_type="manual",
                description="Backup via admin API",
                created_by="api_example"
            )
            print(f"✅ API backup created: {api_backup['message']}")
            
        except Exception as e:
            print(f"⚠️ Admin API example failed: {e}")
        
        # Example 5: Show backup system info
        print("\n🔍 Backup System Information...")
        from services.database_backup import DatabaseBackupManager
        
        manager = DatabaseBackupManager()
        db_path = manager._get_database_path()
        
        print(f"📁 Backup Directory: {manager.backup_dir}")
        print(f"🗄️ Database Path: {db_path}")
        print(f"📋 Database Version: {manager._get_database_version()}")
        
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"📊 Database Size: {size_mb:.1f} MB")
        
        print("\n✅ Backup example completed successfully!")
        print("\n💡 Tips:")
        print("   - Use 'python backup_cli.py list' to see all backups")
        print("   - Use 'python backup_cli.py info' for system information")
        print("   - Use 'python backup_cli.py create --description \"your description\"' for manual backups")
        print("   - Always test restore operations in a development environment first")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
