# alembic_runtime.py
# Demonstrates how to use Alembic programmatically at runtime
# This works in environments where Alembic is available but alembic.ini is not

from typing import Optional
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, DateTime
from sqlalchemy.sql import text
import logging

logger = logging.getLogger(__name__)

class RuntimeAlembicMigrations:
    """Runtime Alembic migrations using programmatic API"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def run_programmatic_migrations(self):
        """Run Alembic migrations programmatically without config files"""
        try:
            from alembic.migration import MigrationContext
            from alembic.operations import Operations
            from alembic.script import ScriptDirectory
            from alembic.config import Config
            import tempfile
            import os
            
            print("🔧 [RuntimeAlembic] Running programmatic migrations")
            
            # Create a temporary alembic configuration in memory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create minimal alembic.ini content
                alembic_ini_content = f"""
[alembic]
script_location = {temp_dir}/alembic
sqlalchemy.url = sqlite:///dummy.db
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
"""
                
                # Write temporary alembic.ini
                ini_path = os.path.join(temp_dir, "alembic.ini")
                with open(ini_path, 'w') as f:
                    f.write(alembic_ini_content)
                
                # Create alembic script directory structure
                script_dir = os.path.join(temp_dir, "alembic")
                os.makedirs(script_dir, exist_ok=True)
                os.makedirs(os.path.join(script_dir, "versions"), exist_ok=True)
                
                # Create env.py
                env_py_content = '''
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

config = context.config
fileConfig(config.config_file_name)

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = context.config.attributes.get("connection", None)
    
    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    pass  # Offline mode not supported
else:
    run_migrations_online()
'''
                
                with open(os.path.join(script_dir, "env.py"), 'w') as f:
                    f.write(env_py_content)
                
                # Load configuration and run migrations
                config = Config(ini_path)
                config.attributes['connection'] = self.engine.connect()
                
                # Create migration context directly
                with self.engine.connect() as connection:
                    context = MigrationContext.configure(connection)
                    current_rev = context.get_current_revision()
                    print(f"📍 [RuntimeAlembic] Current revision: {current_rev}")
                    
                    # Run specific operations
                    self._run_migration_operations(context)
                    
                print("✅ [RuntimeAlembic] Programmatic migrations completed")
                
        except ImportError:
            print("❌ [RuntimeAlembic] Alembic not available")
        except Exception as e:
            print(f"❌ [RuntimeAlembic] Migration failed: {e}")
            raise
    
    def _run_migration_operations(self, context):
        """Define your migration operations here"""
        from alembic.operations import Operations
        
        ops = Operations(context)
        
        # Example migrations - customize these for your needs
        try:
            # Check if we need to add a new column
            # This is just an example - you'd want to check if it exists first
            
            # Example: Add a new column to user_table
            # ops.add_column('user_table', 
            #               Column('last_login', DateTime, nullable=True))
            
            # Example: Create a new table
            # ops.create_table('audit_log',
            #     Column('id', Integer, primary_key=True),
            #     Column('table_name', String(50), nullable=False),
            #     Column('operation', String(20), nullable=False),
            #     Column('timestamp', DateTime, nullable=False)
            # )
            
            print("📦 [RuntimeAlembic] Custom migration operations completed")
            
        except Exception as e:
            print(f"⚠️ [RuntimeAlembic] Some migration operations failed: {e}")
            # Don't raise - some operations might fail if already applied
    
    def create_revision(self, message: str) -> Optional[str]:
        """Create a new revision programmatically"""
        try:
            from alembic.autogenerate import produce_migrations
            from alembic.migration import MigrationContext
            from alembic.operations import Operations
            import uuid
            
            with self.engine.connect() as connection:
                context = MigrationContext.configure(connection)
                
                # Generate a revision ID
                revision_id = str(uuid.uuid4())[:8]
                
                print(f"📝 [RuntimeAlembic] Creating revision {revision_id}: {message}")
                
                # You can use this to generate migration scripts programmatically
                # This would require more setup to be fully functional
                
                return revision_id
                
        except Exception as e:
            print(f"❌ [RuntimeAlembic] Failed to create revision: {e}")
            return None
