#!/usr/bin/env python3
# backup_cli.py
# Command-line interface for database backup operations

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_backup import DatabaseBackupManager
from chame_app.database_instance import Database

def main():
    parser = argparse.ArgumentParser(description='Chame Database Backup Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup command
    create_parser = subparsers.add_parser('create', help='Create a new backup')
    create_parser.add_argument('--type', choices=['manual', 'daily', 'weekly'], 
                              default='manual', help='Backup type (default: manual)')
    create_parser.add_argument('--description', '-d', default='', 
                              help='Backup description')
    create_parser.add_argument('--user', default='cli', 
                              help='User creating the backup (default: cli)')
    
    # List backups command
    list_parser = subparsers.add_parser('list', help='List all backups')
    list_parser.add_argument('--limit', '-l', type=int, default=20, 
                            help='Limit number of backups to show (default: 20)')
    list_parser.add_argument('--type', choices=['manual', 'daily', 'weekly'], 
                            help='Filter by backup type')
    
    # Restore backup command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_file', help='Backup file to restore from')
    restore_parser.add_argument('--confirm', action='store_true', 
                               help='Confirm the restore operation')
    
    # Delete backup command
    delete_parser = subparsers.add_parser('delete', help='Delete a backup')
    delete_parser.add_argument('backup_file', help='Backup file to delete')
    delete_parser.add_argument('--confirm', action='store_true', 
                               help='Confirm the deletion')
    
    # Export data command
    export_parser = subparsers.add_parser('export', help='Export database data')
    export_parser.add_argument('--format', choices=['json', 'csv', 'sql'], 
                              default='json', help='Export format (default: json)')
    export_parser.add_argument('--include-sensitive', action='store_true', 
                              help='Include sensitive data like passwords')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
    cleanup_parser.add_argument('--daily-keep', type=int, default=7, 
                               help='Number of daily backups to keep (default: 7)')
    cleanup_parser.add_argument('--weekly-keep', type=int, default=4, 
                               help='Number of weekly backups to keep (default: 4)')
    cleanup_parser.add_argument('--confirm', action='store_true', 
                               help='Confirm the cleanup operation')
    
    # Info command
    subparsers.add_parser('info', help='Show backup system information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'create':
            return cmd_create_backup(args)
        elif args.command == 'list':
            return cmd_list_backups(args)
        elif args.command == 'restore':
            return cmd_restore_backup(args)
        elif args.command == 'delete':
            return cmd_delete_backup(args)
        elif args.command == 'export':
            return cmd_export_data(args)
        elif args.command == 'cleanup':
            return cmd_cleanup_backups(args)
        elif args.command == 'info':
            return cmd_show_info(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def cmd_create_backup(args):
    """Create a new backup"""
    print(f"🔄 Creating {args.type} backup...")
    
    manager = DatabaseBackupManager()
    result = manager.create_backup(
        backup_type=args.type,
        description=args.description,
        created_by=args.user
    )
    
    if result['success']:
        print(f"✅ {result['message']}")
        metadata = result.get('metadata', {})
        print(f"   📁 Path: {result['backup_path']}")
        print(f"   📊 Size: {metadata.get('file_size', 0) / (1024*1024):.1f} MB")
        print(f"   🏷️ Version: {metadata.get('database_version', 'unknown')}")
        return 0
    else:
        print(f"❌ {result['message']}")
        return 1

def cmd_list_backups(args):
    """List all backups"""
    manager = DatabaseBackupManager()
    backups = manager.list_backups()
    
    if not backups:
        print("📦 No backups found")
        return 0
    
    # Filter by type if specified
    if args.type:
        backups = [b for b in backups if b['type'] == args.type]
    
    # Limit results
    backups = backups[:args.limit]
    
    print(f"📦 Found {len(backups)} backup(s):")
    print("=" * 80)
    
    for backup in backups:
        size_mb = backup['size'] / (1024 * 1024)
        metadata = backup.get('metadata', {})
        
        print(f"📄 {backup['filename']}")
        print(f"   Type: {backup['backup_type']}")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"   Created: {backup['created_at']}")
        print(f"   Description: {metadata.get('description', 'No description')}")
        print(f"   Version: {metadata.get('database_version', 'unknown')}")
        print()
    
    return 0

def cmd_restore_backup(args):
    """Restore from backup"""
    if not args.confirm:
        print("⚠️ WARNING: This will overwrite your current database!")
        print("Use --confirm to proceed with the restore operation.")
        return 1
    
    print(f"🔄 Restoring database from {args.backup_file}...")
    
    manager = DatabaseBackupManager()
    result = manager.restore_backup(args.backup_file, confirm=True)
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   📁 Database: {result['database_path']}")
        print("⚠️ Important: Restart the application to use the restored database")
        return 0
    else:
        print(f"❌ {result['message']}")
        return 1

def cmd_delete_backup(args):
    """Delete a backup"""
    if not args.confirm:
        print("⚠️ This will permanently delete the backup file!")
        print("Use --confirm to proceed with the deletion.")
        return 1
    
    print(f"🗑️ Deleting backup {args.backup_file}...")
    
    manager = DatabaseBackupManager()
    result = manager.delete_backup(args.backup_file)
    
    if result['success']:
        print(f"✅ {result['message']}")
        return 0
    else:
        print(f"❌ {result['message']}")
        return 1

def cmd_export_data(args):
    """Export database data"""
    print(f"📤 Exporting data in {args.format} format...")
    
    manager = DatabaseBackupManager()
    result = manager.export_data(
        format=args.format,
        include_sensitive=args.include_sensitive
    )
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   📁 Export path: {result['export_path']}")
        if 'files' in result:
            print(f"   📄 Files: {', '.join(result['files'])}")
        return 0
    else:
        print(f"❌ {result['message']}")
        return 1

def cmd_cleanup_backups(args):
    """Clean up old backups"""
    if not args.confirm:
        print("⚠️ This will permanently delete old backup files!")
        print(f"Daily backups to keep: {args.daily_keep}")
        print(f"Weekly backups to keep: {args.weekly_keep}")
        print("Use --confirm to proceed with the cleanup.")
        return 1
    
    print("🧹 Cleaning up old backups...")
    
    manager = DatabaseBackupManager()
    result = manager.cleanup_old_backups(
        daily_keep=args.daily_keep,
        weekly_keep=args.weekly_keep
    )
    
    if result['success']:
        print(f"✅ {result['message']}")
        return 0
    else:
        print(f"❌ {result['message']}")
        return 1

def cmd_show_info(_args):
    """Show backup system information"""
    manager = DatabaseBackupManager()
    
    print("🔧 Chame Database Backup System Information")
    print("=" * 50)
    
    # Backup directory info
    print(f"📁 Backup Directory: {manager.backup_dir}")
    print(f"   Exists: {'✅' if manager.backup_dir.exists() else '❌'}")
    
    # Database info
    db_path = manager._get_database_path()
    print(f"🗄️ Database Path: {db_path}")
    print(f"   Exists: {'✅' if db_path.exists() else '❌'}")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"   Size: {size_mb:.1f} MB")
    
    # Version info
    db_version = manager._get_database_version()
    print(f"📋 Database Version: {db_version}")
    
    # Backup counts
    backups = manager.list_backups()
    backup_counts = {}
    total_size = 0
    
    for backup in backups:
        backup_type = backup['backup_type']
        backup_counts[backup_type] = backup_counts.get(backup_type, 0) + 1
        total_size += backup['size']
    
    print("📦 Available Backups:")
    for backup_type, count in backup_counts.items():
        print(f"   {backup_type.title()}: {count}")
    print(f"   Total Size: {total_size / (1024*1024):.1f} MB")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
