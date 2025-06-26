# Testing Framework

Comprehensive testing framework for the Chame App admin API functions.

## 🧪 Framework Components

### Core Testing Files
- **`comprehensive_api_tests.py`** - Main testing engine that validates all admin_api functions
- **`run_api_tests.py`** - Simple test runner with clean output and quick/full modes
- **`generate_test_databases.py`** - Creates different types of test databases
- **`show_testing_framework.py`** - Displays framework overview and capabilities
- **`migration_and_api_tests.py`** - Integration tests combining database migrations with API validation

### Test Databases
- **`test_databases/`** - Directory containing generated test databases

**Note**: Test database files (*.db) in this directory are tracked by git to provide
consistent test data across different development environments and deployments.

## 🚀 Quick Start

### Run Tests
```bash
# Quick health check (data fetchers only)
python run_api_tests.py --quick

# Full comprehensive test suite
python run_api_tests.py

# Or run directly
python comprehensive_api_tests.py

# Migration and API integration tests
python migration_and_api_tests.py
```

### Generate Test Databases
```bash
# Create all database types
python generate_test_databases.py all

# Create specific database type
python generate_test_databases.py minimal
python generate_test_databases.py comprehensive
python generate_test_databases.py edge
python generate_test_databases.py performance
```

### Framework Overview
```bash
python show_testing_framework.py
```

## 📊 Test Database Types

### Minimal Database
- Basic users (admin, regular user)
- Simple ingredients (bread, cheese)
- One basic product (toast)
- Perfect for quick testing

### Comprehensive Database  
- Multiple user types with different roles and balances
- Full range of ingredients with Pfand values
- Various products (toasts, drinks, sandwiches)
- Sample sales transactions
- Realistic business scenarios

### Edge Case Database
- Unicode characters in names (测试, üöä)
- Extreme values (very high/low prices, balances)
- Zero and negative balances
- Special character handling
- Error condition testing

### Performance Database
- 50+ users with varied data
- 20+ ingredients with different properties
- Large datasets for stress testing
- Performance benchmarking scenarios

## 🔗 Migration and API Integration Testing

### Overview
The migration and API integration test suite (`migration_and_api_tests.py`) provides comprehensive testing that:

1. **Tests Multiple Scenarios**: Uses all generated test databases (minimal, comprehensive, edge case, performance)
2. **Migration Testing**: Validates that database migrations work correctly on real data
3. **API Validation**: Ensures API functions work properly after migrations
4. **Data Integrity**: Verifies that data is preserved and accessible throughout the migration process

### What Gets Tested

#### Migration Process
- ✅ Schema migration execution
- ✅ Data preservation during migration
- ✅ Migration rollback capabilities
- ✅ Cross-version compatibility

#### Post-Migration API Testing
- ✅ Data fetcher functions work with migrated schema
- ✅ User operations (deposit, withdraw) function correctly
- ✅ Product and ingredient queries return valid data
- ✅ Database connections and transactions work properly

#### Integration Scenarios
- ✅ Fresh database -> migration -> API operations
- ✅ Populated database -> migration -> data integrity check
- ✅ Edge case data -> migration -> error handling validation
- ✅ Large dataset -> migration -> performance validation

### Usage Examples

```bash
# Run full migration and API integration test suite
python migration_and_api_tests.py

# The test will automatically:
# 1. Find all test databases in testing/test_databases/
# 2. Copy each to a temporary environment
# 3. Run migrations on the copied database
# 4. Test API functionality on the migrated database
# 5. Report results for each database type
```

### Sample Output

```
🚀 Starting Migration and API Integration Test Suite
======================================================================
📁 Found 4 test databases:
  • minimal_test.db
  • comprehensive_test.db
  • edge_case_test.db
  • performance_test.db

🎯 Testing database: minimal_test.db
============================================================
📄 Copied database: minimal_test.db -> test environment
🔄 Testing migration on: minimal_test.db
  📊 Analyzing pre-migration schema...
     Tables: users, ingredients, products, sales
  📋 Current version: 1.0
  📋 Available migrations: 2
  🚀 Running migrations...
  ✅ Migration completed successfully
🧪 Testing API functionality on: minimal_test.db
  🔍 Testing data fetcher functions...
  👥 Testing user operations...
    ✅ User balance operations: Success
  📊 API Test Results: 12 passed, 0 failed
✅ minimal_test.db: All tests passed

📊 FINAL TEST RESULTS
======================================================================
🎯 Total databases tested: 4
✅ Successful: 4
❌ Failed: 0

🎉 All migration and API tests passed!
💡 Your database migrations are working correctly across all test scenarios.
```

