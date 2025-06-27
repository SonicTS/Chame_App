# Migration Testing Workflow

This document explains the recommended workflow for testing database migrations and API functionality.

## Overview

The migration testing system ensures that:
1. Old databases can be successfully migrated to the new schema
2. Migrated databases pass all current API tests
3. New features work correctly on both fresh and migrated data

## Workflow Steps

### 1. Code Development Phase
When you make changes to your database schema or add new features:

1. **Update database models** in `models/` directory
2. **Write new tests** in `testing/comprehensive_api_tests.py` for new functionality
3. **Generate new test databases** with the new schema:
   ```bash
   python testing/generate_test_databases.py all --version v1.1
   ```

### 2. Test Validation Phase
Ensure your new tests work correctly:

1. **Run tests on new databases** to verify they pass:
   ```bash
   python testing/comprehensive_api_tests.py
   ```
   This will automatically use the latest generated databases.

2. **Test specific database version/type** if needed:
   ```bash
   python testing/comprehensive_api_tests.py --version v1.1 --database-type comprehensive
   ```

3. **List available test databases**:
   ```bash
   python testing/comprehensive_api_tests.py --list-databases
   ```

### 3. Migration Development Phase
Write migration functions to update old databases:

1. **Update migration functions** in `chame_app/simple_migrations.py`
2. Add new migration steps for your schema changes
3. Test migration logic manually if needed

### 4. Migration Validation Phase
Test that your migrations work correctly:

1. **Run migration tests** on old databases:
   ```bash
   python testing/migration_and_api_tests.py
   ```
   
   This will:
   - Take old databases from `testing/test_databases/baseline/`
   - Run migrations on them
   - Run current API tests on the migrated databases
   - Report success/failure

2. **Debug migration issues** if tests fail:
   - Check migration logs for SQL errors
   - Verify foreign key constraints
   - Ensure data integrity is maintained

## Directory Structure

```
testing/test_databases/
├── baseline/           # Old schema databases (before migration)
│   ├── minimal_test.db
│   ├── comprehensive_test.db
│   └── edge_case_test.db
└── v1.0/              # Current schema databases (after migration)
    ├── minimal_test.db
    ├── comprehensive_test.db
    └── edge_case_test.db
```

## VS Code Tasks

Use the following VS Code tasks for common operations:

- **API Tests: Quick Health Check**: Run basic API tests
- **API Tests: Full Comprehensive Suite**: Run all API tests
- **Generate Test Database: All Types**: Generate all test database types
- **Migration Tests: Modern Migration Testing**: Run migration tests with API validation
- **Migration Workflow: Complete Testing Workflow**: Run complete migration workflow
- **Migration Workflow: Quick Testing Workflow**: Run quick migration workflow

## Command Examples

### Generate new test databases with current schema:
```bash
python testing/generate_test_databases.py all --version v1.1
```

### Test migrations from baseline to current:
```bash
python testing/migration_and_api_tests.py --baseline-version baseline
```

### Test a single database migration:
```bash
python testing/migration_and_api_tests.py --single-test minimal_test.db
```

### Run only API tests (no migration):
```bash
python testing/comprehensive_api_tests.py
```

## Best Practices

1. **Always test new features** on fresh databases first
2. **Write comprehensive tests** before implementing migrations
3. **Test migrations** on multiple database types (minimal, comprehensive, edge cases)
4. **Keep baseline databases** as reference points for older schema versions
5. **Version your test databases** when making significant schema changes
6. **Document migration steps** in your migration functions

## Troubleshooting

### Common Issues

1. **"Database is locked" errors**:
   - Ensure all database connections are properly closed
   - Check for background processes using the database

2. **Foreign key constraint errors**:
   - Verify foreign key relationships in migration scripts
   - Check that referenced tables exist before creating relationships

3. **Migration fails but no clear error**:
   - Run with verbose logging enabled
   - Check individual migration steps manually

4. **API tests pass on new databases but fail on migrated ones**:
   - Check data integrity after migration
   - Verify all required fields are populated correctly
   - Compare schema between migrated and fresh databases

### Getting Help

1. Check migration logs in the console output
2. Use `--single-test` to isolate issues to specific databases
3. Run API tests separately to verify test logic
4. Review migration functions for edge cases
