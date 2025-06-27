# VS Code Tasks for Chame Project

This document explains all the VS Code tasks available for the Chame project backend. These tasks can be accessed through the VS Code Command Palette (`Ctrl+Shift+P`) by typing "Tasks: Run Task".

## 🧪 Testing Tasks

### Quick Testing
- **API Tests: Quick Health Check**
  - Runs a fast health check using minimal test database
  - Perfect for quick validation during development
  - Uses generated minimal test database for realistic but fast testing
  - Command: `python testing/comprehensive_api_tests.py --database-type minimal`

### Comprehensive Testing
- **API Tests: Full Comprehensive Suite**
  - Runs the complete test suite using comprehensive test database
  - Includes all functions, edge cases, and error handling with realistic data
  - Uses generated comprehensive test database with extensive test scenarios
  - Command: `python testing/comprehensive_api_tests.py --database-type comprehensive`

- **API Tests: Direct Comprehensive (Detailed Output)**
  - Runs comprehensive tests directly with verbose output
  - Shows detailed test progress and preserves test database
  - Best for debugging and detailed validation
  - Command: `python testing/comprehensive_api_tests.py`

### Integration Testing
- **Migration & API Tests: Full Integration Suite**
  - Tests database migrations combined with API functionality
  - Uses all test databases (minimal, comprehensive, edge case, performance)
  - Validates data integrity throughout migration process
  - Takes 5-10 minutes to complete
  - Command: `python testing/migration_and_api_tests.py`

- **Migration Tests: Modern Migration Testing**
  - Runs comprehensive migration tests with API validation
  - Uses versioned test databases and modern workflow
  - Tests that migrated databases work correctly with current API
  - **RECOMMENDED** for all migration testing
  - Command: `python testing/migration_and_api_tests.py`

- **Migration Workflow: Complete Testing Workflow**
  - Runs the complete migration testing workflow from start to finish
  - Generates new databases → Tests APIs → Tests migrations → Validates results
  - Best for comprehensive validation before releases
  - Takes 10-15 minutes to complete
  - Command: `python testing/workflow_demo.py`

- **Migration Workflow: Quick Testing Workflow**
  - Runs streamlined migration workflow using minimal databases only
  - Faster validation for development iterations
  - Same steps as complete workflow but with smaller datasets
  - Takes 3-5 minutes to complete
  - Command: `python testing/workflow_demo.py --quick`

## 🗄️ Database Generation Tasks

### Generate All Test Databases
- **Generate Test Database: All Types**
  - Creates all four types of test databases
  - Includes minimal, comprehensive, edge case, and performance databases
  - Command: `python testing/generate_test_databases.py all`

### Generate Specific Test Databases
- **Generate Test Database: Minimal**
  - Creates a basic database with essential test data
  - Perfect for quick manual testing
  - Command: `python testing/generate_test_databases.py minimal`

- **Generate Test Database: Comprehensive**
  - Creates a realistic database with business-like data
  - Contains complex relationships and realistic scenarios
  - Command: `python testing/generate_test_databases.py comprehensive`

- **Generate Test Database: Edge Cases**
  - Creates a database with edge cases, unicode, and extreme values
  - Perfect for testing error handling and validation
  - Command: `python testing/generate_test_databases.py edge`

- **Generate Test Database: Performance**
  - Creates a large database for stress testing
  - Contains thousands of records for performance validation
  - Command: `python testing/generate_test_databases.py performance`

## 🔧 Utility Tasks

### Database Inspection
- **Database Inspection: List All Databases**
  - Lists all available test databases and their types
  - Shows version information and database types available
  - Quick way to see what test data is available
  - Command: `python testing/comprehensive_api_tests.py --list-databases`

- **Database Inspection: Inspect All Versions**
  - Shows table contents for all test database versions
  - Displays record counts for each table in each database
  - Perfect for understanding test data structure across versions
  - Command: `python testing/comprehensive_api_tests.py --inspect all`

- **Database Inspection: Detailed Inspection (All Versions)**
  - Shows detailed table information including column names and sample data
  - Provides comprehensive view of database schemas and content
  - Includes sample records for small tables
  - Command: `python testing/comprehensive_api_tests.py --inspect all --inspect-detailed`

- **Database Inspection: Inspect Latest Version**
  - Shows table contents for only the latest test database version
  - Faster than inspecting all versions when you only need current data
  - Command: `python testing/comprehensive_api_tests.py --inspect`

### Framework Information
- **Testing Framework: Show Overview**
  - Displays comprehensive information about the testing framework
  - Shows available components, usage examples, and status
  - Command: `python testing/show_testing_framework.py`

