#!/usr/bin/env python3
"""
Complete Migration Testing Workflow Script

This script demonstrates the complete workflow for testing migrations:
1. Generate new test databases with current schema
2. Test that new API tests pass on new databases
3. Test that migrations work on old databases
4. Verify migrated databases pass new tests

Usage:
    python workflow_demo.py                    # Run complete workflow
    python workflow_demo.py --quick           # Skip comprehensive databases
    python workflow_demo.py --new-version v1.2 # Specify version for new databases
"""

import argparse
import os
import sys
import subprocess
import time

def run_command(command, description, working_dir=None):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()
    
    # Change to working directory if specified
    original_dir = os.getcwd()
    if working_dir:
        os.chdir(working_dir)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False
    finally:
        # Restore original directory
        os.chdir(original_dir)

def setup_databases_for_api_testing(backend_dir, new_version):
    """Copy new databases to main test location for API testing"""
    new_db_dir = os.path.join(backend_dir, "testing", "test_databases", new_version)
    if os.path.exists(new_db_dir):
        main_db_dir = os.path.join(backend_dir, "test_databases")
        os.makedirs(main_db_dir, exist_ok=True)
        
        import shutil
        for db_file in os.listdir(new_db_dir):
            if db_file.endswith('.db'):
                shutil.copy2(
                    os.path.join(new_db_dir, db_file),
                    os.path.join(main_db_dir, db_file)
                )

def run_workflow_steps(args, backend_dir):
    """Run all workflow steps and return number of steps passed"""
    db_types = "minimal" if args.quick else "all"
    steps_passed = 0
    
    # Step 1: Generate new test databases
    success = run_command(
        f"python testing/generate_test_databases.py {db_types} --version {args.new_version}",
        f"Step 1: Generate new test databases (version {args.new_version})",
        backend_dir
    )
    if success:
        steps_passed += 1
    
    # Step 2: Setup and test API on new databases
    setup_databases_for_api_testing(backend_dir, args.new_version)
    success = run_command(
        "python testing/comprehensive_api_tests.py",
        "Step 2: Test API functionality on new databases",
        backend_dir
    )
    if success:
        steps_passed += 1
    
    # Step 3: Test migrations
    success = run_command(
        f"python testing/migration_and_api_tests.py --baseline-version {args.baseline_version}",
        f"Step 3: Test migrations from {args.baseline_version} to current",
        backend_dir
    )
    if success:
        steps_passed += 1
    
    return steps_passed

def print_workflow_summary(steps_passed, total_steps):
    """Print workflow summary and recommendations"""
    print(f"\n{'='*60}")
    print("📊 WORKFLOW SUMMARY")
    print(f"{'='*60}")
    print(f"Steps completed successfully: {steps_passed}/{total_steps}")
    
    if steps_passed == total_steps:
        print("🎉 Complete workflow passed!")
        print()
        print("✅ Your migration system is working correctly:")
        print("   • New databases generated with current schema")
        print("   • API tests pass on new databases")
        print("   • Migrations successfully update old databases")
        print("   • Migrated databases pass current API tests")
        print()
        print("🚀 You're ready to deploy your changes!")
        return True
    else:
        print("⚠️ Workflow had some issues:")
        print()
        if steps_passed >= 2:
            print("✅ New database generation and API testing works")
            if steps_passed < 3:
                print("❌ Migration testing failed - check migration scripts")
        elif steps_passed >= 1:
            print("✅ New database generation works")
            print("❌ API testing failed - check test logic")
        else:
            print("❌ Database generation failed - check database models")
        
        print()
        print("🔧 Next steps:")
        print("   1. Review the error messages above")
        print("   2. Fix the identified issues")
        print("   3. Run this workflow again")
        return False

def main():
    parser = argparse.ArgumentParser(description="Complete Migration Testing Workflow")
    parser.add_argument("--quick", action="store_true", help="Skip comprehensive databases (faster testing)")
    parser.add_argument("--new-version", type=str, default="v1.1", help="Version tag for new test databases (default: v1.1)")
    parser.add_argument("--baseline-version", type=str, default="baseline", help="Baseline version for migration testing (default: baseline)")
    
    args = parser.parse_args()
    
    print("🧪 Complete Migration Testing Workflow")
    print("This script will run the complete workflow for testing migrations")
    print()
    
    # Print configuration
    mode = "🚀 Quick mode: Using minimal databases only" if args.quick else "🔬 Full mode: Using all database types"
    print(mode)
    print(f"📦 New database version: {args.new_version}")
    print(f"📋 Baseline version: {args.baseline_version}")
    
    # Get backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    # Run workflow steps
    total_steps = 3
    steps_passed = run_workflow_steps(args, backend_dir)
    
    # Print summary and return result
    return print_workflow_summary(steps_passed, total_steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
