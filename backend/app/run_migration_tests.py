# run_migration_tests.py
# Simple script to run baseline-based migration tests

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from test_migrations import MigrationTester

def main():
    """Run the migration test suite using baseline database"""
    print("🧪 Starting Baseline Migration Test Suite")
    print("=" * 50)
    
    # Check if baseline database exists
    tester = MigrationTester()
    
    if not tester.check_baseline_exists():
        print("\n🚨 No baseline database found!")
        tester.create_baseline_instructions()
        return 1
    
    # Analyze baseline database
    tester.analyze_baseline_database()
    
    # Run migration tests
    success = tester.run_full_test_suite()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed! Your migrations are working correctly.")
        print("💡 Next steps:")
        print("   - Deploy your migration changes")
        print("   - Keep the new baseline for future migration testing")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        print("💡 Troubleshooting:")
        print("   - Check migration SQL syntax")
        print("   - Verify data preservation logic")
        print("   - Test with fresh baseline database")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
