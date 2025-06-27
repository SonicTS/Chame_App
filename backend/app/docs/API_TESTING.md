# API Testing Framework Documentation

This directory contains a comprehensive testing framework for the `admin_api.py` functions. The framework provides several tools for different testing scenarios.

## 🧪 Available Testing Tools

### 1. Comprehensive API Tests (`comprehensive_api_tests.py`)
**Main testing framework that validates all admin_api functions**

**Features:**
- Creates temporary test database with realistic data
- Tests every function in `admin_api.py`
- Includes edge cases and error scenarios
- Preserves test database for manual inspection
- Reports detailed results with success/failure rates

**Usage:**
```bash
python comprehensive_api_tests.py
python comprehensive_api_tests.py --database-type minimal
python comprehensive_api_tests.py --version v1.0
python comprehensive_api_tests.py --list-databases
python comprehensive_api_tests.py --inspect all
python comprehensive_api_tests.py --inspect v1.0 --inspect-detailed
```

**What it tests:**
- ✅ User management (add, deposit, withdraw, login, password change)
- ✅ Ingredient management (add, restock)
- ✅ Product management (add with ingredients)
- ✅ Purchase operations (make_purchase, pfand_return)
- ✅ Bank operations (withdraw)
- ✅ Data fetchers (get_all_* functions)
- ✅ Authentication (login, password validation)
- ✅ Edge cases (unicode, special characters, extreme values)

### 2. Quick Test Runner (`run_api_tests.py`)
**Simplified test runner with clear summary output**

**Usage:**
```bash
python run_api_tests.py           # Full test suite
python run_api_tests.py --quick   # Quick tests only
python run_api_tests.py --help    # Show help
```

**Output:**
- Clear pass/fail summary
- Success rate percentage
- List of any issues found
- Database location for inspection

### 3. Test Database Generator (`generate_test_databases.py`)
**Creates different types of test databases for manual testing**

**Usage:**
```bash
python generate_test_databases.py all            # Create all database types
python generate_test_databases.py minimal        # Basic database
python generate_test_databases.py comprehensive  # Full featured database
python generate_test_databases.py edge          # Edge cases database
python generate_test_databases.py performance   # Large database for performance testing
```

**Database Types:**
- **Minimal**: Basic users, ingredients, and products for quick testing
- **Comprehensive**: Realistic data with multiple users, products, sales
- **Edge Case**: Unicode characters, extreme values, special cases
- **Performance**: Large datasets for stress testing

### 4. Database Inspection Tools
**Built-in tools to examine test database contents**

**Features:**
- List all available test databases across versions
- Inspect table contents and schema information
- Compare database structures between versions
- View sample data for understanding test scenarios

**Usage:**
```bash
# List all available test databases
python comprehensive_api_tests.py --list-databases

# Inspect table contents (basic overview)
python comprehensive_api_tests.py --inspect                    # Latest version
python comprehensive_api_tests.py --inspect all               # All versions
python comprehensive_api_tests.py --inspect v1.0              # Specific version

# Detailed inspection with column info and sample data
python comprehensive_api_tests.py --inspect all --inspect-detailed
python comprehensive_api_tests.py --inspect v1.0 --inspect-detailed
```

**What Inspection Shows:**
- Database versions and types available
- Table names and record counts
- Column names and data types (with `--inspect-detailed`)
- Sample data for small tables (with `--inspect-detailed`)
- Schema differences between versions

**Example Output:**
```
📋 Available Test Databases:
========================================

📦 Version: v1.0
  • minimal: minimal_test.db
  • comprehensive: comprehensive_test.db
  • edge: edge_case_test.db

🎯 Latest version: v1.0

🔍 Database Table Inspection
============================================================
📊 Database: comprehensive (comprehensive_test.db)
  📋 users: 8 records
     Columns: id, name, balance, role, password_hash
     Sample data:
       Row 1: {'id': 1, 'name': 'admin', 'balance': 100.0, 'role': 'admin'}
  📋 products: 6 records
     Columns: id, name, category, price, toaster_space
```

## 📊 Test Database Contents

### Generic Test Data Includes:
- **Users**: Admin, manager, regular users with various balances (including edge cases like negative balance)
- **Ingredients**: Common ingredients with different prices, stock levels, and Pfand values
- **Products**: Various toast products, drinks, sandwiches with realistic pricing
- **Sales**: Sample transactions between users and products
- **Toast Rounds**: Group ordering scenarios

