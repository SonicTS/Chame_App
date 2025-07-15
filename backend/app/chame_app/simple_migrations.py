# simple_migrations.py
# A basic migration system that works in both desktop and mobile environments
# without requiring Alembic

from sqlalchemy import text, inspect
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Firebase logging support
try:
    from utils.firebase_logger import log_to_firebase
    FIREBASE_LOGGING_AVAILABLE = True
except ImportError:
    FIREBASE_LOGGING_AVAILABLE = False
    
    def log_to_firebase(level, message, **metadata):
        """Fallback when Firebase l                print(f"📦 [SimpleMigrations] Running advanced migration: {migration_name}")
                log_to_firebase("INFO", f"Applying advanced migration: {migration_name}",
                               migration_name=migration_name, migration_type="advanced")gging is not available"""
        logger.info(f"[{level}] {message} | Metadata: {metadata}")

class SimpleMigrations:
    """Simple migration system using raw SQL that works in mobile environments"""
    
    # SQL constant to avoid duplication
    INSERT_MIGRATION_SQL = "INSERT OR IGNORE INTO schema_migrations (version) VALUES (:version)"
    
    def __init__(self, engine):
        self.engine = engine
        self.migrations = self._get_migrations()
        self._is_fresh_database = False
    
    def _get_migrations(self) -> Dict[str, str]:
        """Define your migrations here as SQL strings"""
        return {
            "001_init": """
                -- Initial tables are created by SQLAlchemy create_all()
                -- This is just a placeholder for the initial migration
                SELECT 1;
            """,
            "002_add_pfand_and_update_sales": """
                -- Add new consumer_id and donator_id columns to sales table
                ALTER TABLE sales ADD COLUMN consumer_id INTEGER;
                ALTER TABLE sales ADD COLUMN donator_id INTEGER;
                
                -- Backfill consumer_id from old user_id (if user_id column exists)
                UPDATE sales SET consumer_id = user_id WHERE user_id IS NOT NULL;
                
                -- Create pfand_history table with correct foreign key references
                CREATE TABLE IF NOT EXISTS pfand_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    counter INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                );
                
                -- Note: Foreign key constraints and column drops are handled separately
                -- to ensure compatibility across different SQLite versions
            """,
            "003_add_soft_delete_columns": """
                -- Add soft delete columns to users table
                ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE users ADD COLUMN deleted_at DATETIME;
                ALTER TABLE users ADD COLUMN deleted_by VARCHAR(255);
                
                -- Add soft delete columns to products table
                ALTER TABLE products ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE products ADD COLUMN deleted_at DATETIME;
                ALTER TABLE products ADD COLUMN deleted_by VARCHAR(255);
                
                -- Add soft delete columns to ingredients table
                ALTER TABLE ingredients ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE ingredients ADD COLUMN deleted_at DATETIME;
                ALTER TABLE ingredients ADD COLUMN deleted_by VARCHAR(255);
                
                -- Update existing records to have is_deleted = FALSE (default value should handle this, but ensure it)
                UPDATE users SET is_deleted = FALSE WHERE is_deleted IS NULL;
                UPDATE users SET deleted_at = NULL WHERE deleted_at IS NULL;
                UPDATE users SET deleted_by = NULL WHERE deleted_by IS NULL;
                UPDATE products SET is_deleted = FALSE WHERE is_deleted IS NULL;
                UPDATE products SET deleted_at = NULL WHERE deleted_at IS NULL;
                UPDATE products SET deleted_by = NULL WHERE deleted_by IS NULL;
                UPDATE ingredients SET is_deleted = FALSE WHERE is_deleted IS NULL;
                UPDATE ingredients SET deleted_at = NULL WHERE deleted_at IS NULL;
                UPDATE ingredients SET deleted_by = NULL WHERE deleted_by IS NULL;
            """,
            "004_add_enhanced_soft_delete_columns": """
                -- Add enhanced soft delete columns to users table
                ALTER TABLE users ADD COLUMN is_disabled BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE users ADD COLUMN disabled_reason VARCHAR(255);
                
                -- Add enhanced soft delete columns to products table
                ALTER TABLE products ADD COLUMN is_disabled BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE products ADD COLUMN disabled_reason VARCHAR(255);
                
                -- Add enhanced soft delete columns to ingredients table
                ALTER TABLE ingredients ADD COLUMN is_disabled BOOLEAN DEFAULT FALSE NOT NULL;
                ALTER TABLE ingredients ADD COLUMN disabled_reason VARCHAR(255);
                
                -- Update existing records to have is_disabled = FALSE (default value should handle this, but ensure it)
                UPDATE users SET is_disabled = FALSE WHERE is_disabled IS NULL;
                UPDATE users SET disabled_reason = NULL WHERE disabled_reason IS NULL;
                UPDATE products SET is_disabled = FALSE WHERE is_disabled IS NULL;
                UPDATE products SET disabled_reason = NULL WHERE disabled_reason IS NULL;
                UPDATE ingredients SET is_disabled = FALSE WHERE is_disabled IS NULL;
                UPDATE ingredients SET disabled_reason = NULL WHERE disabled_reason IS NULL;
            """,
            "005_add_stock_history_table": """
                -- Create stock_history table to track ingredient stock changes
                CREATE TABLE IF NOT EXISTS stock_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingredient_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    timestamp VARCHAR NOT NULL,
                    comment VARCHAR,
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients (ingredient_id)
                );
                
                -- Create index for better performance on ingredient_id lookups
                CREATE INDEX IF NOT EXISTS ix_stock_history_ingredient_id ON stock_history (ingredient_id);
            """,
            
            # Add more migrations here as needed
        }
    
    def _create_migration_table(self):
        """Create a table to track applied migrations"""
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))
                return [row[0] for row in result]
        except Exception:
            # Table doesn't exist yet
            return []
    
    def _needs_all_migrations(self) -> bool:
        """Check if this is a database that needs all migrations applied"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # If there's no schema_migrations table, check if it's a new database
            if 'schema_migrations' not in tables:
                if self._is_new_database():
                    print("📋 [SimpleMigrations] New database detected - will mark all migrations as applied")
                    return False  # Don't run migrations, just mark them as applied
                else:
                    print("📋 [SimpleMigrations] Existing database without migration tracking - all migrations needed")
                    return True  # Run all migrations
                
            return False
            
        except Exception as e:
            print(f"⚠️ [SimpleMigrations] Error checking if all migrations needed: {e}")
            return False
    
    def mark_all_migrations_applied(self):
        """Mark all migrations as applied for a fresh database"""
        print("📝 [SimpleMigrations] Marking all migrations as applied for fresh database")
        
        # Create migration tracking table first
        self._create_migration_table()
        
        with self.engine.begin() as conn:
            for version in sorted(self.migrations.keys()):
                conn.execute(text(self.INSERT_MIGRATION_SQL), 
                            {"version": version})
            
            # Also mark all advanced migrations as applied
            for migration_name in self._get_advanced_migrations().keys():
                advanced_version = f"advanced_{migration_name}"
                conn.execute(text(self.INSERT_MIGRATION_SQL), 
                            {"version": advanced_version})
        
        print("✅ [SimpleMigrations] All migrations marked as applied")
    
    def _has_pending_migrations(self, applied):
        """Check if there are any pending migrations (regular or advanced)"""
        # Check for pending regular migrations
        pending_regular = [v for v in sorted(self.migrations.keys()) if v not in applied]
        
        # Check for pending advanced migrations
        pending_advanced = []
        for migration_name in self._get_advanced_migrations().keys():
            if not self._check_advanced_migration_applied(migration_name):
                pending_advanced.append(migration_name)
        
        return pending_regular, pending_advanced
    
    def run_migrations(self, create_backup: bool = False):
        """Run all pending migrations with optional backup creation"""
        print("🔄 [SimpleMigrations] Starting database migrations")
        
        # Log migration start to Firebase
        log_to_firebase("INFO", "Database migration process started", 
                       migration_system="SimpleMigrations", 
                       backup_requested=create_backup)
        
        try:
            # Create migration tracking table
            self._create_migration_table()
            
            # Get applied migrations
            applied = set(self._get_applied_migrations())
            
            # Check if this is an empty database that needs all migrations
            if self._needs_all_migrations():
                if self._is_new_database():
                    print("📦 [SimpleMigrations] New database detected - marking all migrations as applied")
                    log_to_firebase("INFO", "New database detected - marking all migrations as applied",
                                   database_type="new", total_migrations=len(self.migrations))
                    self.mark_all_migrations_applied()
                    return True
                else:
                    print("📦 [SimpleMigrations] Existing database without migration tracking - applying all migrations")
                    log_to_firebase("INFO", "Existing database without migration tracking - applying all migrations",
                                   database_type="existing_untracked", total_migrations=len(self.migrations))
                
                # Create backup before migrations if requested (for new database with existing data)
                backup_created = False
                if create_backup:
                    backup_result = self._create_pre_migration_backup()
                    if not backup_result['success']:
                        print(f"⚠️ [SimpleMigrations] Backup failed: {backup_result['message']}")
                        print("⚠️ [SimpleMigrations] Continuing without backup (use at your own risk)")
                        log_to_firebase("WARNING", "Pre-migration backup failed", 
                                       error=backup_result.get('error', 'Unknown'))
                    else:
                        print(f"✅ [SimpleMigrations] Pre-migration backup created: {backup_result['backup_path']}")
                        log_to_firebase("INFO", "Pre-migration backup created successfully",
                                       backup_path=backup_result['backup_path'])
                        backup_created = True
                
                result = self._apply_all_migrations()
                
                if result:
                    log_to_firebase("INFO", "All migrations applied successfully",
                                   migration_type="full_migration", database_type="empty")
                else:
                    log_to_firebase("ERROR", "Migration process failed during full migration",
                                   migration_type="full_migration", database_type="empty")
                
                return result
            
            pending_regular, pending_advanced = self._has_pending_migrations(applied)
            
            # If no pending migrations, skip backup creation
            if not pending_regular and not pending_advanced:
                print("✅ [SimpleMigrations] No pending migrations - no backup needed")
                log_to_firebase("INFO", "No pending migrations found - database up to date",
                               applied_count=len(applied))
                return True
            
            # Log pending migrations info
            log_to_firebase("INFO", "Pending migrations detected",
                           pending_regular_count=len(pending_regular),
                           pending_advanced_count=len(pending_advanced),
                           pending_regular=pending_regular,
                           pending_advanced=pending_advanced)
            
            # Create backup before migrations if requested (only when there are pending migrations)
            backup_created = False
            if create_backup:
                backup_result = self._create_pre_migration_backup()
                if not backup_result['success']:
                    print(f"⚠️ [SimpleMigrations] Backup failed: {backup_result['message']}")
                    print("⚠️ [SimpleMigrations] Continuing without backup (use at your own risk)")
                    log_to_firebase("WARNING", "Pre-migration backup failed", 
                                   error=backup_result.get('error', 'Unknown'))
                else:
                    print(f"✅ [SimpleMigrations] Pre-migration backup created: {backup_result['backup_path']}")
                    log_to_firebase("INFO", "Pre-migration backup created successfully",
                                   backup_path=backup_result['backup_path'])
                    backup_created = True
            
            # Log what migrations will be applied
            if pending_regular:
                print(f"📋 [SimpleMigrations] Found {len(pending_regular)} pending regular migrations: {pending_regular}")
            if pending_advanced:
                print(f"📋 [SimpleMigrations] Found {len(pending_advanced)} pending advanced migrations: {pending_advanced}")
            
            # Run pending migrations for existing database
            success = self._apply_pending_migrations(applied)
            
            # Log final result
            if success:
                log_to_firebase("INFO", "Migration process completed successfully",
                               migration_type="incremental_migration",
                               applied_regular=len(pending_regular),
                               applied_advanced=len(pending_advanced))
            else:
                log_to_firebase("ERROR", "Migration process failed",
                               migration_type="incremental_migration",
                               backup_available=backup_created)
                # If migrations failed and we created a backup, mention it
                if backup_created:
                    print("❌ [SimpleMigrations] Migrations failed! You can restore from backup if needed.")
            
            return success
            
        except Exception as e:
            print(f"❌ [SimpleMigrations] Migration system failed: {e}")
            log_to_firebase("ERROR", "Migration system encountered critical error",
                           error=str(e), error_type=type(e).__name__)
            return False
    
    def _create_pre_migration_backup(self):
        """Create a backup before running migrations"""
        try:
            from services.database_backup import DatabaseBackupManager
            
            backup_manager = DatabaseBackupManager()
            
            # Create backup with migration-specific description
            current_version = self._get_current_version()
            next_version = self._get_next_version()
            
            description = f"Pre-migration backup (v{current_version} -> v{next_version})"
            
            result = backup_manager.create_backup(
                backup_type="manual",
                description=description,
                created_by="migration_system"
            )
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to create pre-migration backup: {e}"
            }
    
    def _get_current_version(self):
        """Get current database version"""
        try:
            applied = self._get_applied_migrations()
            return str(len(applied))
        except Exception:
            return "0"
    
    def _get_next_version(self):
        """Get next database version after migrations"""
        total_migrations = len(self.migrations) + len(self._get_advanced_migrations())
        return str(total_migrations)
    
    def _apply_all_migrations(self):
        """Apply all migrations to an empty database"""
        log_to_firebase("INFO", "Starting full migration process for empty database",
                       total_migrations=len(self.migrations))
        
        pending_count = 0
        for version in sorted(self.migrations.keys()):
            print(f"📦 [SimpleMigrations] Applying migration {version}")
            log_to_firebase("INFO", f"Applying migration {version}",
                           migration_version=version, migration_type="regular")
            
            try:
                # Split migration into individual statements
                statements = [stmt.strip() for stmt in self.migrations[version].split(';') if stmt.strip()]
                
                with self.engine.begin() as conn:
                    for statement in statements:
                        if statement:
                            conn.execute(text(statement))
                    
                    # Mark as applied within the same transaction
                    conn.execute(text(self.INSERT_MIGRATION_SQL), 
                                {"version": version})
                
                print(f"✅ [SimpleMigrations] Migration {version} applied successfully")
                log_to_firebase("INFO", f"Migration {version} completed successfully",
                               migration_version=version, statements_executed=len(statements))
                pending_count += 1
                
            except Exception as e:
                print(f"❌ [SimpleMigrations] Migration {version} failed: {e}")
                log_to_firebase("ERROR", f"Migration {version} failed",
                               migration_version=version, error=str(e), 
                               error_type=type(e).__name__)
                return False
        
        # Run advanced migrations (includes sales table migration)
        log_to_firebase("INFO", "Starting advanced migrations",
                       regular_migrations_applied=pending_count)
        
        if not self.run_advanced_migrations():
            log_to_firebase("ERROR", "Advanced migrations failed")
            return False
        
        print(f"✅ [SimpleMigrations] Applied {pending_count} migrations successfully")
        log_to_firebase("INFO", "Full migration process completed successfully",
                       total_applied=pending_count)
        return True
    
    def _apply_pending_migrations(self, applied):
        """Apply only pending migrations to an existing database"""
        pending_count = 0
        for version in sorted(self.migrations.keys()):
            if version not in applied:
                print(f"📦 [SimpleMigrations] Applying migration {version}")
                try:
                    # Split migration into individual statements
                    statements = [stmt.strip() for stmt in self.migrations[version].split(';') if stmt.strip()]
                    
                    with self.engine.begin() as conn:
                        for statement in statements:
                            if statement:
                                conn.execute(text(statement))
                        
                        # Mark as applied within the same transaction
                        conn.execute(text("INSERT INTO schema_migrations (version) VALUES (:version)"), 
                                    {"version": version})
                    
                    print(f"✅ [SimpleMigrations] Migration {version} applied successfully")
                    pending_count += 1
                    
                except Exception as e:
                    print(f"❌ [SimpleMigrations] Migration {version} failed: {e}")
                    return False
        
        # Run advanced migrations (includes sales table migration)
        if not self.run_advanced_migrations():
            return False
        
        if pending_count == 0:
            print("✅ [SimpleMigrations] No pending migrations")
        else:
            print(f"✅ [SimpleMigrations] Applied {pending_count} migrations successfully")
        
        return True
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    
    def add_column_if_not_exists(self, table_name: str, column_name: str, column_definition: str):
        """Add a column to a table if it doesn't already exist"""
        inspector = inspect(self.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            with self.engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))
                print(f"✅ [SimpleMigrations] Added column {column_name} to {table_name}")
        else:
            print(f"ℹ️ [SimpleMigrations] Column {column_name} already exists in {table_name}")
    
    def handle_sales_table_migration(self):
        """Handle the complex sales table migration separately"""
        print("🔄 [SimpleMigrations] Handling sales table schema changes")
        log_to_firebase("INFO", "Starting sales table migration",
                       migration_type="sales_table_schema_change")
        
        try:
            # Check if the migration is needed
            if not self.check_table_exists('sales'):
                print("ℹ️ [SimpleMigrations] Sales table doesn't exist, skipping migration")
                log_to_firebase("INFO", "Sales table not found - skipping migration",
                               table_name="sales", status="skipped")
                return True
            
            # Check if consumer_id column already exists
            inspector = inspect(self.engine)
            sales_columns = [col['name'] for col in inspector.get_columns('sales')]
            
            if 'consumer_id' not in sales_columns:
                print("📦 [SimpleMigrations] Adding consumer_id and donator_id to sales table")
                log_to_firebase("INFO", "Adding new columns to sales table",
                               new_columns=["consumer_id", "donator_id"],
                               existing_columns=sales_columns)
                
                with self.engine.begin() as conn:
                    # Add new columns
                    conn.execute(text("ALTER TABLE sales ADD COLUMN consumer_id INTEGER"))
                    conn.execute(text("ALTER TABLE sales ADD COLUMN donator_id INTEGER"))
                    
                    # Backfill consumer_id from user_id if it exists
                    if 'user_id' in sales_columns:
                        result = conn.execute(text("UPDATE sales SET consumer_id = user_id WHERE user_id IS NOT NULL"))
                        updated_rows = result.rowcount
                        log_to_firebase("INFO", "Backfilled consumer_id from user_id",
                                       updated_rows=updated_rows)
                    
                    print("✅ [SimpleMigrations] Sales table migration completed")
                    log_to_firebase("INFO", "Sales table migration completed successfully",
                                   columns_added=["consumer_id", "donator_id"])
            else:
                print("ℹ️ [SimpleMigrations] Sales table already migrated")
                log_to_firebase("INFO", "Sales table migration already completed",
                               status="already_migrated")
            
            return True
                
        except Exception as e:
            print(f"❌ [SimpleMigrations] Sales table migration failed: {e}")
            log_to_firebase("ERROR", "Sales table migration failed",
                           error=str(e), error_type=type(e).__name__)
            # Don't raise - this is a non-critical migration that might have already been applied
            return True  # Return True to continue with other migrations
    
    def drop_user_id_from_sales(self):
        """Carefully drop user_id column from sales table (SQLite compatible)"""
        print("🔄 [SimpleMigrations] Attempting to remove user_id from sales table")
        
        try:
            inspector = inspect(self.engine)
            if not self.check_table_exists('sales'):
                return True
                
            sales_columns = [col['name'] for col in inspector.get_columns('sales')]
            
            if 'user_id' in sales_columns and 'consumer_id' in sales_columns:
                print("📦 [SimpleMigrations] Recreating sales table without user_id")
                
                with self.engine.begin() as conn:
                    # SQLite doesn't support DROP COLUMN directly, so we recreate the table
                    # First, create a backup
                    conn.execute(text("""
                        CREATE TABLE sales_backup AS 
                        SELECT * FROM sales
                    """))
                    
                    # Drop the original table
                    conn.execute(text("DROP TABLE sales"))
                    
                    # Recreate without user_id based on actual table structure
                    conn.execute(text("""
                        CREATE TABLE sales (
                            sale_id INTEGER NOT NULL,
                            consumer_id INTEGER,
                            donator_id INTEGER,
                            product_id INTEGER,
                            quantity INTEGER,
                            total_price FLOAT,
                            timestamp VARCHAR,
                            toast_round_id INTEGER,
                            PRIMARY KEY (sale_id),
                            FOREIGN KEY(consumer_id) REFERENCES users (user_id),
                            FOREIGN KEY(donator_id) REFERENCES users (user_id),
                            FOREIGN KEY(product_id) REFERENCES products (product_id),
                            FOREIGN KEY(toast_round_id) REFERENCES toast_round (toast_round_id)
                        )
                    """))
                    
                    # Copy data back (excluding user_id) with correct column names
                    conn.execute(text("""
                        INSERT INTO sales (sale_id, consumer_id, donator_id, product_id, quantity, total_price, timestamp, toast_round_id)
                        SELECT sale_id, consumer_id, donator_id, product_id, quantity, total_price, timestamp, toast_round_id
                        FROM sales_backup
                    """))
                    
                    # Recreate index
                    conn.execute(text("CREATE INDEX ix_sales_sale_id ON sales (sale_id)"))
                    
                    # Drop backup
                    conn.execute(text("DROP TABLE sales_backup"))
                    
                    print("✅ [SimpleMigrations] Successfully removed user_id from sales table")
            else:
                print("ℹ️ [SimpleMigrations] user_id column not found or consumer_id not present, skipping")
            
            return True
                
        except Exception as e:
            print(f"❌ [SimpleMigrations] Failed to remove user_id column: {e}")
            # Restore from backup if it exists
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS sales"))
                    conn.execute(text("ALTER TABLE sales_backup RENAME TO sales"))
                    print("🔄 [SimpleMigrations] Restored sales table from backup")
            except Exception:
                pass
            return False
    
    def _get_advanced_migrations(self):
        """Define advanced migrations with their functions"""
        return {
            "sales_table_migration": lambda: self.handle_sales_table_migration(),
            "remove_user_id_from_sales": lambda: self._handle_user_id_removal()
        }
    
    def run_advanced_migrations(self):
        """Run advanced migrations that need special handling"""
        print("🔄 [SimpleMigrations] Running advanced schema migrations")
        
        # Get advanced migrations from centralized definition
        advanced_migrations = self._get_advanced_migrations()
        
        try:
            for migration_name, migration_func in advanced_migrations.items():
                # Check if already applied
                if self._check_advanced_migration_applied(migration_name):
                    print(f"ℹ️ [SimpleMigrations] Advanced migration '{migration_name}' already applied, skipping")
                    continue
                
                print(f"� [SimpleMigrations] Running advanced migration: {migration_name}")
                
                # Execute the migration function
                if migration_func():
                    # Mark as applied only if successful
                    self._mark_advanced_migration_applied(migration_name)
                    print(f"✅ [SimpleMigrations] Advanced migration '{migration_name}' completed")
                    log_to_firebase("INFO", f"Advanced migration '{migration_name}' completed successfully",
                                   migration_name=migration_name, status="completed")
                else:
                    print(f"❌ [SimpleMigrations] Advanced migration '{migration_name}' failed")
                    log_to_firebase("ERROR", f"Advanced migration '{migration_name}' failed",
                                   migration_name=migration_name, status="failed")
                    return False
            
            log_to_firebase("INFO", "All advanced migrations completed successfully",
                           total_advanced_migrations=len(advanced_migrations))
            return True
            
        except Exception as e:
            print(f"❌ [SimpleMigrations] Advanced migrations failed: {e}")
            log_to_firebase("ERROR", "Advanced migrations encountered critical error",
                           error=str(e), error_type=type(e).__name__)
            return False
    
    def _handle_user_id_removal(self):
        """Handle the user_id removal migration"""
        # For now, skip the advanced user_id removal migration
        # This can be enabled later when the schema is stable
        print("ℹ️ [SimpleMigrations] Advanced migrations (user_id removal) temporarily disabled")
        print("ℹ️ [SimpleMigrations] This ensures compatibility with existing baseline databases")
        return True
    
    def _check_advanced_migration_applied(self, migration_name: str) -> bool:
        """Check if an advanced migration has been applied"""
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(
                    "SELECT 1 FROM schema_migrations WHERE version = :version"
                ), {"version": f"advanced_{migration_name}"})
                return result.fetchone() is not None
        except Exception:
            return False
    
    def _mark_advanced_migration_applied(self, migration_name: str):
        """Mark an advanced migration as applied"""
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT OR IGNORE INTO schema_migrations (version) VALUES (:version)"
            ), {"version": f"advanced_{migration_name}"})

    def set_fresh_database_flag(self):
        """Mark this as a fresh database that was just created"""
        self._is_fresh_database = True

    def _is_new_database(self) -> bool:
        """Check if this is a completely new database (no file existed before)"""
        return self._is_fresh_database
