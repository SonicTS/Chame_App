# Flexible Deletion System Documentation

## Overview

The flexible deletion system provides users with fine-grained control over how entity deletions cascade to related records. Instead of having fixed cascade behaviors, users can choose exactly what happens to each type of dependent record.

## Features

### Two Deletion Types

1. **Soft Delete** - Mark as deleted, preserves all data, can be restored
2. **Hard Delete** - Permanently remove from database, cannot be undone

### Cascade Actions

#### For Soft Delete:
- **CASCADE_SOFT_DELETE** - Also mark dependent records as deleted (can be restored)
- **CASCADE_DISABLE** - Mark dependent records as disabled/broken (unavailable but preserved)
- **CASCADE_NULLIFY** - Remove the connection but keep dependent records
- **CASCADE_IGNORE** - Keep dependent records exactly as they are (recommended for historical data)
- **CASCADE_RESTRICT** - Prevent deletion if dependencies exist

#### For Hard Delete:
- **CASCADE_HARD_DELETE** - Also permanently delete dependent records
- **CASCADE_SOFT_DELETE_DEPS** - Soft delete dependents but hard delete main entity
- **CASCADE_NULLIFY_HARD** - Remove connections but keep dependent records
- **CASCADE_RESTRICT** - Prevent deletion if dependencies exist

## Usage Examples

### Ingredient Deletion Scenarios

When deleting an ingredient, you might have products that use it:

1. **Soft Delete + CASCADE_DISABLE** (Default)
   - Ingredient is marked as deleted
   - Products using it are marked as "broken/unavailable"
   - Products can't be sold but are preserved
   - Good for temporary ingredient shortage

2. **Soft Delete + CASCADE_SOFT_DELETE**
   - Ingredient is marked as deleted
   - Products using it are also marked as deleted
   - Both can be restored together
   - Good for discontinuing product lines

3. **Soft Delete + CASCADE_NULLIFY**
   - Ingredient is marked as deleted
   - Products lose this ingredient from their recipe
   - Products remain available (if they have other ingredients)
   - Good for ingredient substitution

4. **Hard Delete + CASCADE_RESTRICT**
   - Deletion is prevented if products still use the ingredient
   - Forces you to handle products first
   - Good for data integrity

### Product Deletion Scenarios

When deleting a product, you might have sales history and pfand records:

1. **Soft Delete + CASCADE_IGNORE** (Default for sales)
   - Product is marked as deleted
   - Sales history is preserved exactly as-is
   - Maintains financial/historical integrity

2. **Hard Delete + CASCADE_NULLIFY**
   - Product is permanently deleted
   - Sales records remain but lose product reference
   - Preserves financial data but breaks product link

### User Deletion Scenarios

When deleting a user, you have sales as consumer/donator and transactions:

1. **Soft Delete + CASCADE_IGNORE** (Default for consumer sales)
   - User is marked as deleted
   - Sales where they were consumer are preserved
   - Maintains purchase history

2. **Soft Delete + CASCADE_NULLIFY** (Default for donator sales)
   - User is marked as deleted
   - Sales where they were donator lose the donator reference
   - Preserves sales but removes donation credit

## Implementation Details

### FlexibleDeletionService

The main service class that handles the deletion logic:

```python
from services.flexible_deletion_service import FlexibleDeletionService, CascadeAction

# Analyze what would be impacted
service = FlexibleDeletionService(session)
plan = service.analyze_deletion_impact('ingredient', ingredient_id)

# User chooses cascade actions
plan.user_choices['product_ingredients'] = CascadeAction.CASCADE_DISABLE

# Execute the plan
result = service.execute_deletion_plan(plan, deleted_by_user="admin")
```

### Flutter Integration

The Flutter app provides a user-friendly interface:

```dart
import 'package:chame_flutter/widgets/flexible_deletion_dialog.dart';

// Show deletion dialog with options
final result = await showFlexibleDeletionDialog(
  context: context,
  entityType: 'ingredient',
  entityId: ingredientId,
  entityName: ingredientName,
);
```

### API Integration

The admin_api.py provides functions for the Flutter bridge:

```python
# Analyze deletion impact
def get_deletion_impact_analysis(entity_type, entity_id):
    # Returns detailed analysis with dependencies and options

# Execute deletion with user choices
def enhanced_delete_ingredient(ingredient_id, deleted_by_user="admin", 
                              hard_delete=False, cascade_choices=None):
    # Executes deletion plan with user-specified cascade actions
```

## Best Practices

### For Historical Data (Sales, Transactions, Pfand)
- **Always use CASCADE_IGNORE** to preserve business records
- Only use CASCADE_NULLIFY if you specifically need to break references
- Never use CASCADE_HARD_DELETE for financial/historical data

### For Product-Ingredient Relationships
- **Use CASCADE_DISABLE** for temporary ingredient issues
- **Use CASCADE_SOFT_DELETE** when discontinuing product lines
- **Use CASCADE_NULLIFY** when replacing ingredients

### For User Data
- **Use CASCADE_IGNORE** for purchase history (consumer sales)
- **Use CASCADE_NULLIFY** for donation history (donator sales) if desired
- **Never hard delete users** with transaction history

### Safety Recommendations
1. Always analyze impact before deletion
2. Prefer soft delete over hard delete
3. Use CASCADE_RESTRICT when unsure
4. Test deletion scenarios on non-production data
5. Keep backups before bulk deletions

## Database Schema Considerations

### Required Columns for Soft Delete
All entities that support soft delete need:
- `is_deleted` (Boolean, default=False)
- `deleted_at` (DateTime, nullable=True)
- `deleted_by` (String, nullable=True)
- `is_disabled` (Boolean, default=False)
- `disabled_reason` (String, nullable=True)

### Foreign Key Handling
- Foreign keys should allow NULL for CASCADE_NULLIFY operations
- Use appropriate indexes on deletion-related columns
- Consider cascade constraints at database level as backup

## Error Handling

The system provides detailed error reporting:
- **Analysis errors** - Problems checking dependencies
- **Validation errors** - Invalid cascade choices
- **Execution errors** - Database or constraint violations
- **Business logic errors** - Custom validation failures

## Migration from Simple Deletion

To upgrade from the basic deletion system:

1. Add soft delete columns to existing tables
2. Update models to inherit from EnhancedSoftDeleteMixin
3. Replace deletion calls with flexible deletion service
4. Update frontend to use new deletion dialogs
5. Test all deletion scenarios thoroughly

## Performance Considerations

- Analysis phase may be slow for entities with many dependencies
- Consider caching dependency analysis for frequently deleted entities
- Use database transactions to ensure consistency
- Monitor performance for bulk deletion operations

## Security Considerations

- Validate user permissions before allowing deletion
- Log all deletion operations with user attribution
- Consider approval workflows for critical deletions
- Implement role-based cascade restrictions

## Testing

Test scenarios should cover:
- Each cascade action type
- Complex dependency chains
- Error conditions and rollbacks
- Performance with large datasets
- User permission boundaries
- Restoration after soft delete

This flexible deletion system provides the granular control you requested while maintaining data integrity and user safety.