### Edge Cases Covered:
- Unicode characters in names (测试, üöä)
- Extreme values (very high/low prices, balances)
- Zero and negative values where appropriate
- Special characters and formatting
- Empty/null inputs
- Invalid combinations

## 🔧 Setup and Requirements

### Dependencies:
```bash
pip install sqlalchemy passlib argon2-cffi flask
```

### Environment:
- The tests create temporary databases in system temp directories
- Original database is not affected
- Test databases are preserved for inspection

## 📈 Interpreting Results

### Success Rates:
- **≥90%**: Excellent - API is working correctly
- **75-89%**: Good - Minor issues that should be addressed
- **<75%**: Needs attention - Check error details

### Common Test Failures:
1. **Database connection issues**: Check SQLAlchemy setup
2. **Missing dependencies**: Install required packages
3. **Invalid data format**: Check model field names and types
4. **Business logic errors**: Review function implementations

## 🚀 Quick Start Guide

### 1. Run Full Test Suite:
```bash
python comprehensive_api_tests.py
```

### 2. Generate Test Databases:
```bash
python generate_test_databases.py all
```

### 3. Quick Health Check:
```bash
python run_api_tests.py --quick
```

### 4. Manual Testing:
1. Generate a test database: `python generate_test_databases.py comprehensive`
2. Copy the generated database to your working directory
3. Run your application with the test data
4. Manually verify functionality

## 🛠️ Customizing Tests

### Adding New Test Cases:
1. Edit `comprehensive_api_tests.py`
2. Add test methods to appropriate test sections
3. Use the `_test_function()` helper method for consistency

### Creating Custom Test Data:
1. Modify `generate_test_databases.py`
2. Add new database creation methods
3. Customize data sets for specific scenarios

### Testing Specific Functions:
1. Import the tester class: `from comprehensive_api_tests import ComprehensiveAPITester`
2. Call specific test methods: `tester._test_user_management(results)`

## 📁 Output Files

### Test Results:
- Console output with detailed pass/fail information
- Test databases preserved at reported locations
- Error details for failed tests

### Generated Databases:
- Saved in `test_databases/` directory
- Named by type: `minimal_test.db`, `comprehensive_test.db`, etc.
- Can be opened with SQLite browser for inspection

## 🔍 Debugging Failed Tests

### 1. Check Error Messages:
- Look for specific error details in test output
- Pay attention to function names and parameters

### 2. Inspect Test Database:
- Open preserved database with SQLite browser
- Verify data was created correctly
- Check table contents and relationships

### 3. Manual Function Testing:
```python
import services.admin_api as api
api.create_database()
# Test individual functions manually
```

### 4. Enable Debug Output:
- Many functions include debug prints
- Check console for detailed execution information

## 💡 Best Practices

### For Development:
1. Run tests after making changes to `admin_api.py`
2. Use `--quick` flag for rapid feedback during development
3. Generate fresh test databases when data models change
4. Keep test databases for regression testing

### For Production:
1. Run full test suite before deployment
2. Test with realistic data volumes (performance database)
3. Verify edge cases are handled correctly
4. Document any expected test failures

## 🎯 Test Coverage

The framework tests **every public function** in `admin_api.py`:

### User Functions:
- `add_user()` - Valid/invalid scenarios
- `login()` - Authentication testing
- `change_password()` - Password validation
- `deposit()` / `withdraw()` - Money operations

### Product/Ingredient Functions:
- `add_ingredient()` - With/without Pfand
- `add_product()` - Complex ingredient relationships
- `restock_ingredient()` / `restock_ingredients()` - Stock management

### Transaction Functions:
- `make_purchase()` - Purchase validation
- `submit_pfand_return()` - Return processing
- `add_toast_round()` - Group orders

### Data Access Functions:
- All `get_all_*()` functions
- `get_filtered_transaction()` - With various filters
- `get_bank()` / `get_bank_transaction()` - Bank operations

### Bank Functions:
- `bank_withdraw()` - Cash management

## 🔄 Continuous Integration

The testing framework is designed to work in CI environments:

```bash
# Basic CI test command
python comprehensive_api_tests.py
if [ $? -eq 0 ]; then
    echo "✅ All API tests passed"
else
    echo "❌ API tests failed"
    exit 1
fi
```

This comprehensive testing framework ensures your admin API functions work correctly across all scenarios and provides the confidence needed for production deployment.
