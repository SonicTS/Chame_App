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
                
                -- Create pfand_history table
                CREATE TABLE IF NOT EXISTS pfand_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    counter INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES user_table(id),
                    FOREIGN KEY (product_id) REFERENCES product_table(id)
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
    
    def _mark_migration_applied(self, version: str):
        """Mark a migration as applied"""
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO schema_migrations (version) VALUES (:version)"), 
                        {"version": version})
    
    def run_migrations(self):
        """Run all pending migrations"""
        print("🔄 [SimpleMigrations] Starting database migrations")
        
        # Create migration tracking table
        self._create_migration_table()
        
        # Get applied migrations
        applied = set(self._get_applied_migrations())
        
        # Run pending migrations
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
                        
                        # Mark as applied
                        self._mark_migration_applied(version)
                    
                    print(f"✅ [SimpleMigrations] Migration {version} applied successfully")
                    pending_count += 1
                    
                except Exception as e:
                    print(f"❌ [SimpleMigrations] Migration {version} failed: {e}")
                    raise
        
        # Run additional complex migrations
        self.handle_sales_table_migration()
        
        # Run advanced migrations (like column drops)
        self.run_advanced_migrations()
        
        if pending_count == 0:
            print("✅ [SimpleMigrations] No pending migrations")
        else:
            print(f"✅ [SimpleMigrations] Applied {pending_count} migrations successfully")
    
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
                return
            
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
                
        except Exception as e:
            print(f"❌ [SimpleMigrations] Sales table migration failed: {e}")
            # Don't raise - this is a non-critical migration that might have already been applied
    
    def drop_user_id_from_sales(self):
        """Carefully drop user_id column from sales table (SQLite compatible)"""
        print("🔄 [SimpleMigrations] Attempting to remove user_id from sales table")
        
        try:
            inspector = inspect(self.engine)
            if not self.check_table_exists('sales'):
                return
                
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
                    
                    # Recreate without user_id (this is a simplified version)
                    # You might need to adjust this based on your actual sales table structure
                    conn.execute(text("""
                        CREATE TABLE sales (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            consumer_id INTEGER,
                            donator_id INTEGER,
                            product_id INTEGER NOT NULL,
                            quantity INTEGER NOT NULL,
                            total_price REAL NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (consumer_id) REFERENCES user_table(id),
                            FOREIGN KEY (donator_id) REFERENCES user_table(id),
                            FOREIGN KEY (product_id) REFERENCES product_table(id)
                        )
                    """))
                    
                    # Copy data back (excluding user_id)
                    conn.execute(text("""
                        INSERT INTO sales (id, consumer_id, donator_id, product_id, quantity, total_price, timestamp)
                        SELECT id, consumer_id, donator_id, product_id, quantity, total_price, timestamp 
                        FROM sales_backup
                    """))
                    
                    # Drop backup
                    conn.execute(text("DROP TABLE sales_backup"))
                    
                    print("✅ [SimpleMigrations] Successfully removed user_id from sales table")
            else:
                print("ℹ️ [SimpleMigrations] user_id column not found or consumer_id not present, skipping")
                
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
    
    def run_advanced_migrations(self):
        """Run advanced migrations that need special handling"""
        print("🔄 [SimpleMigrations] Running advanced schema migrations")
        
        # Check if we need to remove user_id column from sales
        advanced_migration_applied = self._check_advanced_migration_applied("remove_user_id_from_sales")
        
        if not advanced_migration_applied:
            print("📦 [SimpleMigrations] Running user_id removal from sales table")
            self.drop_user_id_from_sales()
            self._mark_advanced_migration_applied("remove_user_id_from_sales")
        else:
            print("ℹ️ [SimpleMigrations] Advanced migrations already applied")
    
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
