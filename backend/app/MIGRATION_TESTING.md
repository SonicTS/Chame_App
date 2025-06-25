# Migration Testing Guide - Baseline Database Approach

## Overview

This testing framework uses **real baseline databases** created from your actual application data to test migrations. This approach ensures:
- Migrations work with real production-like data
- Data integrity is preserved during schema changes
- All admin API functions work after migration
- Migrations are idempotent (can be run multiple times safely)

## Baseline Database Workflow

### 1. **Create Baseline Database**
```bash
# 1. Save your migration changes
git stash push -m "migration changes"

# 2. Switch to original branch (without migrations)
git checkout main

# 3. Run your app and create real data
python -m chame_app  # or however you start your app
# Use the app UI to create users, products, sales, etc.

# 4. Copy the database
cp kassensystem.db baseline.db

# 5. Switch back to migration branch
git checkout feature/migrations
git stash pop

# 6. Run tests
python run_migration_tests.py
```

### 2. **Test Structure**
- **Baseline Database**: Your real application database with actual data
- **Test Database**: Copy of baseline used for testing (disposable)
- **Migrated Database**: Result after running migrations (can become new baseline)

### 3. **Migration Testing Cycle**
1. **Copy baseline** → Create test database
2. **Run migrations** → Apply your schema changes
3. **Validate results** → Check schema and data integrity
4. **Test API functions** → Ensure everything still works
5. **Save success** → Optionally update baseline for future tests

## How to Run Tests

### Option 1: Simple Test Runner
```bash
cd backend/app
python run_migration_tests.py
```

### Option 2: Pytest (more detailed output)
```bash
cd backend/app
pytest test_migrations.py -v
```

### Option 3: Specific Test
```bash
cd backend/app
pytest test_migrations.py::TestMigrations::test_migration_from_v1 -v
```

## What Gets Tested

### Schema Validation
- ✅ Required tables exist after migration
- ✅ Required columns exist in correct tables
- ✅ Foreign keys are properly set up
- ✅ Migration tracking table is created

### Data Preservation
- ✅ No data loss during migration
- ✅ Data is properly backfilled (user_id → consumer_id)
- ✅ Relationships are maintained
- ✅ Counts match before and after

### API Functionality
- ✅ All getter functions work (get_all_users, get_all_products, etc.)
- ✅ Create functions work (add_user, add_ingredient, etc.)
- ✅ Update functions work (change_password, etc.)
- ✅ Transaction functions work (withdraw, deposit, etc.)

### Migration Safety
- ✅ Migrations are idempotent
- ✅ Partial migrations can be completed
- ✅ Rollback capability (where possible)
- ✅ Error handling and recovery

## Test Scenarios

### Scenario 1: Fresh Installation
- New database with latest schema
- No migration needed
- All APIs should work immediately

### Scenario 2: Migration from V1
- Old schema with `user_id` in sales
- Needs full migration path
- Data backfill required

### Scenario 3: Migration from V2
- Intermediate schema
- Partial migration already applied
- Should complete remaining steps

### Scenario 4: Re-running Migrations
- Migration already completed
- Should be no-op
- No data should be affected

## Adding New Tests

### For New Migrations
1. Update `_get_migrations()` in `simple_migrations.py`
2. Add new legacy database version in `test_migrations.py`
3. Add validation rules for new schema changes
4. Test new API functions if added

### For New API Functions
1. Add function to `test_functions` list in `_test_admin_api_functions()`
2. Add any specific validation needed
3. Consider edge cases and error conditions

## Continuous Integration

The GitHub Actions workflow automatically runs migration tests on:
- Push to main/develop branches
- Pull requests to main
- Changes to backend code

## Troubleshooting

### Common Issues

1. **"Table already exists" errors**
   - Usually means migration tracking is off
   - Check `schema_migrations` table
   - Clear test database and retry

2. **Data validation failures**
   - Check that legacy database creation matches old schema exactly
   - Verify migration SQL matches expected changes
   - Look for null values where they shouldn't be

3. **API function failures**
   - Check that all required test data exists
   - Verify foreign key relationships
   - Check for missing migrations

### Debug Mode
Add this to get more detailed output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### When Writing Migrations
1. **Always backup data** before destructive operations
2. **Test on copy of production data** before deployment
3. **Make migrations reversible** where possible
4. **Handle edge cases** (null values, missing data, etc.)
5. **Use transactions** to ensure atomicity

### When Adding Tests
1. **Test both success and failure paths**
2. **Include edge cases** (empty tables, null values, etc.)
3. **Verify data integrity** after each major change
4. **Test performance** with larger datasets
5. **Document expected behavior** clearly

## Migration Checklist

Before deploying a new migration:
- [ ] Written migration SQL
- [ ] Added to simple_migrations.py
- [ ] Created legacy database version for testing
- [ ] Added validation rules
- [ ] Tested all admin API functions
- [ ] Verified idempotency
- [ ] Tested rollback (if applicable)
- [ ] Ran full test suite
- [ ] Documented changes

## Performance Considerations

### For Large Databases
- Consider adding progress logging for long operations
- Use batched updates for large data migrations
- Test with realistic data volumes
- Monitor memory usage during migrations
- Consider migration time windows

### Example Performance Test
```python
def test_migration_performance(self):
    # Create large legacy database
    large_db = self.create_large_legacy_database(rows=100000)
    
    import time
    start_time = time.time()
    
    # Run migration
    self.test_migration_from_version(large_db, "performance_test")
    
    end_time = time.time()
    migration_time = end_time - start_time
    
    # Assert reasonable time limit
    assert migration_time < 60, f"Migration took {migration_time}s, should be under 60s"
```
