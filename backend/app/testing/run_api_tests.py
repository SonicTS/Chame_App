#!/usr/bin/env python3
"""
Quick test runner for admin API functions
Provides a simple way to run comprehensive tests and get a clear summary
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comprehensive_api_tests import ComprehensiveAPITester

def main():
    """Main test runner"""
    print("🚀 Quick API Test Runner")
    print("=" * 50)
    
    # Check if we want to run specific test types
    run_full = True
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            run_full = False
            print("Running quick tests only...")
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python run_api_tests.py           # Full test suite")
            print("  python run_api_tests.py --quick   # Quick tests only")
            print("  python run_api_tests.py --help    # Show this help")
            return
    
    tester = ComprehensiveAPITester()
    
    try:
        # Setup test environment
        tester.setup_test_environment()
        tester.create_test_database()
        
        print("\n📊 Populating test database...")
        tester.populate_generic_test_data()
        
        print("\n🧪 Running API tests...")
        if run_full:
            main_results = tester.test_all_api_functions()
            edge_results = tester.test_edge_cases()
            
            total_passed = main_results['passed'] + edge_results['passed']
            total_failed = main_results['failed'] + edge_results['failed']
        else:
            # Quick test - just data fetchers and basic operations
            main_results = {'passed': 0, 'failed': 0, 'errors': []}
            tester._test_data_fetchers(main_results)
            
            total_passed = main_results['passed']
            total_failed = main_results['failed']
            edge_results = {'errors': []}
        
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 50)
        print("📈 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {total_failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if main_results.get('errors') or edge_results.get('errors'):
            print("\n⚠️ Issues found:")
            for error in main_results.get('errors', []) + edge_results.get('errors', []):
                print(f"  • {error}")
        else:
            print("\n🎉 All tests passed!")
        
        print(f"\n💾 Test database: {tester.test_db_path}")
        print("   ↳ Contains realistic test data for manual inspection")
        
        if success_rate >= 90:
            print("\n✨ Your API is working excellently!")
            return 0
        elif success_rate >= 75:
            print("\n👍 Your API is working well with minor issues")
            return 0
        else:
            print("\n⚠️ Your API needs attention - check the errors above")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
