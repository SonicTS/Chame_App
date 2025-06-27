# database_backup.py
# Comprehensive database backup and restore functionality

import os
import shutil
import sqlite3
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# Constants
DB_FILENAME = "kassensystem.db"
FILTERED_TEXT = "[FILTERED]"
GET_TABLES_SQL = "SELECT name FROM sqlite_master WHERE type='table'"

@dataclass
class BackupMetadata:
    """Metadata for database backups"""
    timestamp: str
    backup_type: str  # 'full', 'incremental', 'manual'
    database_version: str
    file_size: int
    checksum: str
    description: str
    created_by: str = "system"

class DatabaseBackupManager:
    """Manages database backups and restores"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups. If None, uses environment or default.
        """
        self.backup_dir = self._get_backup_directory(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "daily").mkdir(exist_ok=True)
        (self.backup_dir / "weekly").mkdir(exist_ok=True)
        (self.backup_dir / "manual").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
        
        logger.info(f"Backup manager initialized. Backup directory: {self.backup_dir}")
    
    def _get_backup_directory(self, backup_dir: Optional[str]) -> Path:
        """Get the backup directory path"""
        if backup_dir:
            return Path(backup_dir)
        
        # Check environment variables
        private_dir = os.environ.get("PRIVATE_STORAGE")
        if private_dir:
            return Path(private_dir) / "backups"
        
        home_dir = os.environ.get("HOME")
        if home_dir:
            return Path(home_dir) / "chame_backups"
        
        # Default to current directory
        return Path("backups")
    
    def _get_database_path(self) -> Path:
        """Get the current database file path"""
        private_dir = os.environ.get("PRIVATE_STORAGE")
        home_dir = os.environ.get("HOME")
        
        if private_dir:
            db_path = Path(private_dir) / DB_FILENAME
        elif home_dir:
            db_path = Path(home_dir) / DB_FILENAME
        else:
            db_path = Path(DB_FILENAME)
        
        return db_path
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file"""
        import hashlib
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_database_version(self) -> str:
        """Get database version from user_version pragma"""
        db_path = self._get_database_path()
        if not db_path.exists():
            return "0"
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            conn.close()
            return str(version)
        except Exception as e:
            logger.warning(f"Failed to get database version: {e}")
            return "unknown"
    
    def create_backup(self, 
                      backup_type: str = "manual", 
                      description: str = "", 
                      created_by: str = "user") -> Dict[str, Any]:
        """
        Create a database backup
        
        Args:
            backup_type: Type of backup ('manual', 'daily', 'weekly')
            description: Description of the backup
            created_by: Who created the backup
            
        Returns:
            Dict with backup information
        """
        try:
            db_path = self._get_database_path()
            if not db_path.exists():
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            # Generate backup filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"chame_backup_{backup_type}_{timestamp}.db"
            
            # Determine backup subdirectory
            if backup_type in ["daily", "weekly"]:
                backup_subdir = self.backup_dir / backup_type
            else:
                backup_subdir = self.backup_dir / "manual"
            
            backup_path = backup_subdir / backup_filename
            
            # Create backup using SQLite backup API for consistency
            self._create_sqlite_backup(db_path, backup_path)
            
            # Calculate metadata
            file_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            db_version = self._get_database_version()
            
            # Create metadata
            metadata = BackupMetadata(
                timestamp=datetime.datetime.now().isoformat(),
                backup_type=backup_type,
                database_version=db_version,
                file_size=file_size,
                checksum=checksum,
                description=description or f"Automatic {backup_type} backup",
                created_by=created_by
            )
            
            # Save metadata
            metadata_path = self.backup_dir / "metadata" / f"{backup_filename}.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_path}")
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'metadata': asdict(metadata),
                'message': f"Backup created: {backup_filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Backup failed: {e}"
            }
    
    def _create_sqlite_backup(self, source_path: Path, backup_path: Path):
        """Create backup using SQLite backup API for database consistency"""
        # Connect to source database
        source_conn = sqlite3.connect(str(source_path))
        
        # Create backup database
        backup_conn = sqlite3.connect(str(backup_path))
        
        try:
            # Use SQLite backup API
            source_conn.backup(backup_conn)
        finally:
            source_conn.close()
            backup_conn.close()
    
    def restore_backup(self, backup_path: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            confirm: Must be True to actually perform restore
            
        Returns:
            Dict with restore information
        """
        try:
            if not confirm:
                return {
                    'success': False,
                    'error': 'Restore not confirmed',
                    'message': 'You must set confirm=True to perform restore'
                }
            
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            db_path = self._get_database_path()
            
            # Create backup of current database before restore
            if db_path.exists():
                pre_restore_backup = self.create_backup(
                    backup_type="manual",
                    description="Automatic backup before restore",
                    created_by="system"
                )
                logger.info(f"Created pre-restore backup: {pre_restore_backup.get('backup_path')}")
            
            # Perform restore
            shutil.copy2(backup_file, db_path)
            
            # Verify restored database
            if not self._verify_database_integrity(db_path):
                raise RuntimeError("Restored database failed integrity check")
            
            logger.info(f"Database restored successfully from: {backup_path}")
            
            return {
                'success': True,
                'restored_from': backup_path,
                'database_path': str(db_path),
                'message': f"Database restored from {backup_file.name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Restore failed: {e}"
            }
    
    def _verify_database_integrity(self, db_path: Path) -> bool:
        """Verify database integrity"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            return result == "ok"
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_type in ["daily", "weekly", "manual"]:
            backup_subdir = self.backup_dir / backup_type
            if not backup_subdir.exists():
                continue
            
            for backup_file in backup_subdir.glob("*.db"):
                metadata_file = self.backup_dir / "metadata" / f"{backup_file.name}.json"
                
                backup_info = {
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'type': backup_type,
                    'size': backup_file.stat().st_size,
                    'created': datetime.datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()
                }
                
                # Load metadata if available
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backup_info['metadata'] = metadata
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for {backup_file.name}: {e}")
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def delete_backup(self, backup_filename: str) -> Dict[str, Any]:
        """Delete a specific backup and its metadata"""
        try:
            # Find the backup file
            backup_path = None
            for backup_type in ["daily", "weekly", "manual"]:
                potential_path = self.backup_dir / backup_type / backup_filename
                if potential_path.exists():
                    backup_path = potential_path
                    break
            
            if not backup_path:
                raise FileNotFoundError(f"Backup not found: {backup_filename}")
            
            # Delete backup file
            backup_path.unlink()
            
            # Delete metadata file
            metadata_path = self.backup_dir / "metadata" / f"{backup_filename}.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Backup deleted: {backup_filename}")
            
            return {
                'success': True,
                'message': f"Backup deleted: {backup_filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to delete backup: {e}"
            }
    
    def cleanup_old_backups(self, 
                           daily_keep: int = 7, 
                           weekly_keep: int = 4) -> Dict[str, Any]:
        """
        Clean up old backups based on retention policy
        
        Args:
            daily_keep: Number of daily backups to keep
            weekly_keep: Number of weekly backups to keep
        """
        deleted_count = 0
        
        try:
            # Clean daily backups
            daily_backups = list((self.backup_dir / "daily").glob("*.db"))
            daily_backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            for backup in daily_backups[daily_keep:]:
                backup.unlink()
                metadata_file = self.backup_dir / "metadata" / f"{backup.name}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old daily backup: {backup.name}")
            
            # Clean weekly backups
            weekly_backups = list((self.backup_dir / "weekly").glob("*.db"))
            weekly_backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            for backup in weekly_backups[weekly_keep:]:
                backup.unlink()
                metadata_file = self.backup_dir / "metadata" / f"{backup.name}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old weekly backup: {backup.name}")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f"Cleaned up {deleted_count} old backups"
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Cleanup failed: {e}"
            }
    
    def export_data(self, format: str = "json", include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Export database data in various formats
        
        Args:
            format: Export format ('json', 'csv', 'sql')
            include_sensitive: Whether to include sensitive data (passwords, etc.)
        """
        try:
            db_path = self._get_database_path()
            if not db_path.exists():
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"chame_export_{format}_{timestamp}"
            
            if format == "json":
                return self._export_json(conn, export_filename, include_sensitive)
            elif format == "csv":
                return self._export_csv(conn, export_filename, include_sensitive)
            elif format == "sql":
                return self._export_sql(conn, export_filename, include_sensitive)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Export failed: {e}"
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _export_json(self, conn: sqlite3.Connection, filename: str, include_sensitive: bool) -> Dict[str, Any]:
        """Export data to JSON format"""
        export_path = self.backup_dir / f"{filename}.json"
        
        # Get all tables
        cursor = conn.cursor()
        cursor.execute(GET_TABLES_SQL)
        tables = [row[0] for row in cursor.fetchall()]
        
        export_data = {}
        
        for table in tables:
            if table.startswith('sqlite_'):
                continue
                
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            table_data = []
            for row in rows:
                row_dict = dict(row)
                
                # Filter sensitive data if requested
                if not include_sensitive and 'password' in row_dict:
                    row_dict['password_hash'] = FILTERED_TEXT
                
                table_data.append(row_dict)
            
            export_data[table] = table_data
        
        # Add metadata
        export_data['_metadata'] = {
            'export_timestamp': datetime.datetime.now().isoformat(),
            'database_version': self._get_database_version(),
            'include_sensitive': include_sensitive,
            'format': 'json'
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return {
            'success': True,
            'export_path': str(export_path),
            'format': 'json',
            'message': f"Data exported to {filename}.json"
        }
    
    def _export_csv(self, conn: sqlite3.Connection, filename: str, include_sensitive: bool) -> Dict[str, Any]:
        """Export data to CSV format (one file per table)"""
        import csv
        
        export_dir = self.backup_dir / filename
        export_dir.mkdir(exist_ok=True)
        
        # Get all tables
        cursor = conn.cursor()
        cursor.execute(GET_TABLES_SQL)
        tables = [row[0] for row in cursor.fetchall()]
        
        exported_files = []
        
        for table in tables:
            if table.startswith('sqlite_'):
                continue
                
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows:
                continue
            
            csv_path = export_dir / f"{table}.csv"
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                
                for row in rows:
                    row_dict = dict(row)
                    
                    # Filter sensitive data if requested
                    if not include_sensitive and 'password_hash' in row_dict:
                        row_dict['password_hash'] = FILTERED_TEXT
                    
                    writer.writerow(row_dict)
            
            exported_files.append(csv_path.name)
        
        return {
            'success': True,
            'export_path': str(export_dir),
            'format': 'csv',
            'files': exported_files,
            'message': f"Data exported to {len(exported_files)} CSV files in {filename}/"
        }
    
    def _export_sql(self, conn: sqlite3.Connection, filename: str, include_sensitive: bool) -> Dict[str, Any]:
        """Export data to SQL format"""
        export_path = self.backup_dir / f"{filename}.sql"
        
        with open(export_path, 'w') as f:
            # Write header
            f.write("-- Chame Database Export\n")
            f.write(f"-- Generated: {datetime.datetime.now().isoformat()}\n")
            f.write(f"-- Database Version: {self._get_database_version()}\n")
            f.write(f"-- Include Sensitive: {include_sensitive}\n\n")
            
            # Export schema
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
            for row in cursor.fetchall():
                if row[0]:
                    f.write(f"{row[0]};\n\n")
            
            # Export data
            cursor.execute(GET_TABLES_SQL)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                if table.startswith('sqlite_'):
                    continue
                
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                if not rows:
                    continue
                
                f.write(f"-- Data for table {table}\n")
                
                for row in rows:
                    row_dict = dict(row)
                    
                    # Filter sensitive data if requested
                    if not include_sensitive and 'password_hash' in row_dict:
                        row_dict['password_hash'] = FILTERED_TEXT
                    
                    columns = ', '.join(row_dict.keys())
                    values = ', '.join([f"'{str(v).replace(chr(39), chr(39)+chr(39))}'" if v is not None else 'NULL' for v in row_dict.values()])
                    
                    f.write(f"INSERT INTO {table} ({columns}) VALUES ({values});\n")
                
                f.write("\n")
        
        return {
            'success': True,
            'export_path': str(export_path),
            'format': 'sql',
            'message': f"Data exported to {filename}.sql"
        }

# Convenience function for quick backups
def create_quick_backup(description: str = "Quick backup") -> Dict[str, Any]:
    """Create a quick manual backup"""
    manager = DatabaseBackupManager()
    return manager.create_backup(
        backup_type="manual",
        description=description,
        created_by="user"
    )

# Convenience function for scheduled backups
def create_scheduled_backup(backup_type: str = "daily") -> Dict[str, Any]:
    """Create a scheduled backup (daily/weekly)"""
    manager = DatabaseBackupManager()
    return manager.create_backup(
        backup_type=backup_type,
        description=f"Scheduled {backup_type} backup",
        created_by="system"
    )
