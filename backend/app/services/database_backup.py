# database_backup.py
# Comprehensive database backup and restore functionality

from __future__ import annotations

import os
import shutil
import sqlite3
import json
import datetime
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from chame_app.database import resolve_database_path

logger = logging.getLogger(__name__)

# Constants
DB_FILENAME = "kassensystem.db"
FILTERED_TEXT = "[FILTERED]"
GET_TABLES_SQL = "SELECT name FROM sqlite_master WHERE type='table'"
SENSITIVE_FIELDS = {"password_hash", "password", "secret", "token", "api_key"}
NULL_AS_SALESMAN_ID = "NULL AS salesman_id"

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
    
    def __init__(self, backup_dir: Optional[str] = None, database_path: Optional[str] = None):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups. If None, uses environment or default.
            database_path: Explicit database file path. If None, auto-detects the active database.
        """
        self.backup_dir = self._get_backup_directory(backup_dir)
        self.database_path = Path(database_path) if database_path else None
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "daily").mkdir(exist_ok=True)
        (self.backup_dir / "weekly").mkdir(exist_ok=True)
        (self.backup_dir / "manual").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
        (self.backup_dir / "exports").mkdir(exist_ok=True)
        (self.backup_dir / "reports").mkdir(exist_ok=True)
        
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
        if self.database_path:
            return self.database_path
        return resolve_database_path()
    
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

    def export_data(self, format: str = "json", include_sensitive: bool = False) -> Dict[str, Any]:
        """Export database contents in JSON, CSV, or SQL format."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_root = self.backup_dir / "exports"

        try:
            normalized_format = format.lower()
            if normalized_format == "json":
                export_path = export_root / f"chame_export_json_{timestamp}.json"
                payload = self._build_export_payload(include_sensitive=include_sensitive)
                with open(export_path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2, ensure_ascii=False)

                return {
                    'success': True,
                    'export_path': str(export_path),
                    'format': normalized_format,
                    'message': f"JSON export created: {export_path.name}"
                }

            if normalized_format == "csv":
                export_dir = export_root / f"chame_export_csv_{timestamp}"
                export_dir.mkdir(parents=True, exist_ok=True)
                exported_files = self._export_csv_bundle(export_dir, include_sensitive=include_sensitive)

                return {
                    'success': True,
                    'export_path': str(export_dir),
                    'files': exported_files,
                    'format': normalized_format,
                    'message': f"CSV export created: {export_dir.name}"
                }

            if normalized_format == "sql":
                export_path = export_root / f"chame_export_sql_{timestamp}.sql"
                self._export_sql_dump(export_path)

                return {
                    'success': True,
                    'export_path': str(export_path),
                    'format': normalized_format,
                    'message': f"SQL export created: {export_path.name}"
                }

            raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.exception("Failed to export data in %s format", format)
            return {
                'success': False,
                'error': str(e),
                'message': f"Export failed: {e}"
            }

    def generate_database_report(
        self,
        include_sensitive: bool = False,
        trend_days: int = 30,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a PDF report documenting the database schema and recent activity."""
        reportlab_dependencies = self._load_reportlab_dependencies()
        if not reportlab_dependencies['success']:
            return {
                'success': False,
                'error': reportlab_dependencies['error'],
                'message': "PDF reporting requires reportlab. Install it with: pip install reportlab"
            }

        try:
            report_data = self._collect_report_data(
                include_sensitive=include_sensitive,
                trend_days=trend_days,
            )
            pdf_path = self._resolve_report_path(output_path)
            doc = self._create_pdf_document(pdf_path, reportlab_dependencies)
            story = self._build_database_report_story(
                report_data=report_data,
                trend_days=trend_days,
                reportlab_dependencies=reportlab_dependencies,
            )
            doc.build(story)
            logger.info(f"Database PDF report created: {pdf_path}")

            return {
                'success': True,
                'report_path': str(pdf_path),
                'format': 'pdf',
                'generated_at': report_data['generated_at'],
                'message': f"Database report created: {pdf_path.name}"
            }

        except Exception as e:
            logger.exception("Failed to generate database report")
            return {
                'success': False,
                'error': str(e),
                'message': f"PDF report generation failed: {e}"
            }

    def _load_reportlab_dependencies(self) -> Dict[str, Any]:
        """Import ReportLab lazily so the rest of the backup tools stay usable without it."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            return {
                'success': True,
                'colors': colors,
                'A4': A4,
                'ParagraphStyle': ParagraphStyle,
                'getSampleStyleSheet': getSampleStyleSheet,
                'mm': mm,
                'PageBreak': PageBreak,
                'Paragraph': Paragraph,
                'SimpleDocTemplate': SimpleDocTemplate,
                'Spacer': Spacer,
                'Table': Table,
                'TableStyle': TableStyle,
            }
        except ImportError as e:
            return {
                'success': False,
                'error': str(e),
            }

    def _resolve_report_path(self, output_path: Optional[str]) -> Path:
        """Resolve the target path for a generated PDF report."""
        if output_path:
            pdf_path = Path(output_path)
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            return pdf_path

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.backup_dir / "reports" / f"chame_database_report_{timestamp}.pdf"

    def _create_pdf_document(self, pdf_path: Path, reportlab_dependencies: Dict[str, Any]):
        """Create the ReportLab document instance."""
        return reportlab_dependencies['SimpleDocTemplate'](
            str(pdf_path),
            pagesize=reportlab_dependencies['A4'],
            leftMargin=14 * reportlab_dependencies['mm'],
            rightMargin=14 * reportlab_dependencies['mm'],
            topMargin=16 * reportlab_dependencies['mm'],
            bottomMargin=16 * reportlab_dependencies['mm'],
        )

    def _build_database_report_story(
        self,
        report_data: Dict[str, Any],
        trend_days: int,
        reportlab_dependencies: Dict[str, Any],
    ) -> List[Any]:
        """Build the sequence of PDF elements for the database report."""
        styles = reportlab_dependencies['getSampleStyleSheet']()
        small_style = reportlab_dependencies['ParagraphStyle'](
            "ReportSmall",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=10,
        )

        story: List[Any] = []
        self._append_report_header(story, report_data, styles, reportlab_dependencies)
        self._append_executive_summary(story, report_data, trend_days, styles, reportlab_dependencies)
        self._append_activity_section(story, report_data, styles, reportlab_dependencies)
        self._append_recent_changes_section(story, report_data, styles, reportlab_dependencies)
        self._append_schema_section(story, report_data, styles, small_style, reportlab_dependencies)
        self._append_backup_section(story, report_data, styles, reportlab_dependencies)
        return story

    def _append_report_header(self, story: List[Any], report_data: Dict[str, Any], styles, reportlab_dependencies: Dict[str, Any]):
        """Append the report title and metadata block."""
        paragraph = reportlab_dependencies['Paragraph']
        spacer = reportlab_dependencies['Spacer']
        story.append(paragraph("Chame Database Documentation Report", styles["Title"]))
        story.append(spacer(1, 8))
        story.append(paragraph(
            f"Generated: {report_data['generated_at']}<br/>"
            f"Database: {report_data['database_path']}<br/>"
            f"Schema version: {report_data['database_version']}<br/>"
            f"Integrity check: {'OK' if report_data['integrity_ok'] else 'FAILED'}",
            styles["BodyText"],
        ))
        story.append(spacer(1, 10))

    def _append_executive_summary(
        self,
        story: List[Any],
        report_data: Dict[str, Any],
        trend_days: int,
        styles,
        reportlab_dependencies: Dict[str, Any],
    ):
        """Append the summary, entity counts, and financial snapshot."""
        paragraph = reportlab_dependencies['Paragraph']
        spacer = reportlab_dependencies['Spacer']
        table = reportlab_dependencies['Table']
        table_style = reportlab_dependencies['TableStyle']
        colors = reportlab_dependencies['colors']

        story.append(paragraph("Executive Summary", styles["Heading2"]))
        summary_rows = [
            ["Metric", "Value"],
            ["Database size", report_data['database_size']],
            ["Tables documented", str(len(report_data['schema']))],
            ["Recent backups", str(len(report_data['recent_backups']))],
            ["Trend window", f"Last {trend_days} day(s)"],
        ]
        story.append(self._build_pdf_table(table, table_style, colors, summary_rows, [120, 360]))
        story.append(spacer(1, 10))

        story.append(paragraph("Current Snapshot", styles["Heading2"]))
        snapshot_rows = [["Entity", "Count"]]
        for row in report_data['table_counts']:
            snapshot_rows.append([row['table'], str(row['count'])])
        story.append(self._build_pdf_table(table, table_style, colors, snapshot_rows, [220, 120]))
        story.append(spacer(1, 10))

        if report_data['bank_summary']:
            story.append(paragraph("Financial Snapshot", styles["Heading2"]))
            bank_rows = [["Field", "Value"]]
            for key, value in report_data['bank_summary'].items():
                bank_rows.append([key.replace("_", " ").title(), str(value)])
            story.append(self._build_pdf_table(table, table_style, colors, bank_rows, [220, 180]))
            story.append(spacer(1, 10))

    def _append_activity_section(self, story: List[Any], report_data: Dict[str, Any], styles, reportlab_dependencies: Dict[str, Any]):
        """Append grouped activity trends."""
        paragraph = reportlab_dependencies['Paragraph']
        spacer = reportlab_dependencies['Spacer']
        table = reportlab_dependencies['Table']
        table_style = reportlab_dependencies['TableStyle']
        colors = reportlab_dependencies['colors']

        story.append(paragraph("Activity Trends", styles["Heading2"]))
        if not report_data['activity_trends']:
            story.append(paragraph("No activity tables were available in this database.", styles["BodyText"]))
            story.append(spacer(1, 8))
            return

        for trend_name, rows in report_data['activity_trends'].items():
            story.append(paragraph(trend_name.replace("_", " ").title(), styles["Heading3"]))
            story.append(self._build_data_table_for_pdf(table, table_style, colors, rows, empty_message="No activity available"))
            story.append(spacer(1, 8))

    def _append_recent_changes_section(self, story: List[Any], report_data: Dict[str, Any], styles, reportlab_dependencies: Dict[str, Any]):
        """Append recent row-level activity samples."""
        paragraph = reportlab_dependencies['Paragraph']
        spacer = reportlab_dependencies['Spacer']
        page_break = reportlab_dependencies['PageBreak']
        table = reportlab_dependencies['Table']
        table_style = reportlab_dependencies['TableStyle']
        colors = reportlab_dependencies['colors']

        story.append(page_break())
        story.append(paragraph("Recent Changes", styles["Heading2"]))
        for section_name, rows in report_data['recent_changes'].items():
            story.append(paragraph(section_name.replace("_", " ").title(), styles["Heading3"]))
            story.append(self._build_data_table_for_pdf(table, table_style, colors, rows, empty_message="No rows available"))
            story.append(spacer(1, 8))

    def _append_schema_section(self, story: List[Any], report_data: Dict[str, Any], styles, small_style, reportlab_dependencies: Dict[str, Any]):
        """Append per-table schema documentation."""
        paragraph = reportlab_dependencies['Paragraph']
        spacer = reportlab_dependencies['Spacer']
        page_break = reportlab_dependencies['PageBreak']
        table = reportlab_dependencies['Table']
        table_style = reportlab_dependencies['TableStyle']
        colors = reportlab_dependencies['colors']

        story.append(page_break())
        story.append(paragraph("Schema Documentation", styles["Heading2"]))
        for table_schema in report_data['schema']:
            story.append(paragraph(table_schema['table'], styles["Heading3"]))
            story.append(paragraph(
                f"Rows: {table_schema['row_count']} | Columns: {len(table_schema['columns'])}",
                small_style,
            ))
            schema_rows = [["Column", "Type", "PK", "Required", "Default", "Foreign Keys"]]
            for column in table_schema['columns']:
                schema_rows.append([
                    column['name'],
                    column['type'],
                    "yes" if column['primary_key'] else "",
                    "yes" if column['not_null'] else "",
                    column['default'] or "",
                    ", ".join(column['foreign_keys']) if column['foreign_keys'] else "",
                ])
            story.append(self._build_pdf_table(table, table_style, colors, schema_rows, font_size=7.5))
            story.append(spacer(1, 8))

    def _append_backup_section(self, story: List[Any], report_data: Dict[str, Any], styles, reportlab_dependencies: Dict[str, Any]):
        """Append the recent backup inventory section."""
        if not report_data['recent_backups']:
            return

        paragraph = reportlab_dependencies['Paragraph']
        page_break = reportlab_dependencies['PageBreak']
        table = reportlab_dependencies['Table']
        table_style = reportlab_dependencies['TableStyle']
        colors = reportlab_dependencies['colors']

        story.append(page_break())
        story.append(paragraph("Recent Backups", styles["Heading2"]))
        backup_rows = [["Filename", "Type", "Created", "Size MB", "Description"]]
        for backup in report_data['recent_backups']:
            backup_rows.append([
                backup['filename'],
                backup['backup_type'],
                backup['created_at'],
                backup['size_mb'],
                self._truncate_for_pdf(backup['description'], limit=90),
            ])
        story.append(self._build_pdf_table(table, table_style, colors, backup_rows, font_size=7.5))

    def _build_data_table_for_pdf(self, table_cls, table_style_cls, colors_module, rows: List[Dict[str, Any]], empty_message: str):
        """Build a PDF table from a list of dictionaries."""
        if not rows:
            table_rows = [["message"], [empty_message]]
        else:
            table_rows = [list(rows[0].keys())]
            for row in rows:
                table_rows.append([self._truncate_for_pdf(value) for value in row.values()])
        return self._build_pdf_table(table_cls, table_style_cls, colors_module, table_rows)

    def _build_export_payload(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Build a serializable snapshot of the current database."""
        db_path = self._get_database_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.cursor()
            tables = self._get_user_tables(cursor)
            payload = {
                'metadata': {
                    'generated_at': datetime.datetime.now().isoformat(),
                    'database_path': str(db_path),
                    'database_version': self._get_database_version(),
                    'integrity_ok': self._verify_database_integrity(db_path),
                    'table_count': len(tables),
                },
                'tables': {},
            }

            for table_name in tables:
                rows = cursor.execute(f'SELECT * FROM "{table_name}"').fetchall()
                payload['tables'][table_name] = [
                    self._sanitize_row(dict(row), include_sensitive=include_sensitive)
                    for row in rows
                ]

            return payload
        finally:
            conn.close()

    def _export_csv_bundle(self, export_dir: Path, include_sensitive: bool = False) -> List[str]:
        """Export each table into its own CSV file."""
        db_path = self._get_database_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.cursor()
            exported_files = []

            for table_name in self._get_user_tables(cursor):
                rows = cursor.execute(f'SELECT * FROM "{table_name}"').fetchall()
                if rows:
                    fieldnames = list(rows[0].keys())
                else:
                    fieldnames = [column['name'] for column in self._get_table_schema(cursor, table_name)['columns']]

                csv_path = export_dir / f"{table_name}.csv"
                with open(csv_path, 'w', newline='', encoding='utf-8') as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(self._sanitize_row(dict(row), include_sensitive=include_sensitive))

                exported_files.append(csv_path.name)

            manifest_path = export_dir / "manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as handle:
                json.dump({
                    'generated_at': datetime.datetime.now().isoformat(),
                    'database_version': self._get_database_version(),
                    'files': exported_files,
                }, handle, indent=2)
            exported_files.append(manifest_path.name)

            return exported_files
        finally:
            conn.close()

    def _export_sql_dump(self, export_path: Path):
        """Export the database as a SQLite SQL dump."""
        db_path = self._get_database_path()
        conn = sqlite3.connect(str(db_path))

        try:
            with open(export_path, 'w', encoding='utf-8') as handle:
                for line in conn.iterdump():
                    handle.write(f"{line}\n")
        finally:
            conn.close()

    def _collect_report_data(self, include_sensitive: bool, trend_days: int) -> Dict[str, Any]:
        """Collect the structured data used by the PDF generator."""
        db_path = self._get_database_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.cursor()
            schema = [self._get_table_schema(cursor, table_name) for table_name in self._get_user_tables(cursor)]
            table_counts = [
                {'table': table_schema['table'], 'count': table_schema['row_count']}
                for table_schema in schema
            ]

            return {
                'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
                'database_path': str(db_path),
                'database_version': self._get_database_version(),
                'database_size': f"{db_path.stat().st_size / (1024 * 1024):.2f} MB" if db_path.exists() else "0.00 MB",
                'integrity_ok': self._verify_database_integrity(db_path),
                'schema': schema,
                'table_counts': table_counts,
                'bank_summary': self._get_bank_summary(cursor),
                'activity_trends': self._get_activity_trends(cursor, trend_days),
                'recent_changes': self._get_recent_changes(cursor, include_sensitive=include_sensitive),
                'recent_backups': self._get_recent_backup_summary(),
            }
        finally:
            conn.close()

    def _get_user_tables(self, cursor: sqlite3.Cursor) -> List[str]:
        """Return all non-SQLite internal tables."""
        rows = cursor.execute(GET_TABLES_SQL).fetchall()
        return sorted([
            row[0]
            for row in rows
            if row[0] and not row[0].startswith("sqlite_")
        ])

    def _get_table_schema(self, cursor: sqlite3.Cursor, table_name: str) -> Dict[str, Any]:
        """Return schema information for a table."""
        columns = cursor.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        foreign_keys = cursor.execute(f'PRAGMA foreign_key_list("{table_name}")').fetchall()
        fk_map: Dict[str, List[str]] = {}
        for fk in foreign_keys:
            from_column = fk[3]
            fk_map.setdefault(from_column, []).append(f"{fk[2]}.{fk[4]}")

        row_count = cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        return {
            'table': table_name,
            'row_count': row_count,
            'columns': [
                {
                    'name': column[1],
                    'type': column[2],
                    'not_null': bool(column[3]),
                    'default': None if column[4] is None else str(column[4]),
                    'primary_key': bool(column[5]),
                    'foreign_keys': fk_map.get(column[1], []),
                }
                for column in columns
            ],
        }

    def _get_column_names(self, cursor: sqlite3.Cursor, table_name: str) -> set[str]:
        """Return the available column names for a table."""
        return {
            column['name']
            for column in self._get_table_schema(cursor, table_name)['columns']
        }

    def _get_bank_summary(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """Return a snapshot of the bank table if present."""
        tables = set(self._get_user_tables(cursor))
        if "bank" not in tables:
            return {}

        bank_columns = self._get_column_names(cursor, 'bank')
        row_data = self._get_bank_row_data(cursor, bank_columns)
        if not row_data:
            return {}

        return self._build_bank_summary_from_row(row_data, bank_columns)

    def _get_bank_row_data(self, cursor: sqlite3.Cursor, bank_columns: set[str]) -> Dict[str, Any]:
        """Fetch only the bank columns that exist in the current schema."""
        selected_columns = [
            column for column in [
                'account_id',
                'total_balance',
                'customer_funds',
                'revenue_total',
                'costs_total',
                'profit_total',
                'product_value',
                'ingredient_value',
                'revenue_funds',
                'costs_reserved',
                'profit_retained',
            ]
            if column in bank_columns
        ]
        if not selected_columns:
            return {}

        row = cursor.execute(
            f"SELECT {', '.join(selected_columns)} FROM bank LIMIT 1"
        ).fetchone()
        return dict(row) if row else {}

    def _build_bank_summary_from_row(self, row_data: Dict[str, Any], bank_columns: set[str]) -> Dict[str, Any]:
        """Normalize legacy and current bank schemas into one summary shape."""
        total_balance = float(row_data.get('total_balance') or 0)
        customer_funds = float(row_data.get('customer_funds') or 0)
        revenue_total = float(row_data.get('revenue_total') or 0)
        costs_total = float(row_data.get('costs_total') or 0)
        profit_total = self._resolve_profit_total(row_data, bank_columns, revenue_total, costs_total)

        return {
            'account_id': row_data.get('account_id', 1),
            'total_balance': round(total_balance, 2),
            'customer_funds': round(customer_funds, 2),
            'business_balance': round(total_balance - customer_funds, 2),
            'revenue_total': round(revenue_total, 2),
            'costs_total': round(costs_total, 2),
            'profit_total': round(float(profit_total or 0), 2),
            'product_value': round(float(row_data.get('product_value') or 0), 2),
            'ingredient_value': round(float(row_data.get('ingredient_value') or 0), 2),
            'legacy_revenue_funds': round(float(row_data.get('revenue_funds') or 0), 2),
            'legacy_costs_reserved': round(float(row_data.get('costs_reserved') or 0), 2),
            'legacy_profit_retained': round(float(row_data.get('profit_retained') or 0), 2),
        }

    def _resolve_profit_total(
        self,
        row_data: Dict[str, Any],
        bank_columns: set[str],
        revenue_total: float,
        costs_total: float,
    ) -> float:
        """Compute profit_total even for older schemas that do not persist it."""
        if row_data.get('profit_total') is not None:
            return float(row_data['profit_total'] or 0)
        if {'revenue_total', 'costs_total'}.issubset(bank_columns):
            return revenue_total - costs_total
        return float(row_data.get('profit_retained') or 0)

    def _get_activity_trends(self, cursor: sqlite3.Cursor, trend_days: int) -> Dict[str, List[Dict[str, Any]]]:
        """Return grouped recent activity for major history tables."""
        tables = set(self._get_user_tables(cursor))
        trends: Dict[str, List[Dict[str, Any]]] = {}
        window_days = max(int(trend_days), 1)
        cutoff = (datetime.date.today() - datetime.timedelta(days=window_days - 1)).isoformat()

        queries = {
            'sales': (
                "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count, ROUND(COALESCE(SUM(total_price), 0), 2) AS total_amount "
                "FROM sales WHERE substr(timestamp, 1, 10) >= ? GROUP BY substr(timestamp, 1, 10) ORDER BY day DESC"
            ),
            'transactions': (
                "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count, ROUND(COALESCE(SUM(amount), 0), 2) AS total_amount "
                "FROM transactions WHERE substr(timestamp, 1, 10) >= ? GROUP BY substr(timestamp, 1, 10) ORDER BY day DESC"
            ),
            'bank_transactions': (
                "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count, ROUND(COALESCE(SUM(amount), 0), 2) AS total_amount "
                "FROM bank_transactions WHERE substr(timestamp, 1, 10) >= ? GROUP BY substr(timestamp, 1, 10) ORDER BY day DESC"
            ),
            'stock_history': (
                "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count, ROUND(COALESCE(SUM(amount), 0), 2) AS total_amount "
                "FROM stock_history WHERE substr(timestamp, 1, 10) >= ? GROUP BY substr(timestamp, 1, 10) ORDER BY day DESC"
            ),
        }

        for table_name, query in queries.items():
            if table_name not in tables:
                continue
            rows = cursor.execute(query, (cutoff,)).fetchall()
            trends[table_name] = [dict(row) for row in rows]

        return trends

    def _get_recent_changes(self, cursor: sqlite3.Cursor, include_sensitive: bool) -> Dict[str, List[Dict[str, Any]]]:
        """Return recent row-level activity for key history tables."""
        tables = set(self._get_user_tables(cursor))
        recent: Dict[str, List[Dict[str, Any]]] = {}

        if {'sales', 'users', 'products'}.issubset(tables):
            recent['sales'] = self._get_recent_sales(cursor)

        if {'transactions', 'users'}.issubset(tables):
            recent['transactions'] = self._get_recent_transactions(cursor, include_sensitive)

        if 'bank_transactions' in tables:
            recent['bank_transactions'] = self._get_recent_bank_transactions(cursor)

        if {'stock_history', 'ingredients'}.issubset(tables):
            recent['stock_history'] = self._get_recent_stock_history(cursor)

        return recent

    def _get_recent_sales(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        """Return recent sales with compatibility for older schemas."""
        sales_columns = self._get_column_names(cursor, 'sales')
        consumer_column = 'consumer_id' if 'consumer_id' in sales_columns else 'user_id'
        donator_expression = "COALESCE(donator.name, '') AS donator" if 'donator_id' in sales_columns else "'' AS donator"
        salesman_expression = 's.salesman_id' if 'salesman_id' in sales_columns else NULL_AS_SALESMAN_ID
        toast_round_expression = 's.toast_round_id' if 'toast_round_id' in sales_columns else 'NULL AS toast_round_id'
        rows = cursor.execute(
            f"SELECT s.sale_id, s.timestamp, COALESCE(consumer.name, s.{consumer_column}) AS consumer, "
            f"{donator_expression}, COALESCE(product.name, s.product_id) AS product, "
            f"s.quantity, ROUND(s.total_price, 2) AS total_price, {salesman_expression}, {toast_round_expression} "
            "FROM sales s "
            f"LEFT JOIN users consumer ON consumer.user_id = s.{consumer_column} "
            + ("LEFT JOIN users donator ON donator.user_id = s.donator_id " if 'donator_id' in sales_columns else "")
            + "LEFT JOIN products product ON product.product_id = s.product_id "
            "ORDER BY s.sale_id DESC LIMIT 10"
        ).fetchall()
        return [dict(row) for row in rows]

    def _get_recent_transactions(self, cursor: sqlite3.Cursor, include_sensitive: bool) -> List[Dict[str, Any]]:
        """Return recent user transactions with compatibility for older schemas."""
        transaction_columns = self._get_column_names(cursor, 'transactions')
        transaction_comment = 't.comment' if 'comment' in transaction_columns else 'NULL AS comment'
        transaction_salesman = 't.salesman_id' if 'salesman_id' in transaction_columns else NULL_AS_SALESMAN_ID
        rows = cursor.execute(
            f"SELECT t.transaction_id, t.timestamp, COALESCE(user.name, t.user_id) AS user, t.type, "
            f"ROUND(t.amount, 2) AS amount, {transaction_comment}, {transaction_salesman} "
            "FROM transactions t "
            "LEFT JOIN users user ON user.user_id = t.user_id "
            "ORDER BY t.transaction_id DESC LIMIT 10"
        ).fetchall()
        return [self._sanitize_row(dict(row), include_sensitive=include_sensitive) for row in rows]

    def _get_recent_bank_transactions(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        """Return recent bank transactions with compatibility for older schemas."""
        bank_transaction_columns = self._get_column_names(cursor, 'bank_transactions')
        description_expression = 'description' if 'description' in bank_transaction_columns else 'NULL AS description'
        salesman_expression = 'salesman_id' if 'salesman_id' in bank_transaction_columns else NULL_AS_SALESMAN_ID
        rows = cursor.execute(
            f"SELECT transaction_id, timestamp, type, ROUND(amount, 2) AS amount, {description_expression}, {salesman_expression} "
            "FROM bank_transactions ORDER BY transaction_id DESC LIMIT 10"
        ).fetchall()
        return [dict(row) for row in rows]

    def _get_recent_stock_history(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        """Return recent stock history rows."""
        rows = cursor.execute(
            "SELECT sh.history_id, sh.timestamp, COALESCE(i.name, sh.ingredient_id) AS ingredient, "
            "ROUND(sh.amount, 2) AS amount, sh.comment "
            "FROM stock_history sh "
            "LEFT JOIN ingredients i ON i.ingredient_id = sh.ingredient_id "
            "ORDER BY sh.history_id DESC LIMIT 10"
        ).fetchall()
        return [dict(row) for row in rows]

    def _get_recent_backup_summary(self) -> List[Dict[str, Any]]:
        """Return the most recent backup metadata in a compact shape."""
        summary = []
        for backup in self.list_backups()[:10]:
            summary.append({
                'filename': backup['filename'],
                'backup_type': backup['backup_type'],
                'created_at': backup['created_at'],
                'size_mb': f"{backup['size'] / (1024 * 1024):.2f}",
                'description': backup.get('description', ''),
            })
        return summary

    def _sanitize_row(self, row: Dict[str, Any], include_sensitive: bool) -> Dict[str, Any]:
        """Filter sensitive fields from row-like dictionaries."""
        if include_sensitive:
            return row

        sanitized = {}
        for key, value in row.items():
            if str(key).lower() in SENSITIVE_FIELDS:
                sanitized[key] = FILTERED_TEXT
            else:
                sanitized[key] = value
        return sanitized

    def _truncate_for_pdf(self, value: Any, limit: int = 60) -> str:
        """Normalize PDF cell values so wide content does not break layout."""
        text = "" if value is None else str(value)
        if len(text) <= limit:
            return text
        return f"{text[:limit - 3]}..."

    def _build_pdf_table(
        self,
        table_cls,
        table_style_cls,
        colors_module,
        rows: List[List[Any]],
        column_widths: Optional[List[int]] = None,
        font_size: float = 8.0,
    ):
        """Create a consistently styled report table."""
        normalized_rows = [[self._truncate_for_pdf(cell, limit=90) for cell in row] for row in rows]
        table = table_cls(normalized_rows, colWidths=column_widths, repeatRows=1)
        table.setStyle(table_style_cls([
            ('BACKGROUND', (0, 0), (-1, 0), colors_module.HexColor('#dbe7f3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors_module.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('GRID', (0, 0), (-1, -1), 0.25, colors_module.HexColor('#a5b7c9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors_module.white, colors_module.HexColor('#f7fafc')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return table
    
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
