# Database Backup System

This document explains how to use the comprehensive database backup system implemented for the Chame application.

## Overview

The backup system provides multiple ways to create, manage, and restore database backups:

1. **Programmatic API** - Use backup functions directly in code
2. **Command Line Interface** - Use the `backup_cli.py` script
3. **Admin API Integration** - Backup functions available through admin_api.py
4. **Automated Scheduling** - Automatic backups via `backup_scheduler.py`

## Features

- **Multiple backup types**: Manual, daily, weekly
- **Data export formats**: JSON, CSV, SQL
- **Metadata tracking**: Version, checksum, description, timestamps
- **Integrity verification**: Database integrity checks
- **Automatic cleanup**: Configurable retention policies
- **Safe restore**: Creates pre-restore backup automatically
- **Sensitive data filtering**: Option to exclude passwords from exports

## Quick Start

### 1. Create a Manual Backup

```bash
# Using CLI
python backup_cli.py create --description "Before migration"

# Using Python API
from chame_app.database_instance import Database
db = Database()
result = db.create_backup(description="Before migration")
```

### 2. List Available Backups

```bash
# Using CLI
python backup_cli.py list

# Using Python API
backups = db.list_backups()
```

### 3. Restore from Backup

```bash
# Using CLI (requires confirmation)
python backup_cli.py restore backup_file.db --confirm

# Using Python API
result = db.restore_backup("path/to/backup.db", confirm=True)
```

## Command Line Interface

The `backup_cli.py` script provides a comprehensive command-line interface:

### Create Backups

```bash
# Manual backup with description
python backup_cli.py create --description "Before major update"

# Daily backup (for automated systems)
python backup_cli.py create --type daily

# Weekly backup
python backup_cli.py create --type weekly --user "admin"
```

### List and Manage Backups

```bash
# List all backups
python backup_cli.py list

# List only manual backups
python backup_cli.py list --type manual

# Limit to 10 most recent
python backup_cli.py list --limit 10
```

### Restore Operations

```bash
# Restore from backup (WARNING: Overwrites current database!)
python backup_cli.py restore chame_backup_manual_20250627_143022.db --confirm
```

### Data Export

```bash
# Export to JSON (default)
python backup_cli.py export

# Export to CSV format
python backup_cli.py export --format csv

# Export to SQL with sensitive data
python backup_cli.py export --format sql --include-sensitive
```

### Cleanup Old Backups

```bash
# Clean up old backups (keeps 7 daily, 4 weekly)
python backup_cli.py cleanup --confirm

# Custom retention policy
python backup_cli.py cleanup --daily-keep 14 --weekly-keep 8 --confirm
```

### System Information

```bash
# Show backup system info
python backup_cli.py info
```

## Python API Usage

### Basic Backup Operations

```python
from chame_app.database_instance import Database

# Initialize database
db = Database()

# Create a backup
result = db.create_backup(
    backup_type="manual",
    description="Before testing new features",
    created_by="developer"
)

if result['success']:
    print(f"Backup created: {result['backup_path']}")
else:
    print(f"Backup failed: {result['message']}")

# List backups
backups = db.list_backups()
for backup in backups[:5]:  # Show 5 most recent
    print(f"{backup['filename']} - {backup['type']} - {backup['created']}")

# Restore from backup
result = db.restore_backup("/path/to/backup.db", confirm=True)
if result['success']:
    print("Database restored successfully")
    # Important: Restart application after restore
```

### Export Data

```python
# Export to JSON
result = db.export_data(format="json", include_sensitive=False)

# Export to CSV
result = db.export_data(format="csv")

# Export to SQL with all data
result = db.export_data(format="sql", include_sensitive=True)
```

### Cleanup Old Backups

```python
# Clean up with default retention (7 daily, 4 weekly)
result = db.cleanup_old_backups()

# Custom retention policy
result = db.cleanup_old_backups(daily_keep=14, weekly_keep=8)
```

## Admin API Integration

The backup functions are available through the admin API:

```python
import services.admin_api as api

# Create backup
result = api.create_backup(
    backup_type="manual",
    description="User requested backup",
    created_by="admin"
)

# List backups
backups = api.list_backups()

# Export data
result = api.export_data(format="json")

# Cleanup old backups
result = api.cleanup_old_backups(daily_keep=7, weekly_keep=4)
```

## Automated Backup Scheduling

The `backup_scheduler.py` script provides automated backup scheduling:

### Installation

First, install the required dependency:

