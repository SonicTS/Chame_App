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
                    'backup_type': backup_type,  # Changed from 'type' to 'backup_type'
                    'size': backup_file.stat().st_size,
                    'created_at': datetime.datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()  # Changed from 'created' to 'created_at'
                }
                
                # Load metadata if available and merge important fields
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backup_info['metadata'] = metadata
                        # Merge key metadata fields to top level for easier access
                        backup_info['description'] = metadata.get('description', '')
                        backup_info['checksum'] = metadata.get('checksum', '')
                        backup_info['created_by'] = metadata.get('created_by', 'system')
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for {backup_file.name}: {e}")
                        # Set default values if metadata loading fails
                        backup_info['description'] = ''
                        backup_info['checksum'] = ''
                        backup_info['created_by'] = 'system'
                else:
                    # Set default values if no metadata file exists
                    backup_info['description'] = ''
                    backup_info['checksum'] = ''
                    backup_info['created_by'] = 'system'
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
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
    
    def export_backup_to_public(self, backup_filename: str) -> Dict[str, Any]:
        """
        Export backup file to Android's public storage for sharing
        
        Args:
            backup_filename: Name of the backup file to export
            
        Returns:
            Dict with export information
        """
        try:
            # Find the backup file
            backup_path = None
            backup_type = None
            for btype in ["daily", "weekly", "manual"]:
                potential_path = self.backup_dir / btype / backup_filename
                if potential_path.exists():
                    backup_path = potential_path
                    backup_type = btype
                    break
            
            if not backup_path:
                raise FileNotFoundError(f"Backup not found: {backup_filename}")
            
            # Get Android's public storage directory
            shared_storage = os.environ.get("EXTERNAL_STORAGE", "/storage/emulated/0")
            export_dir = Path(shared_storage) / "Download" / "ChameBackups"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy backup file to public storage
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"exported_{timestamp}_{backup_filename}"
            export_path = export_dir / export_filename
            
            shutil.copy2(backup_path, export_path)
            
            # Copy metadata if it exists
            metadata_source = self.backup_dir / "metadata" / f"{backup_filename}.json"
            metadata_export = None
            if metadata_source.exists():
                metadata_filename = f"exported_{timestamp}_{backup_filename}.json"
                metadata_export = export_dir / metadata_filename
                shutil.copy2(metadata_source, metadata_export)
            
            # Create a readable info file
            info_filename = f"exported_{timestamp}_{backup_filename}_info.txt"
            info_path = export_dir / info_filename
            
            with open(info_path, 'w') as f:
                f.write("Chame Database Backup Export\n")
                f.write("=" * 40 + "\n")
                f.write(f"Original Backup: {backup_filename}\n")
                f.write(f"Backup Type: {backup_type}\n")
                f.write(f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"File Size: {backup_path.stat().st_size} bytes\n")
                f.write(f"Exported File: {export_filename}\n")
                if metadata_export:
                    f.write(f"Metadata File: {metadata_export.name}\n")
                f.write("\nFiles in this export:\n")
                f.write(f"1. {export_filename} - Database backup file\n")
                if metadata_export:
                    f.write(f"2. {metadata_export.name} - Backup metadata\n")
                f.write(f"3. {info_filename} - This info file\n")
                f.write("\nTo restore this backup:\n")
                f.write("1. Copy the .db file back to the app's private storage\n")
                f.write("2. Use the restore function in the Chame app\n")
                f.write("3. Select the backup file for restoration\n")
            
            logger.info(f"Backup exported to public storage: {export_path}")
            
            result = {
                'success': True,
                'export_path': str(export_path),
                'info_path': str(info_path),
                'original_backup': backup_filename,
                'exported_filename': export_filename,
                'size': export_path.stat().st_size,
                'message': f"Backup exported to Downloads/ChameBackups: {export_filename}"
            }
            
            if metadata_export:
                result['metadata_path'] = str(metadata_export)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to export backup to public storage: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Export failed: {e}"
            }
    
    def upload_backup_to_server(self, backup_filename: str, server_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Upload backup file and metadata to server via SFTP/SCP
        
        Args:
            backup_filename: Name of the backup file to upload
            server_config: Server configuration
                          {
                              'method': 'sftp'|'scp',
                              'host': 'server.example.com',
                              'port': '22',
                              'username': 'user',
                              'password': 'pass',  # or use key_path
                              'key_path': '/path/to/key',
                              'remote_path': '/backups/',
                          }
                          
        Returns:
            Dict with upload result
        """
        try:
            # Find the backup file
            backup_path = None
            for btype in ["daily", "weekly", "manual"]:
                potential_path = self.backup_dir / btype / backup_filename
                if potential_path.exists():
                    backup_path = potential_path
                    break
            
            if not backup_path:
                raise FileNotFoundError(f"Backup not found: {backup_filename}")
            
            # Get metadata file if it exists
            metadata_path = self.backup_dir / "metadata" / f"{backup_filename}.json"
            
            method = server_config.get('method', 'http').lower()
            
            if method == 'sftp':
                return self._upload_backup_sftp(backup_path, metadata_path, server_config)
            elif method == 'http':
                return self._upload_backup_http(backup_path, metadata_path, server_config)
            elif method == 'scp':
                # SCP not available on Android
                raise RuntimeError(
                    "SCP upload not available on Android. "
                    "Please use HTTP upload method or Export & Share instead."
                )
            else:
                raise ValueError(f"Unsupported upload method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to upload backup to server: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Upload failed: {e}"
            }
    
    def _upload_backup_http(self, backup_path: Path, metadata_path: Path, config: Dict[str, str]) -> Dict[str, Any]:
        """Upload backup via HTTP POST using requests"""
        try:
            try:
                import requests
            except ImportError:
                raise RuntimeError(
                    "requests library is not available. "
                    "HTTP uploads require requests to be installed."
                )
            
            url = config['url']
            auth_header = config.get('auth_header', '')
            
            # Prepare files for upload
            files = {}
            
            # Main backup file
            with open(backup_path, 'rb') as f:
                files['backup'] = (backup_path.name, f.read(), 'application/octet-stream')
            
            # Metadata file if exists
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    files['metadata'] = (metadata_path.name, f.read(), 'application/json')
            
            # Create info file
            info_content = f"""Chame Database Backup Upload
{'=' * 40}
Backup File: {backup_path.name}
Upload Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Upload Method: HTTP POST
Server URL: {url}
File Size: {backup_path.stat().st_size} bytes
"""
            files['info'] = (f"{backup_path.stem}_upload_info.txt", info_content.encode(), 'text/plain')
            
            # Prepare headers
            headers = {}
            if auth_header:
                headers['Authorization'] = auth_header
            
            # Upload files
            response = requests.post(
                url,
                files=files,
                headers=headers,
                timeout=300  # 5 minute timeout
            )
            
            response.raise_for_status()  # Raise exception for HTTP errors
            
            uploaded_files = list(files.keys())
            
            return {
                'success': True,
                'uploaded_files': uploaded_files,
                'server': url,
                'response_status': response.status_code,
                'response_text': response.text[:200] if response.text else '',
                'message': f"Successfully uploaded {len(uploaded_files)} files to {url}"
            }
            
        except ImportError:
            raise RuntimeError("HTTP upload requires requests library")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HTTP upload failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Upload failed: {e}")
    
    def _upload_backup_sftp(self, backup_path: Path, metadata_path: Path, config: Dict[str, str]) -> Dict[str, Any]:
        """Upload backup via SFTP using paramiko"""
        try:
            try:
                import paramiko
            except ImportError:
                raise RuntimeError(
                    "paramiko library is not available. "
                    "SFTP uploads require paramiko to be installed. "
                    "Please use SCP method instead or install paramiko."
                )
            
            host = config['host']
            port = int(config.get('port', '22'))
            username = config['username']
            remote_path = config['remote_path']
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            if 'key_path' in config:
                ssh.connect(host, port=port, username=username, key_filename=config['key_path'])
            else:
                ssh.connect(host, port=port, username=username, password=config['password'])
            
            # Create remote directory if it doesn't exist
            sftp = ssh.open_sftp()
            try:
                sftp.listdir(remote_path)
            except FileNotFoundError:
                # Directory doesn't exist, create it
                sftp.mkdir(remote_path)
            
            # Upload backup file
            remote_backup = f"{remote_path}/{backup_path.name}"
            sftp.put(str(backup_path), remote_backup)
            
            uploaded_files = [remote_backup]
            
            # Upload metadata if it exists
            remote_metadata = None
            if metadata_path.exists():
                remote_metadata = f"{remote_path}/{metadata_path.name}"
                sftp.put(str(metadata_path), remote_metadata)
                uploaded_files.append(remote_metadata)
            
            # Create remote info file
            remote_info = f"{remote_path}/{backup_path.stem}_upload_info.txt"
            info_content = f"""Chame Database Backup Upload
{'=' * 40}
Backup File: {backup_path.name}
Upload Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Upload Method: SFTP
Server: {username}@{host}:{port}
Remote Path: {remote_path}
File Size: {backup_path.stat().st_size} bytes

Uploaded Files:
"""
            for i, file in enumerate(uploaded_files, 1):
                info_content += f"{i}. {file}\n"
            
            # Write info file to remote
            with sftp.file(remote_info, 'w') as f:
                f.write(info_content)
            uploaded_files.append(remote_info)
            
            # Close connections
            sftp.close()
            ssh.close()
            
            return {
                'success': True,
                'method': 'sftp',
                'uploaded_files': uploaded_files,
                'server': f"{username}@{host}:{port}",
                'remote_path': remote_path,
                'message': f"Backup uploaded via SFTP to {username}@{host}:{remote_path}"
            }
            
        except ImportError:
            raise RuntimeError("paramiko library required for SFTP uploads. Install with: pip install paramiko")
        except Exception as e:
            raise RuntimeError(f"SFTP upload failed: {e}")

    def download_backup_from_server(self, server_config: Dict[str, str], remote_filename: str) -> Dict[str, Any]:
        """
        Download backup from server via HTTP or SFTP
        
        Args:
            server_config: Server configuration
                          {
                              'method': 'http'|'sftp',
                              'url': 'http://server.com/download/filename',  # for HTTP
                              'host': 'server.example.com',  # for SFTP
                              'port': '22',
                              'username': 'user',
                              'password': 'pass',
                              'remote_dir': '/backups/',
                          }
            remote_filename: Name of the backup file to download
                          
        Returns:
            Dict with download result including local file path
        """
        try:
            method = server_config.get('method', 'http').lower()
            
            if method == 'http':
                return self._download_backup_http(server_config, remote_filename)
            elif method == 'sftp':
                return self._download_backup_sftp(server_config, remote_filename)
            else:
                raise ValueError(f"Unsupported download method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to download backup from server: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Download failed: {e}"
            }
    
    def _download_backup_http(self, config: Dict[str, str], remote_filename: str) -> Dict[str, Any]:
        """Download backup via HTTP GET using requests"""
        try:
            try:
                import requests
            except ImportError:
                raise RuntimeError(
                    "requests library is not available. "
                    "HTTP downloads require requests to be installed."
                )
            
            # Build download URL
            base_url = config.get('url', '').rstrip('/')
            if '/upload' in base_url:
                base_url = base_url.replace('/upload', '/download')
            
            download_url = f"{base_url}/{remote_filename}"
            auth_header = config.get('auth_header', '')
            
            # Prepare headers
            headers = {}
            if auth_header:
                headers['Authorization'] = auth_header
            
            # Download file
            response = requests.get(
                download_url,
                headers=headers,
                timeout=300,  # 5 minute timeout
                stream=True  # Stream for large files
            )
            
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Save to manual backups directory
            local_filename = f"downloaded_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{remote_filename}"
            local_path = self.backup_dir / "manual" / local_filename
            
            # Write file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = local_path.stat().st_size
            
            return {
                'success': True,
                'local_path': str(local_path),
                'local_filename': local_filename,
                'original_filename': remote_filename,
                'download_url': download_url,
                'file_size': file_size,
                'message': f"Successfully downloaded {remote_filename} ({file_size} bytes)"
            }
            
        except ImportError:
            raise RuntimeError("HTTP download requires requests library")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HTTP download failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}")
    
    def _download_backup_sftp(self, config: Dict[str, str], remote_filename: str) -> Dict[str, Any]:
        """Download backup via SFTP using paramiko"""
        try:
            try:
                import paramiko
            except ImportError:
                raise RuntimeError(
                    "paramiko library is not available. "
                    "SFTP downloads require paramiko to be installed. "
                    "Please use HTTP download method instead."
                )
                
            # Connect to server
            transport = paramiko.Transport((config['host'], int(config.get('port', 22))))
            
            if config.get('key_file'):
                # Key authentication
                private_key = paramiko.RSAKey.from_private_key_file(config['key_file'])
                transport.connect(username=config['username'], pkey=private_key)
            else:
                # Password authentication
                transport.connect(username=config['username'], password=config.get('password', ''))
            
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Download file
            remote_dir = config.get('remote_dir', '/tmp')
            remote_path = f"{remote_dir}/{remote_filename}"
            
            # Save to manual backups directory
            local_filename = f"downloaded_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{remote_filename}"
            local_path = self.backup_dir / "manual" / local_filename
            
            sftp.get(remote_path, str(local_path))
            
            sftp.close()
            transport.close()
            
            file_size = local_path.stat().st_size
            
            return {
                'success': True,
                'local_path': str(local_path),
                'local_filename': local_filename,
                'original_filename': remote_filename,
                'remote_path': remote_path,
                'server': f"{config['host']}:{config.get('port', 22)}",
                'file_size': file_size,
                'message': f"Successfully downloaded {remote_filename} via SFTP ({file_size} bytes)"
            }
            
        except ImportError:
            raise RuntimeError("SFTP download requires paramiko library")
        except Exception as e:
            raise RuntimeError(f"SFTP download failed: {e}")

    def list_server_backups(self, server_config: Dict[str, str]) -> Dict[str, Any]:
        """
        List all available backup files on the server
        
        Args:
            server_config: Server configuration
                          {
                              'method': 'http'|'sftp',
                              'url': 'http://server.com/list',  # for HTTP
                              'host': 'server.example.com',    # for SFTP
                              'port': '22',
                              'username': 'user',
                              'password': 'pass',
                              'remote_dir': '/backups/',
                          }
                          
        Returns:
            Dict with list of available backup files and their details
        """
        try:
            method = server_config.get('method', 'http').lower()
            
            if method == 'http':
                return self._list_server_backups_http(server_config)
            elif method == 'sftp':
                return self._list_server_backups_sftp(server_config)
            else:
                raise ValueError(f"Unsupported list method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to list server backups: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"List failed: {e}",
                'files': []
            }
    
    def _list_server_backups_http(self, config: Dict[str, str]) -> Dict[str, Any]:
        """List backups via HTTP GET to /list endpoint"""
        try:
            try:
                import requests
            except ImportError:
                raise RuntimeError(
                    "requests library is not available. "
                    "HTTP listing requires requests to be installed."
                )
            
            # Build list URL - use provided URL or construct from base
            if 'url' in config:
                list_url = config['url']
                # If URL ends with /download, replace with /list
                if list_url.endswith('/download'):
                    list_url = list_url[:-9] + '/list'
                elif not list_url.endswith('/list'):
                    # Add /list if not present
                    list_url = list_url.rstrip('/') + '/list'
            else:
                # Fallback to default construction
                base_url = f"http://{config.get('host', 'localhost')}:{config.get('port', 5050)}"
                list_url = f"{base_url}/list"
            
            logger.info(f"Listing backups from: {list_url}")
            
            # Make request
            response = requests.get(list_url, timeout=30)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if data.get('success', False):
                files = data.get('files', [])
                return {
                    'success': True,
                    'files': files,
                    'total_count': data.get('total_count', len(files)),
                    'server_info': {
                        'url': list_url,
                        'timestamp': data.get('timestamp'),
                        'upload_dir': data.get('upload_dir')
                    },
                    'message': f"Found {len(files)} backup files on server"
                }
            else:
                raise RuntimeError(f"Server returned error: {data.get('error', 'Unknown error')}")
            
        except Exception as e:
            raise RuntimeError(f"HTTP list failed: {e}")
    
    def _list_server_backups_sftp(self, config: Dict[str, str]) -> Dict[str, Any]:
        """List backups via SFTP directory listing"""
        try:
            try:
                import paramiko
            except ImportError:
                raise RuntimeError(
                    "paramiko library is not available. "
                    "SFTP listing requires paramiko to be installed. "
                    "Please use HTTP list method instead."
                )
                
            # Connect to server
            transport = paramiko.Transport((config['host'], int(config.get('port', 22))))
            
            if config.get('key_file'):
                # Key authentication
                private_key = paramiko.RSAKey.from_private_key_file(config['key_file'])
                transport.connect(username=config['username'], pkey=private_key)
            else:
                # Password authentication
                transport.connect(username=config['username'], password=config.get('password', ''))
            
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # List files in remote directory
            remote_dir = config.get('remote_dir', '/tmp')
            file_list = sftp.listdir_attr(remote_dir)
            
            # Filter and format backup files
            backup_files = []
            allowed_extensions = {'.db', '.sqlite', '.sqlite3', '.json', '.txt'}
            
            for file_attr in file_list:
                if any(file_attr.filename.lower().endswith(ext) for ext in allowed_extensions):
                    backup_files.append({
                        'filename': file_attr.filename,
                        'size': file_attr.st_size,
                        'modified': datetime.datetime.fromtimestamp(file_attr.st_mtime).isoformat(),
                        'extension': Path(file_attr.filename).suffix.lower()
                    })
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            
            sftp.close()
            transport.close()
            
            return {
                'success': True,
                'files': backup_files,
                'total_count': len(backup_files),
                'server_info': {
                    'host': config['host'],
                    'port': config.get('port', 22),
                    'remote_dir': remote_dir
                },
                'message': f"Found {len(backup_files)} backup files on SFTP server"
            }
            
        except ImportError:
            raise RuntimeError("SFTP listing requires paramiko library")
        except Exception as e:
            raise RuntimeError(f"SFTP listing failed: {e}")

    def import_backup_from_share(self, shared_file_path: str) -> Dict[str, Any]:
        """
        Import backup file from Android share/file picker
        
        Args:
            shared_file_path: Path to the shared backup file
                          
        Returns:
            Dict with import result including new local file path
        """
        try:
            shared_path = Path(shared_file_path)
            
            if not shared_path.exists():
                raise FileNotFoundError(f"Shared file not found: {shared_file_path}")
            
            # Validate file extension
            if shared_path.suffix.lower() not in ['.db', '.sqlite', '.sqlite3']:
                raise ValueError(f"Invalid backup file type: {shared_path.suffix}")
            
            # Create new filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            local_filename = f"imported_{timestamp}_{shared_path.name}"
            local_path = self.backup_dir / "manual" / local_filename
            
            # Copy file to backups directory
            shutil.copy2(shared_file_path, local_path)
            
            file_size = local_path.stat().st_size
            
            # Create metadata
            metadata = BackupMetadata(
                timestamp=datetime.datetime.now().isoformat(),
                backup_type="manual",
                database_version="imported",
                file_size=file_size,
                checksum=self._calculate_checksum(local_path),
                description=f"Imported from shared file: {shared_path.name}",
                created_by="import"
            )
            
            # Save metadata
            metadata_path = self.backup_dir / "metadata" / f"{local_filename}.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            return {
                'success': True,
                'local_path': str(local_path),
                'local_filename': local_filename,
                'original_filename': shared_path.name,
                'file_size': file_size,
                'metadata_path': str(metadata_path),
                'message': f"Successfully imported {shared_path.name} as {local_filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to import backup from share: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Import failed: {e}"
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

# Convenience functions for backup export
def export_backup_to_public(backup_filename: str) -> Dict[str, Any]:
    """Export backup to Android public storage for sharing"""
    manager = DatabaseBackupManager()
    return manager.export_backup_to_public(backup_filename)

def upload_backup_to_server(backup_filename: str, server_config: Dict[str, str]) -> Dict[str, Any]:
    """Upload backup to server via HTTP/SFTP"""
    manager = DatabaseBackupManager()
    return manager.upload_backup_to_server(backup_filename, server_config)

def download_backup_from_server(server_config: Dict[str, str], remote_filename: str) -> Dict[str, Any]:
    """Download backup from server via HTTP/SFTP"""
    manager = DatabaseBackupManager()
    return manager.download_backup_from_server(server_config, remote_filename)

def import_backup_from_share(shared_file_path: str) -> Dict[str, Any]:
    """Import backup file from Android share/file picker"""
    manager = DatabaseBackupManager()
    return manager.import_backup_from_share(shared_file_path)

def list_server_backups(server_config: Dict[str, str]) -> Dict[str, Any]:
    """List all available backup files on the server"""
    manager = DatabaseBackupManager()
    return manager.list_server_backups(server_config)
