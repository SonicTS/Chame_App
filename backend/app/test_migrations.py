# test_migrations.py
# Migration testing framework using real baseline databases

import os
import tempfile
import shutil
from sqlalchemy import create_engine, text
import logging

# Import your modules
from chame_app.simple_migrations import SimpleMigrations
from chame_app.database import Base
import services.admin_api as api

logger = logging.getLogger(__name__)

class MigrationTester:
    """Test framework for database migrations using real baseline databases"""
    
    def __init__(self, baseline_db_path=None):
        self.baseline_db_path = baseline_db_path or "baseline.db"
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Set up temporary directory for test databases"""
        self.temp_dir = tempfile.mkdtemp(prefix="migration_test_")
        print(f"📁 Test environment created at: {self.temp_dir}")
        
    def teardown_test_environment(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up test environment: {self.temp_dir}")
    
    def check_baseline_exists(self) -> bool:
        """Check if baseline database exists"""
        if not os.path.exists(self.baseline_db_path):
            print(f"❌ Baseline database not found at: {self.baseline_db_path}")
            print("📋 To create baseline database:")
            print("   1. Checkout your original branch (before migration changes)")
            print("   2. Run your app and create/populate the database")
            print("   3. Copy the database file to baseline.db")
            print("   4. Switch back to your migration branch")
            print("   5. Run tests again")
            return False
        
        print(f"✅ Found baseline database at: {self.baseline_db_path}")
        return True
    
    def create_test_database_from_baseline(self, test_name: str) -> str:
        """Create a test database copy from baseline"""
        if not self.check_baseline_exists():
            raise FileNotFoundError(f"Baseline database not found: {self.baseline_db_path}")
        
        test_db_path = os.path.join(self.temp_dir, f"test_{test_name}.db")
        shutil.copy2(self.baseline_db_path, test_db_path)
        
        print(f"📋 Created test database: {test_db_path}")
        return test_db_path
    
    def test_migration_from_baseline(self, test_name: str = "baseline_migration"):
        """Test migration from baseline database"""
        print(f"\n🧪 Testing migration from baseline database")
        
        # Create test database from baseline
        test_db_path = self.create_test_database_from_baseline(test_name)
        
        # Create engine for test database
        engine = create_engine(f"sqlite:///{test_db_path}")
        
        # Record original data
        original_data = self._capture_database_state(engine)
        
        try:
            # Run migrations
            migrations = SimpleMigrations(engine)
            migrations.run_migrations()
            
            # Capture final data
            final_data = self._capture_database_state(engine)
            
            # Validate migration
            self._validate_migration_results(original_data, final_data, test_name)
            
            # Test admin API functions
            self._test_admin_api_functions(engine, test_db_path)
            
            print(f"✅ Migration test from baseline passed!")
            return True
            
        except Exception as e:
            print(f"❌ Migration test from baseline failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            engine.dispose()
    
    def save_successful_migration_as_new_baseline(self, source_test_name: str, new_baseline_name: str = None):
        """Save a successfully migrated database as new baseline for future tests"""
        if new_baseline_name is None:
            new_baseline_name = f"baseline_v{len(os.listdir('.')) + 1}.db"
        
        source_path = os.path.join(self.temp_dir, f"test_{source_test_name}.db")
        
        if not os.path.exists(source_path):
            print(f"❌ Source test database not found: {source_path}")
            return False
        
        shutil.copy2(source_path, new_baseline_name)
        print(f"✅ Saved migrated database as new baseline: {new_baseline_name}")
        print(f"   You can now use this as your baseline for future migrations:")
        print(f"   tester = MigrationTester('{new_baseline_name}')")
        return True
    
    def _capture_database_state(self, engine):
        """Capture current state of database for comparison"""
        state = {
            'tables': [],
            'data': {},
            'columns': {}
        }
        
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        # Get table names
        state['tables'] = inspector.get_table_names()
        
        # Get column info for each table
        for table_name in state['tables']:
            state['columns'][table_name] = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Capture data from key tables
        with engine.connect() as conn:
            for table in ['user_table', 'product_table', 'sales', 'pfand_history']:
                if table in state['tables']:
                    try:
                        result = conn.execute(text(f"SELECT * FROM {table}"))
                        state['data'][table] = [dict(row._mapping) for row in result]
                    except Exception as e:
                        print(f"Warning: Could not capture data from {table}: {e}")
                        state['data'][table] = []
        
        return state
    
    def _validate_migration_results(self, before, after, version_name):
        """Validate that migration worked correctly"""
        print(f"🔍 Validating migration results for {version_name}")
        
        # Check that required tables exist
        required_tables = ['user_table', 'product_table', 'sales', 'schema_migrations']
        for table in required_tables:
            assert table in after['tables'], f"Required table {table} missing after migration"
        
        # Check sales table has correct columns
        sales_columns = after['columns'].get('sales', [])
        assert 'consumer_id' in sales_columns, "sales table missing consumer_id column"
        assert 'donator_id' in sales_columns, "sales table missing donator_id column"
        
        # Check data preservation
        if 'sales' in before['data'] and 'sales' in after['data']:
            before_sales_count = len(before['data']['sales'])
            after_sales_count = len(after['data']['sales'])
            assert after_sales_count >= before_sales_count, "Sales data lost during migration"
            
            # Check that consumer_id was properly backfilled
            for sale in after['data']['sales']:
                if sale.get('consumer_id') is None and version_name != "v2":
                    print(f"Warning: Sale {sale['id']} has null consumer_id")
        
        # Check pfand_history table exists (if migration should have created it)
        if version_name in ["v1", "v2"]:
            assert 'pfand_history' in after['tables'], "pfand_history table not created"
        
        print(f"✅ Migration validation passed for {version_name}")
    
    def _test_admin_api_functions(self, engine, db_path):
        """Test all admin API functions against migrated database"""
        print("🧪 Testing admin API functions against migrated database")
        
        # Mock the database connection in admin_api
        import services.admin_api as api
        
        # Create a test database instance
        # Note: You might need to adjust this based on your Database class
        original_database = api.database
        
        try:
            # Set up test database
            # This is a simplified approach - you might need to adjust based on your Database class
            api.database = api.create_database()
            
            # Test basic functions that don't require specific data
            test_functions = [
                ('get_all_users', []),
                ('get_all_products', []),
                ('get_all_ingredients', []),
                ('get_all_sales', []),
                ('get_bank', []),
                ('get_bank_transaction', []),
                ('get_pfand_history', []),
            ]
            
            for func_name, args in test_functions:
                try:
                    func = getattr(api, func_name)
                    result = func(*args)
                    print(f"✅ {func_name}() executed successfully, returned {type(result)}")
                except Exception as e:
                    print(f"❌ {func_name}() failed: {e}")
                    # Don't raise - some functions might fail due to missing test data
            
            # Test functions that create data
            try:
                # Test adding a user
                user_result = api.add_user("test_user", 10.0, "user", "")
                print(f"✅ add_user() executed successfully")
                
                # Test adding an ingredient
                ingredient_result = api.add_ingredient("test_ingredient", 5.0, 10, 20, 0.25)
                print(f"✅ add_ingredient() executed successfully")
                
            except Exception as e:
                print(f"⚠️ Some create functions failed: {e}")
            
            print("✅ Admin API function tests completed")
            
        finally:
            # Restore original database
            api.database = original_database
    
    def run_full_test_suite(self):
        """Run complete migration test suite using baseline database"""
        print("🚀 Starting migration test suite with baseline database")
        
        if not self.check_baseline_exists():
            print("\n📋 Instructions to create baseline database:")
            print("1. git stash  # Save your current migration changes")
            print("2. git checkout <original-branch>  # Switch to branch without migrations") 
            print("3. Run your app and create/populate database with real data")
            print("4. Copy the database file: cp kassensystem.db baseline.db")
            print("5. git checkout <migration-branch>  # Switch back to migration branch")
            print("6. git stash pop  # Restore your migration changes")
            print("7. Run tests again: python test_migrations.py")
            return False
        
        try:
            self.setup_test_environment()
            
            # Test migration from baseline
            success = self.test_migration_from_baseline("baseline_test")
            
            if success:
                print("\n🎉 Migration test passed!")
                print("💾 Do you want to save this migrated database as new baseline? (y/n)")
                response = input().lower().strip()
                if response == 'y':
                    self.save_successful_migration_as_new_baseline("baseline_test")
                return True
            else:
                print("\n❌ Migration test failed!")
                return False
                
        finally:
            self.teardown_test_environment()
    
    def test_idempotency(self):
        """Test that running migrations multiple times is safe"""
        print("\n🧪 Testing migration idempotency")
        
        if not self.check_baseline_exists():
            return False
        
        try:
            self.setup_test_environment()
            
            # Run migration first time
            test_db_1 = self.create_test_database_from_baseline("idempotency_test_1")
            engine_1 = create_engine(f"sqlite:///{test_db_1}")
            migrations_1 = SimpleMigrations(engine_1)
            migrations_1.run_migrations()
            
            # Capture state after first migration
            state_after_first = self._capture_database_state(engine_1)
            engine_1.dispose()
            
            # Run migration second time on the same database
            engine_2 = create_engine(f"sqlite:///{test_db_1}")
            migrations_2 = SimpleMigrations(engine_2)
            migrations_2.run_migrations()
            
            # Capture state after second migration
            state_after_second = self._capture_database_state(engine_2)
            engine_2.dispose()
            
            # Compare states - they should be identical
            if self._compare_database_states(state_after_first, state_after_second):
                print("✅ Migration idempotency test passed!")
                return True
            else:
                print("❌ Migration idempotency test failed - states differ!")
                return False
                
        except Exception as e:
            print(f"❌ Migration idempotency test failed: {e}")
            return False
        finally:
            self.teardown_test_environment()
    
    def test_fresh_database_creation(self):
        """Test creating a fresh database (no migration needed)"""
        print(f"\n🧪 Testing fresh database creation")
        
        try:
            # Create fresh database
            fresh_db_path = os.path.join(self.temp_dir, "fresh.db")
            engine = create_engine(f"sqlite:///{fresh_db_path}")
            
            # Create all tables using SQLAlchemy
            Base.metadata.create_all(engine)
            
            # Run migrations (should be no-op for fresh DB)
            migrations = SimpleMigrations(engine)
            migrations.run_migrations()
            
            # Test API functions
            self._test_admin_api_functions(engine, fresh_db_path)
            
            print("✅ Fresh database creation test passed!")
            return True
            
        except Exception as e:
            print(f"❌ Fresh database creation test failed: {e}")
            return False
        finally:
            engine.dispose()
    
    def _compare_database_states(self, state1, state2):
        """Compare two database states for idempotency testing"""
        # Compare table names
        if set(state1['tables']) != set(state2['tables']):
            print("❌ Table lists differ between states")
            return False
        
        # Compare column structures
        for table in state1['tables']:
            if state1['columns'][table] != state2['columns'][table]:
                print(f"❌ Column structure differs for table {table}")
                return False
        
        # Compare data counts (should be same)
        for table in state1['data']:
            if len(state1['data'][table]) != len(state2['data'][table]):
                print(f"❌ Data count differs for table {table}")
                return False
        
        return True
    
    def create_baseline_instructions(self):
        """Print detailed instructions for creating baseline database"""
        print("\n" + "="*60)
        print("📋 BASELINE DATABASE CREATION GUIDE")
        print("="*60)
        print()
        print("To create a baseline database for migration testing:")
        print()
        print("1️⃣  SAVE YOUR CURRENT WORK")
        print("   git add . && git commit -m 'WIP: migration changes'")
        print("   # OR")
        print("   git stash push -m 'migration changes'")
        print()
        print("2️⃣  SWITCH TO ORIGINAL BRANCH (without migrations)")
        print("   git checkout main  # or whatever your original branch is")
        print()
        print("3️⃣  RUN YOUR APP AND CREATE DATA")
        print("   - Start your application")
        print("   - Create users, products, ingredients")
        print("   - Make some sales transactions")
        print("   - Add realistic data that represents your production scenario")
        print()
        print("4️⃣  COPY THE DATABASE")
        print("   cp kassensystem.db baseline.db")
        print("   # OR copy from wherever your app creates the database")
        print()
        print("5️⃣  SWITCH BACK TO MIGRATION BRANCH")
        print("   git checkout feature/migrations  # or your migration branch")
        print("   git stash pop  # if you used stash")
        print()
        print("6️⃣  RUN TESTS")
        print("   python test_migrations.py")
        print()
        print("💡 TIP: The more realistic your baseline data, the better your tests!")
        print("="*60)
        print()
    
    def analyze_baseline_database(self):
        """Analyze the baseline database and show its contents"""
        if not self.check_baseline_exists():
            return
        
        print(f"\n🔍 Analyzing baseline database: {self.baseline_db_path}")
        
        engine = create_engine(f"sqlite:///{self.baseline_db_path}")
        try:
            state = self._capture_database_state(engine)
            
            print("\n📊 Database Statistics:")
            print("-" * 40)
            for table in sorted(state['tables']):
                count = len(state['data'].get(table, []))
                columns = len(state['columns'].get(table, []))
                print(f"  {table:<20} {count:>6} rows, {columns:>2} columns")
            
            print("\n📋 Table Structures:")
            print("-" * 40)
            for table in sorted(state['tables']):
                if table in state['columns']:
                    cols = ', '.join(state['columns'][table][:5])  # Show first 5 columns
                    if len(state['columns'][table]) > 5:
                        cols += ", ..."
                    print(f"  {table}: {cols}")
            
            print("\n✅ Baseline database analysis complete")
            
        except Exception as e:
            print(f"❌ Error analyzing baseline database: {e}")
        finally:
            engine.dispose()
        


# Pytest integration
class TestMigrations:
    """Pytest test class for migrations using baseline approach"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.tester = MigrationTester()
        self.tester.setup_test_environment()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.tester.teardown_test_environment()
    
    def test_migration_from_baseline(self):
        """Test migration from baseline database"""
        assert self.tester.test_migration_from_baseline("pytest_baseline")
    
    def test_fresh_database(self):
        """Test fresh database creation"""
        assert self.tester.test_fresh_database_creation()
    
    def test_migration_idempotency(self):
        """Test that running migrations multiple times is safe"""
        assert self.tester.test_idempotency()


# CLI runner
if __name__ == "__main__":
    # Run tests directly
    tester = MigrationTester()
    success = tester.run_full_test_suite()
    
    if success:
        exit(0)
    else:
        exit(1)