```bash
pip install schedule
```

### Running the Scheduler

```bash
# Run as daemon (default)
python backup_scheduler.py

# Run a test backup
python backup_scheduler.py --test

# Run specific backup once
python backup_scheduler.py --run-once daily
python backup_scheduler.py --run-once weekly
python backup_scheduler.py --run-once cleanup
```

### Schedule Configuration

The default schedule is:
- **Daily backups**: Every day at 2:00 AM
- **Weekly backups**: Every Sunday at 3:00 AM  
- **Cleanup**: First day of each month at 4:00 AM

### Running as a Service

To run the scheduler as a system service, you can create a systemd service file:

```ini
# /etc/systemd/system/chame-backup.service
[Unit]
Description=Chame Database Backup Scheduler
After=network.target

[Service]
Type=simple
User=chame
WorkingDirectory=/path/to/chame/backend/app
ExecStart=/usr/bin/python3 backup_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable chame-backup.service
sudo systemctl start chame-backup.service
sudo systemctl status chame-backup.service
```

## Backup Directory Structure

Backups are organized in the following structure:

```
backups/
├── daily/                          # Daily backups
│   ├── chame_backup_daily_20250627_020000.db
│   └── chame_backup_daily_20250628_020000.db
├── weekly/                         # Weekly backups
│   └── chame_backup_weekly_20250623_030000.db
├── manual/                         # Manual backups
│   ├── chame_backup_manual_20250627_143022.db
│   └── chame_backup_manual_20250627_150000.db
└── metadata/                       # Backup metadata
    ├── chame_backup_daily_20250627_020000.db.json
    └── chame_backup_manual_20250627_143022.db.json
```

## Backup Metadata

Each backup includes metadata stored as JSON:

```json
{
  "timestamp": "2025-06-27T14:30:22",
  "backup_type": "manual",
  "database_version": "1",
  "file_size": 2048576,
  "checksum": "a1b2c3d4e5f6...",
  "description": "Before migration",
  "created_by": "admin"
}
```

## Security Considerations

1. **Sensitive Data**: Use `include_sensitive=False` when exporting data for external use
2. **Backup Location**: Store backups on a different drive/server for disaster recovery
3. **Access Control**: Restrict access to backup directories
4. **Encryption**: Consider encrypting backups containing sensitive data

## Best Practices

1. **Regular Testing**: Periodically test backup restoration in a development environment
2. **Multiple Backup Types**: Use both automated and manual backups
3. **Documentation**: Always include meaningful descriptions for manual backups
4. **Monitoring**: Monitor backup scheduler logs for failures
5. **Storage Management**: Regularly clean up old backups to manage disk space
6. **Disaster Recovery**: Store copies of critical backups off-site

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure the application has write access to the backup directory
2. **Disk Space**: Monitor available disk space for backup storage
3. **Database Locks**: Backups may fail if database is heavily used; try during off-peak hours
4. **Restore Issues**: Always verify database integrity after restore operations

### Error Messages

- **"Database file not found"**: Check database path and permissions
- **"Restore not confirmed"**: Use `confirm=True` parameter for restore operations  
- **"Insufficient disk space"**: Free up space in backup directory
- **"Backup integrity check failed"**: Source database may be corrupted

### Logging

Check the following log files for detailed error information:
- `backup_scheduler.log` - Automated backup scheduler logs
- Application logs - Database operation logs

## Migration and Backup Strategy

When performing database migrations:

1. **Pre-migration backup**: Always create a backup before migrations
```python
result = db.create_backup(description="Before migration to v2.0")
```

2. **Test migrations**: Test migrations on a copy of production data
3. **Rollback plan**: Keep pre-migration backups until migration is confirmed stable
4. **Post-migration verification**: Verify data integrity after migration

## Performance Considerations

- **Backup Size**: Large databases will create large backup files
- **Backup Time**: Backup creation time scales with database size
- **I/O Impact**: Backup operations may temporarily impact database performance
- **Storage**: Plan backup storage capacity based on database growth and retention policy

## Integration with Testing

The backup system integrates well with the testing framework:

```python
# In test setup
def setUp(self):
    # Create test backup before running tests
    self.backup_result = db.create_backup(description="Before tests")

def tearDown(self):
    # Optionally restore from backup after tests
    if self.restore_after_tests:
        db.restore_backup(self.backup_result['backup_path'], confirm=True)
```

This comprehensive backup system ensures your Chame database is protected against data loss and provides flexible recovery options for various scenarios.