### Build and Run Tasks
- **Build: Create Executable**
  - Builds a standalone executable using PyInstaller
  - Creates executable in the `build/` directory
  - Command: `scripts\build_executeable.bat`

- **Run Main Application**
  - Starts the main Chame application
  - Runs the backend server and admin interface
  - Command: `python -m chame_app`

## 📋 How to Use VS Code Tasks

1. **Open Command Palette**: Press `Ctrl+Shift+P`
2. **Find Tasks**: Type "Tasks: Run Task"
3. **Select Task**: Choose from the list of available tasks
4. **View Output**: Task output appears in the VS Code terminal

### Keyboard Shortcuts
- `Ctrl+Shift+P` → "Tasks: Run Task" → Quick access to all tasks
- `Ctrl+Shift+B` → Default build task (if configured)

## 🔄 Common Workflows

### Development Workflow
1. **Quick Health Check**: Run "API Tests: Quick Health Check" during development
2. **Full Testing**: Run "API Tests: Full Comprehensive Suite" before committing
3. **Generate Fresh Data**: Use "Generate Test Database: Minimal" for manual testing
4. **Inspect Data**: Use "Database Inspection: List All Databases" to see available test data

### Debugging Workflow
1. **Generate Edge Cases**: Use "Generate Test Database: Edge Cases"
2. **Detailed Testing**: Run "API Tests: Direct Comprehensive (Detailed Output)"
3. **Inspect Database Structure**: Use "Database Inspection: Detailed Inspection (All Versions)"
4. **Manual Inspection**: Open generated test databases in SQLite browser

### Database Investigation Workflow
1. **List Available Data**: Use "Database Inspection: List All Databases"
2. **Quick Structure View**: Use "Database Inspection: Inspect Latest Version"
3. **Detailed Analysis**: Use "Database Inspection: Detailed Inspection (All Versions)"
4. **Generate Missing Data**: Use appropriate "Generate Test Database" tasks as needed

### Migration Testing Workflow
1. **Complete Workflow**: Use "Migration Workflow: Complete Testing Workflow" for full validation
2. **Quick Workflow**: Use "Migration Workflow: Quick Testing Workflow" for faster testing
3. **Modern Migration Testing**: Use "Migration Tests: Modern Migration Testing" for migration-only testing

### Release Workflow
1. **Comprehensive Testing**: Run "API Tests: Full Comprehensive Suite"
2. **Performance Testing**: Generate and test with performance database
3. **Build Executable**: Use "Build: Create Executable"

## 📊 Task Groups

Tasks are organized into logical groups:
- **Test Group**: All testing-related tasks (API tests, migration tests, integration tests)
- **Build Group**: Database generation, building, inspection, and utility tasks

## 🎯 Quick Reference

| Task Type | Quick | Full | Detailed | Integration |
|-----------|-------|------|----------|-------------|
| **Health Check** | ✅ Quick Health Check | ✅ Full Comprehensive | ✅ Direct Comprehensive | ✅ Migration & API Tests |
| **Time** | ~30 seconds | 2-5 minutes | 3-7 minutes | 5-10 minutes |
| **Output** | Clean summary | Clean summary | Verbose details | Comprehensive report |
| **Database** | Temporary | Temporary | Preserved | Multiple test scenarios |

## 🛠️ Troubleshooting

### Task Not Found
- Ensure you're in the correct workspace folder
- Check that VS Code has loaded the workspace correctly
- Reload VS Code window if necessary

### Python Not Found
- Ensure Python is installed and in PATH
- Check that you're in the `backend/app` directory context
- Verify Python environment is properly configured

### Permission Errors
- Run VS Code as administrator if needed (Windows)
- Check file permissions in the project directory
- Ensure no antivirus software is blocking file access

## 📁 File Locations

All tasks execute from the `backend/app` directory context:
- **Testing Scripts**: `backend/app/testing/`
- **Documentation**: `backend/app/docs/`
- **Build Scripts**: `backend/app/scripts/`
- **Generated Databases**: `backend/app/testing/test_databases/`

## 🔗 Related Documentation

- `backend/app/docs/API_TESTING.md` - Complete testing documentation
- `backend/app/testing/README.md` - Testing framework overview
- `backend/app/scripts/README.md` - Build scripts documentation
- `backend/app/docs/README.md` - Documentation index

---

*This document covers all VS Code tasks configured for the Chame project. For more detailed information about the testing framework itself, see the documentation in `backend/app/docs/`.*
