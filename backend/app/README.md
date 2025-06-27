# Chame App Backend

This is the backend application for the Chame system, providing API functionality and database management.

## 📁 Project Structure

```
backend/app/
├── 📂 chame_app/          # Core application code
│   ├── __init__.py
│   ├── __main__.py        # Application entry point
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection setup
│   └── database_instance.py  # Database instance management
├── 📂 models/             # Database models
│   ├── user_table.py      # User model
│   ├── product_table.py   # Product model
│   ├── ingredient.py      # Ingredient model
│   ├── sales_table.py     # Sales model
│   └── ...               # Other models
├── 📂 services/           # Business logic services
│   ├── admin_api.py       # Main admin API functions
│   └── admin_webpage.py   # Web interface
├── 📂 testing/           # Testing framework
│   ├── comprehensive_api_tests.py  # Complete API test suite with CLI
│   ├── generate_test_databases.py  # Test database generator
│   ├── migration_and_api_tests.py  # Migration testing suite
│   ├── show_testing_framework.py   # Framework overview
│   └── test_databases/             # Generated test databases (tracked in git)
├── 📂 docs/              # Documentation
│   └── API_TESTING.md    # Testing documentation
├── 📂 scripts/           # Utility scripts
│   └── build_executeable.bat  # Build script
├── 📂 build/             # Build artifacts
├── config.py             # Main configuration
├── requirements.txt      # Python dependencies
└── kassensystem.db       # Main database file
```

## 🚀 Quick Start

### Running the Application
```bash
python -m chame_app
```

### Testing the API
```bash
# Quick health check using minimal database
python testing/comprehensive_api_tests.py --database-type minimal

# Full test suite using comprehensive database
python testing/comprehensive_api_tests.py --database-type comprehensive

# List available test databases
python testing/comprehensive_api_tests.py --list-databases

# Generate test databases (if missing)
python testing/generate_test_databases.py all
```

### Building Executable
```bash
# Run the build script
scripts\build_executeable.bat
```

## 📚 Documentation

- **[API Testing Guide](docs/API_TESTING.md)** - Comprehensive testing framework documentation
- **Testing Framework Overview** - Run `python testing/show_testing_framework.py`

## 🧪 Testing

The `testing/` directory contains a complete testing framework:

- **comprehensive_api_tests.py** - Complete API test suite with CLI for version/database selection
- **generate_test_databases.py** - Creates various test database scenarios with version support
- **migration_and_api_tests.py** - Tests database migrations and validates API functionality
- **show_testing_framework.py** - Displays framework capabilities and usage examples

### Test Database Types
- **Minimal** - Basic entities for quick testing
- **Comprehensive** - Realistic business data
- **Edge Cases** - Unicode, extremes, error conditions
- **Performance** - Large datasets for stress testing

## 🛠️ Development

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### Database Management
- Main database: `kassensystem.db`
- Test databases: `testing/test_databases/`
- Migrations: `chame_app/simple_migration/`

### Code Organization
- **Models** - Database table definitions
- **Services** - Business logic and API functions
- **Testing** - Comprehensive test framework
- **Scripts** - Build and utility scripts
- **Docs** - Documentation and guides

## 🔧 Configuration

Main configuration is handled in:
- `config.py` - Application settings
- `chame_app/config.py` - Core configuration
- Environment variables for database paths

## 📊 Key Features

- ✅ User management (roles, authentication, balance)
- ✅ Product and ingredient management
- ✅ Sales and transaction tracking
- ✅ Bank operations and financial tracking
- ✅ Toast round group ordering
- ✅ Pfand (deposit) return system
- ✅ Comprehensive testing framework
- ✅ Database migrations support
- ✅ Web interface for administration

## 🎯 API Functions

The main API functions are in `services/admin_api.py`:

### User Management
- `add_user()` - Create users with roles
- `login()` - Authenticate users
- `deposit()` / `withdraw()` - Manage balances
- `change_password()` - Update credentials

### Product Management  
- `add_ingredient()` - Create ingredients with pricing
- `add_product()` - Create products from ingredients
- `restock_ingredient()` - Manage inventory

### Sales Operations
- `make_purchase()` - Process sales
- `submit_pfand_return()` - Handle returns
- `add_toast_round()` - Group orders

### Data Access
- `get_all_*()` functions - Retrieve entities
- `get_filtered_transaction()` - Transaction filtering
- `get_bank()` - Financial data

## 🚨 Testing Your Changes

Before committing changes:

1. **Quick Test**: `python testing/comprehensive_api_tests.py --database-type minimal`
2. **Full Test**: `python testing/comprehensive_api_tests.py --database-type comprehensive` 
3. **Check Results**: Review any failed tests and success rate
4. **Inspect Data**: Examine preserved test databases in temp directory

## 📈 Success Metrics

The testing framework provides success rates:
- **≥90%**: Excellent - Ready for production
- **75-89%**: Good - Minor issues to address  
- **<75%**: Needs attention - Check errors

---

**Ready to develop!** Start with the testing framework to ensure everything works correctly.
