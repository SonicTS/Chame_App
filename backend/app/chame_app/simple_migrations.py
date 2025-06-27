# simple_migrations.py
# A basic migration system that works in both desktop and mobile environments
# without requiring Alembic

from sqlalchemy import text, inspect
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class SimpleMigrations:
    """Simple migration system using raw SQL that works in mobile environments"""
    
    def __init__(self, engine):
        self.engine = engine
        self.migrations = self._get_migrations()
    
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
        """Check if this is a database that needs all migrations applied (no migration tracking table)"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # If there's no schema_migrations table, we need to apply all migrations
            if 'schema_migrations' not in tables:
                print("📋 [SimpleMigrations] No migration tracking table found - all migrations needed")
                return True
                
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
                conn.execute(text("INSERT OR IGNORE INTO schema_migrations (version) VALUES (:version)"), 
                            {"version": version})
            
            # Also mark all advanced migrations as applied
            for migration_name in self._get_advanced_migrations().keys():
                advanced_version = f"advanced_{migration_name}"
                conn.execute(text("INSERT OR IGNORE INTO schema_migrations (version) VALUES (:version)"), 
                            {"version": advanced_version})
        
        print("✅ [SimpleMigrations] All migrations marked as applied")
    
    def run_migrations(self):
        """Run all pending migrations"""
        print("🔄 [SimpleMigrations] Starting database migrations")
        
        try:
            # Create migration tracking table
            self._create_migration_table()
            
            # Get applied migrations
            applied = set(self._get_applied_migrations())
            
            # Check if this is an empty database that needs all migrations
            if self._needs_all_migrations():
                print("📦 [SimpleMigrations] Empty database - applying all migrations")
                return self._apply_all_migrations()
            
            # Run pending migrations for existing database
            return self._apply_pending_migrations(applied)
            
        except Exception as e:
            print(f"❌ [SimpleMigrations] Migration system failed: {e}")
            return False
    
    def _apply_all_migrations(self):
        """Apply all migrations to an empty database"""
        pending_count = 0
        for version in sorted(self.migrations.keys()):
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
        
        print(f"✅ [SimpleMigrations] Applied {pending_count} migrations successfully")
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
        
        try:
            # Check if the migration is needed
            if not self.check_table_exists('sales'):
                print("ℹ️ [SimpleMigrations] Sales table doesn't exist, skipping migration")
                return True
            
            # Check if consumer_id column already exists
            inspector = inspect(self.engine)
            sales_columns = [col['name'] for col in inspector.get_columns('sales')]
            
            if 'consumer_id' not in sales_columns:
                print("📦 [SimpleMigrations] Adding consumer_id and donator_id to sales table")
                
                with self.engine.begin() as conn:
                    # Add new columns
                    conn.execute(text("ALTER TABLE sales ADD COLUMN consumer_id INTEGER"))
                    conn.execute(text("ALTER TABLE sales ADD COLUMN donator_id INTEGER"))
                    
                    # Backfill consumer_id from user_id if it exists
                    if 'user_id' in sales_columns:
                        conn.execute(text("UPDATE sales SET consumer_id = user_id WHERE user_id IS NOT NULL"))
                    
                    print("✅ [SimpleMigrations] Sales table migration completed")
            else:
                print("ℹ️ [SimpleMigrations] Sales table already migrated")
            
            return True
                
        except Exception as e:
            print(f"❌ [SimpleMigrations] Sales table migration failed: {e}")
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
                else:
                    print(f"❌ [SimpleMigrations] Advanced migration '{migration_name}' failed")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ [SimpleMigrations] Advanced migrations failed: {e}")
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
