#!/usr/bin/env python3
"""
Migration and API Integration Tests
Comprehensive testing that:
1. Uses generated test databases
2. Performs database migrations
3. Tests API functionality after migration
4. Validates data integrity throughout the process
"""

import os
import sys
import tempfile
import shutil
import sqlite3
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.admin_api as api
from chame_app.simple_migrations import SimpleMigrations
from comprehensive_api_tests import ComprehensiveAPITester

class MigrationAPITester:
    """Comprehensive testing of migrations and API functionality using baseline databases"""
    
    def __init__(self, baseline_version: str = "baseline", target_version: str = None):
        self.test_databases_dir = "testing/test_databases"
        self.baseline_version = baseline_version  # Old schema (pre-migration)
        self.target_version = target_version      # New schema (post-migration target)
        self.baseline_dir = os.path.join(self.test_databases_dir, baseline_version)
        self.target_dir = os.path.join(self.test_databases_dir, target_version) if target_version else None
        self.temp_dir = None
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def setup_test_environment(self):
        """Set up temporary directory for testing"""
        self.temp_dir = tempfile.mkdtemp(prefix="migration_api_test_")
        print(f"📁 Test environment created at: {self.temp_dir}")
        
        # Set environment to use our temp directory
        os.environ["PRIVATE_STORAGE"] = self.temp_dir
        
    def teardown_test_environment(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print("🧹 Cleaned up test environment")
    
    def find_available_test_databases(self):
        """Find all available baseline databases"""
        test_db_files = []
        baseline_path = Path(self.baseline_dir)
        
        if not baseline_path.exists():
            print(f"❌ Baseline directory not found: {self.baseline_dir}")
            print("💡 Expected directory structure:")
            print(f"   {self.test_databases_dir}/")
            print("   ├── baseline/")
            print("   │   ├── minimal_test.db")
            print("   │   ├── comprehensive_test.db")
            print("   │   └── edge_case_test.db")
            print("   └── [future_version]/")
            return []
        
        for db_file in baseline_path.glob("*.db"):
            if db_file.is_file():
                test_db_files.append(str(db_file))
        
        return test_db_files
    
    def get_available_baseline_versions(self):
        """Get all available baseline versions (directories)"""
        test_db_path = Path(self.test_databases_dir)
        baseline_versions = []
        
        if test_db_path.exists():
            for item in test_db_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if directory contains .db files
                    db_files = list(item.glob("*.db"))
                    if db_files:
                        baseline_versions.append(item.name)
        
        return baseline_versions
    
    def copy_database_to_test_env(self, source_db_path: str) -> str:
        """Copy a database to the test environment"""
        if not os.path.exists(source_db_path):
            raise FileNotFoundError(f"Source database not found: {source_db_path}")
        
        # Target path in test environment
        target_path = os.path.join(self.temp_dir, "kassensystem.db")
        
        # Remove existing database if it exists
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception as e:
                print(f"  ⚠️ Warning: Could not remove existing database: {e}")
        
        # Copy database
        shutil.copy2(source_db_path, target_path)
        print(f"📄 Copied database: {os.path.basename(source_db_path)} -> test environment")
        
        # Small delay to ensure file system operations complete
        import time
        time.sleep(0.1)
        
        return target_path
    
    def analyze_database_schema(self, db_path: str) -> dict:
        """Analyze database schema and data"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = {
                'tables': tables,
                'data_counts': {}
            }
            
            # Get row counts for each table
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    schema_info['data_counts'][table] = count
                except Exception as e:
                    schema_info['data_counts'][table] = f"Error: {e}"
            
            return schema_info
            
        finally:
            conn.close()
    
    def test_database_migration(self, db_path: str) -> bool:
        """Test migration on a specific database"""
        print(f"🔄 Testing migration on: {os.path.basename(db_path)}")
        
        engine = None
        try:
            # Analyze schema before migration
            print("  📊 Analyzing pre-migration schema...")
            pre_migration_schema = self.analyze_database_schema(db_path)
            print(f"     Tables: {', '.join(pre_migration_schema['tables'])}")
            
            # Reset API database instance to use our test database
            api.database = None
            
            # Create SQLAlchemy engine for migrations with proper connection settings
            from sqlalchemy import create_engine
            engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                },
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False  # Disable SQL logging to reduce output
            )
            
            # Initialize migration system
            migrations = SimpleMigrations(engine)
            
            # Check current migration status
            applied_migrations = migrations._get_applied_migrations()
            available_migrations = list(migrations.migrations.keys())
            
            print(f"  📋 Applied migrations: {len(applied_migrations)}")
            print(f"  📋 Available migrations: {len(available_migrations)}")
            
            if len(applied_migrations) >= len(available_migrations):
                print("  ✅ No migrations needed - database is up to date")
                return True
            
            # Run migrations
            print("  🚀 Running migrations...")
            migration_success = migrations.run_migrations()
            
            if not migration_success:
                print("  ❌ Migration failed!")
                return False
            
            print("  ✅ Migrations completed successfully")
            
            # Analyze schema after migration
            print("  � Analyzing post-migration schema...")
            post_migration_schema = self.analyze_database_schema(db_path)
            
            print(f"     Updated tables: {', '.join(post_migration_schema['tables'])}")
            print("  ✅ Migration test completed successfully")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Migration test failed: {e}")
            return False
            
        finally:
            # Ensure engine is properly disposed
            if engine:
                try:
                    engine.dispose()
                    print("  🧹 Database engine disposed")
                except Exception as e:
                    print(f"  ⚠️ Warning: Error disposing engine: {e}")
            
            # Add a small delay to ensure all connections are closed
            time.sleep(0.5)
    
    def test_api_functionality(self, db_path: str) -> dict:
        """Test API functionality after migration"""
        print(f"🧪 Testing API functionality on: {os.path.basename(db_path)}")
        
        try:
            # Reset API database to use our migrated database
            api.database = None
            api.create_database()
            
            # Create API tester with our test environment
            api_tester = ComprehensiveAPITester()
            api_tester.temp_dir = self.temp_dir
            api_tester.test_db_path = db_path
            
            # Test core API functions
            print("  🔍 Testing all api functions...")
    
            # Test basic data fetchers
            test_results = api_tester.test_all_api_functions()
    
            print(f"  📊 API Test Results: {test_results['passed']} passed, {test_results['failed']} failed")
            return test_results
            
        except Exception as e:
            print(f"  ❌ API testing error: {e}")
            return {
                'passed': 0,
                'failed': 1,
                'errors': [f"API testing failed: {e}"]
            }
    
    def run_migration_validation_test(self, baseline_db_path: str, target_db_path: str = None) -> dict:
        """
        Run migration validation test:
        1. Migrate baseline database
        2. Run tests on migrated database
        3. Optionally compare against target database to ensure same behavior
        """
        db_name = os.path.basename(baseline_db_path)
        print(f"\n🎯 Migration Validation Test: {db_name}")
        print("=" * 60)
        
        test_result = {
            'database': db_name,
            'migration_success': False,
            'api_test_results': None,
            'target_comparison': None,
            'errors': []
        }
        
        try:
            # Step 1: Migrate baseline database
            print("📋 Step 1: Migrating baseline database...")
            migrated_db_path = self.copy_database_to_test_env(baseline_db_path)
            migration_success = self.test_database_migration(migrated_db_path)
            test_result['migration_success'] = migration_success
            
            if not migration_success:
                test_result['errors'].append("Migration failed")
                return test_result
            
            # Step 2: Test migrated database
            print("📋 Step 2: Testing migrated database...")
            migrated_api_results = self.test_api_functionality(migrated_db_path)
            test_result['api_test_results'] = migrated_api_results
            
            # Step 3: Optional comparison with target database
            if target_db_path and os.path.exists(target_db_path):
                print("📋 Step 3: Comparing with target database...")
                target_comparison = self.compare_with_target_database(target_db_path)
                test_result['target_comparison'] = target_comparison
            
            # Update overall test counts
            self.test_results['total_tests'] += 1
            if migration_success and migrated_api_results['failed'] == 0:
                self.test_results['passed'] += 1
                print(f"✅ {db_name}: Migration validation passed")
            else:
                self.test_results['failed'] += 1
                print(f"❌ {db_name}: Migration validation failed")
                if test_result['errors']:
                    self.test_results['errors'].extend(test_result['errors'])
                if migrated_api_results and migrated_api_results['errors']:
                    self.test_results['errors'].extend(migrated_api_results['errors'])
            
        except Exception as e:
            test_result['errors'].append(f"Migration validation failed: {e}")
            self.test_results['failed'] += 1
            self.test_results['total_tests'] += 1
            print(f"❌ {db_name}: Migration validation failed: {e}")
        
        return test_result
    
    def compare_with_target_database(self, target_db_path: str) -> dict:
        """
        Compare the migrated database behavior with a target database
        by running the same API tests on both
        """
        print(f"  🔍 Running API tests on target database for comparison...")
        
        # Setup separate temp environment for target database
        target_temp_dir = tempfile.mkdtemp(prefix="target_test_")
        old_private_storage = os.environ.get("PRIVATE_STORAGE")
        
        try:
            # Test target database
            os.environ["PRIVATE_STORAGE"] = target_temp_dir
            target_test_path = os.path.join(target_temp_dir, "kassensystem.db")
            shutil.copy2(target_db_path, target_test_path)
            
            # Reset API and test target
            api.database = None
            api.create_database()
            
            target_api_results = self.test_api_functionality(target_test_path)
            
            return {
                'target_api_results': target_api_results,
                'comparison_notes': f"Target database API tests: {target_api_results['passed']} passed, {target_api_results['failed']} failed"
            }
            
        except Exception as e:
            return {
                'target_api_results': None,
                'comparison_notes': f"Target database test failed: {e}"
            }
        finally:
            # Restore environment
            if old_private_storage:
                os.environ["PRIVATE_STORAGE"] = old_private_storage
            else:
                os.environ.pop("PRIVATE_STORAGE", None)
            
            # Cleanup target temp directory
            if os.path.exists(target_temp_dir):
                shutil.rmtree(target_temp_dir, ignore_errors=True)
    
    def run_full_test_suite(self) -> bool:
        """Run migration and API tests on all available test databases"""
        print("🚀 Starting Migration and API Integration Test Suite")
        print("=" * 70)
        
        try:
            return self._execute_test_suite()
        except Exception as e:
            print(f"💥 Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.teardown_test_environment()
    
    def _execute_test_suite(self) -> bool:
        """Execute the migration validation test suite"""
        # Setup test environment
        self.setup_test_environment()
        
        # Show available baseline versions
        available_versions = self.get_available_baseline_versions()
        if len(available_versions) > 1:
            print(f"📋 Available baseline versions: {', '.join(available_versions)}")
            print(f"🎯 Using baseline version: {self.baseline_version}")
            if self.target_version:
                print(f"🎯 Target version for comparison: {self.target_version}")
        
        # Find available test databases
        baseline_databases = self.find_available_test_databases()
        
        if not baseline_databases:
            print(f"❌ No baseline databases found in: {self.baseline_dir}")
            print("💡 Baseline databases contain the old schema before migration.")
            print("💡 Migration tests will:")
            print("   1. Take baseline databases (old schema)")
            print("   2. Apply migrations to transform to new schema")
            print("   3. Run new tests on migrated databases")
            print("   4. Verify they behave like target databases")
            return False
        
        print(f"📁 Found {len(baseline_databases)} baseline databases:")
        for db in baseline_databases:
            print(f"  • {os.path.basename(db)}")
        
        # Find target databases for comparison (if target version specified)
        target_databases = {}
        if self.target_version and self.target_dir and os.path.exists(self.target_dir):
            target_path = Path(self.target_dir)
            for target_db in target_path.glob("*.db"):
                if target_db.is_file():
                    target_databases[target_db.name] = str(target_db)
            if target_databases:
                print(f"📁 Found {len(target_databases)} target databases for comparison:")
                for db_name in target_databases:
                    print(f"  • {db_name}")
        
        # Test each baseline database
        detailed_results = []
        for i, baseline_db_path in enumerate(baseline_databases):
            if i > 0:
                # Add small delay between tests to ensure proper cleanup
                time.sleep(0.5)
            
            # Find corresponding target database
            baseline_name = os.path.basename(baseline_db_path)
            target_db_path = target_databases.get(baseline_name) if target_databases else None
            
            result = self.run_migration_validation_test(baseline_db_path, target_db_path)
            detailed_results.append(result)
        
        # Print results and return success status
        return self._print_final_results(detailed_results)
    
    def _print_final_results(self, detailed_results: list) -> bool:
        """Print final summary and return success status"""
        print("\n" + "=" * 70)
        print("📊 FINAL TEST RESULTS")
        print("=" * 70)
        
        print(f"🎯 Total databases tested: {self.test_results['total_tests']}")
        print(f"✅ Successful: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            self._print_error_summary()
        
        self._print_detailed_results(detailed_results)
        
        success = self.test_results['failed'] == 0
        self._print_conclusion(success)
        return success
    
    def _print_error_summary(self):
        """Print error summary"""
        print("\n🚨 Error Summary:")
        for error in self.test_results['errors']:
            print(f"  • {error}")
    
    def _print_detailed_results(self, detailed_results: list):
        """Print detailed results for each database"""
        print("\n📋 Detailed Results:")
        for result in detailed_results:
            status = "✅" if result['migration_success'] and (not result['api_test_results'] or result['api_test_results']['failed'] == 0) else "❌"
            print(f"  {status} {result['database']}")
            
            if result['migration_success']:
                print("      Migration: ✅ Success")
            else:
                print("      Migration: ❌ Failed")
            
            if result['api_test_results']:
                api_res = result['api_test_results']
                print(f"      API Tests: {api_res['passed']} passed, {api_res['failed']} failed")
            
            if result['errors']:
                print(f"      Errors: {'; '.join(result['errors'])}")
    
    def _print_conclusion(self, success: bool):
        """Print final conclusion"""
        if success:
            print("\n🎉 All migration and API tests passed!")
            print("💡 Your database migrations are working correctly across all test scenarios.")
        else:
            print("\n⚠️ Some tests failed. Please review the errors above.")
            print("💡 Check migration scripts and API compatibility.")

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration and API Integration Test Suite")
    parser.add_argument(
        "--baseline-version", 
        default="baseline",
        help="Baseline version (old schema) to use for testing (default: baseline)"
    )
    parser.add_argument(
        "--target-version",
        help="Target version (new schema) to compare against after migration"
    )
    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List available baseline versions and exit"
    )
    parser.add_argument(
        "--single-test",
        type=str,
        help="Run test on a single database file (e.g., minimal_test.db)"
    )
    
    args = parser.parse_args()
    
    # Handle list versions command
    if args.list_versions:
        temp_tester = MigrationAPITester()
        versions = temp_tester.get_available_baseline_versions()
        if versions:
            print("📋 Available baseline versions:")
            for version in versions:
                print(f"  • {version}")
        else:
            print("❌ No baseline versions found")
            print(f"💡 Expected location: {temp_tester.test_databases_dir}/")
        exit(0)
    
    print("🧪 Migration and API Integration Test Suite")
    print("This will test database migrations and API functionality")
    print("using baseline databases with old schema, migrating them,")
    print("and testing with new API tests.")
    print()
    
    tester = MigrationAPITester(
        baseline_version=args.baseline_version,
        target_version=args.target_version
    )
    
    # Handle single test mode
    if args.single_test:
        print(f"🎯 Running single migration test on: {args.single_test}")
        baseline_path = os.path.join(tester.baseline_dir, args.single_test)
        if not os.path.exists(baseline_path):
            print(f"❌ Baseline database not found: {baseline_path}")
            exit(1)
        
        # Find corresponding target database if target version specified
        target_path = None
        if args.target_version:
            target_path = os.path.join(tester.target_dir, args.single_test)
            if not os.path.exists(target_path):
                print(f"⚠️ Warning: Target database not found: {target_path}")
                target_path = None
        
        tester.setup_test_environment()
        try:
            result = tester.run_migration_validation_test(baseline_path, target_path)
            if result['migration_success'] and (not result['api_test_results'] or result['api_test_results']['failed'] == 0):
                print(f"\n🎉 Migration test passed for {args.single_test}!")
                exit(0)
            else:
                print(f"\n❌ Migration test failed for {args.single_test}")
                exit(1)
        finally:
            tester.teardown_test_environment()
    
    # Run full test suite
    success = tester.run_full_test_suite()
    
    if success:
        print("\n🎉 All tests passed! Your migrations and API are working correctly.")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        exit(1)