## 🧪 What Gets Tested

### User Management
- ✅ User creation (all roles: user, admin, wirt)
- ✅ Login and authentication
- ✅ Password validation and changes
- ✅ Balance operations (deposit, withdraw)
- ✅ Input validation and error handling

### Ingredient Management
- ✅ Ingredient creation with pricing
- ✅ Stock management and restocking
- ✅ Pfand (deposit) handling
- ✅ Bulk restocking operations

### Product Management
- ✅ Product creation with ingredient relationships
- ✅ Complex ingredient combinations
- ✅ Pricing calculations
- ✅ Toaster space management

### Sales Operations
- ✅ Purchase processing
- ✅ Balance validation
- ✅ Stock deduction
- ✅ Pfand return processing
- ✅ Toast round group orders

### Data Access
- ✅ All `get_all_*()` functions
- ✅ Filtered transaction queries
- ✅ Bank operations and tracking
- ✅ Data integrity validation

### Edge Cases
- ✅ Unicode and special characters
- ✅ Extreme values and boundaries
- ✅ Error conditions and validation
- ✅ Concurrent operation simulation

## 📈 Understanding Results

### Success Rate Indicators
- **≥90%**: Excellent - API working correctly
- **75-89%**: Good - Minor issues to address
- **<75%**: Needs attention - Review errors

### Sample Output
```
📈 TEST RESULTS SUMMARY
==================================================
✅ Passed: 48
❌ Failed: 3
📊 Success Rate: 94.1%

⚠️ Issues found:
  • submit_pfand_return: validation error
  • add_toast_round: insufficient balance handling

💾 Test database: /tmp/api_test_xyz/test_api.db
   ↳ Contains realistic test data for inspection
```

## 🔧 Customizing Tests

### Adding New Test Cases
1. Edit `comprehensive_api_tests.py`
2. Add methods to appropriate test sections
3. Use `_test_function()` helper for consistency

### Creating Custom Test Data
1. Modify `generate_test_databases.py`
2. Add new database creation methods
3. Customize data sets for specific scenarios

### Running Specific Tests
```python
from comprehensive_api_tests import ComprehensiveAPITester

tester = ComprehensiveAPITester()
tester.setup_test_environment()
tester.create_test_database()
tester.populate_generic_test_data()

# Run specific test sections
results = {'passed': 0, 'failed': 0, 'errors': []}
tester._test_user_management(results)
```

## 🐛 Debugging Failed Tests

### 1. Check Error Messages
- Review console output for specific errors
- Look for function names and parameters in error details

### 2. Inspect Test Database
- Open preserved database with SQLite browser
- Verify data was created correctly
- Check table contents and relationships

### 3. Manual Function Testing
```python
import sys
import os
sys.path.append('..')
import services.admin_api as api

# Create database and test manually
api.create_database()
api.add_user("test", 50.0, "user")
users = api.get_all_users()
print(users)
```

### 4. Debug Output
- Many functions include debug prints
- Check console for detailed execution information
- Enable additional logging if needed

## 📁 File Structure

```
testing/
├── comprehensive_api_tests.py  # Main test engine
├── run_api_tests.py           # Test runner
├── generate_test_databases.py # Database generator
├── show_testing_framework.py  # Framework overview
├── test_databases/            # Generated databases
│   ├── minimal_test.db
│   ├── comprehensive_test.db
│   ├── edge_case_test.db
│   └── performance_test.db
└── README.md                  # This file
```

## 🔄 CI/CD Integration

The framework is designed for automated testing:

```bash
# Basic CI command
cd testing
python comprehensive_api_tests.py
if [ $? -eq 0 ]; then
    echo "✅ All API tests passed"
else
    echo "❌ API tests failed - check output"
    exit 1
fi
```

## 💡 Best Practices

### For Development
1. Run `--quick` tests during active development
2. Run full tests before committing changes
3. Generate fresh databases when models change
4. Add custom tests for new business logic

### For Production
1. Run full test suite in CI/CD pipeline
2. Test with performance database for load scenarios
3. Monitor success rates over time
4. Validate edge cases are handled properly

---

**Start testing:** `python run_api_tests.py --quick`
