# Hard Delete Implementation Guide

## Overview

The Chame Cafe system now supports both **soft delete** and **hard delete** operations with configurable cascade rules. This document explains the hard delete functionality, its cascade rules, and how to use it safely.

## Hard Delete vs Soft Delete

### Soft Delete
- Records are marked as deleted but remain in the database
- `is_deleted` flag is set to `True`
- Records can be restored
- Historical data is preserved
- Related records can be disabled or left untouched

### Hard Delete
- Records are permanently removed from the database
- Cannot be undone
- Related records are handled based on cascade rules
- Should be used with extreme caution

## Hard Delete Cascade Rules

### Available Cascade Types

1. **CASCADE_HARD_DELETE** - Also permanently delete related records
2. **CASCADE_NULLIFY** - Set foreign key references to NULL (preserves records)
3. **CASCADE_RESTRICT** - Prevent deletion if related records exist
4. **CASCADE_SOFT_DELETE** - Soft delete related records instead

### Model-Specific Rules

#### Product Hard Delete Rules
```python
_hard_delete_rules = [
    HardDeleteCascadeRule(
        "sales",
        HardDeleteCascadeRule.CASCADE_NULLIFY,  # Preserve sales history
        cascade_order=1
    ),
    HardDeleteCascadeRule(
        "pfand_history", 
        HardDeleteCascadeRule.CASCADE_NULLIFY,  # Preserve pfand history
        cascade_order=1
    ),
    HardDeleteCascadeRule(
        "product_ingredients",
        HardDeleteCascadeRule.CASCADE_HARD_DELETE,  # Remove associations
        cascade_order=0  # Delete these first
    )
]
```

#### Ingredient Hard Delete Rules
```python
_hard_delete_rules = [
    HardDeleteCascadeRule(
        "ingredient_products",
        HardDeleteCascadeRule.CASCADE_RESTRICT,  # Prevent if products use it
        condition_callback=lambda pi: pi.product and pi.product.is_available,
        cascade_order=0
    )
]
```

#### User Hard Delete Rules
```python
_hard_delete_rules = [
    HardDeleteCascadeRule(
        "sales",
        HardDeleteCascadeRule.CASCADE_NULLIFY,  # Preserve sales history
        cascade_order=1
    ),
    HardDeleteCascadeRule(
        "donated_sales",
        HardDeleteCascadeRule.CASCADE_NULLIFY,  # Preserve donations
        cascade_order=1
    ),
    HardDeleteCascadeRule(
        "pfand_history",
        HardDeleteCascadeRule.CASCADE_NULLIFY,  # Preserve pfand history
        cascade_order=1
    )
]
```

## Usage Examples

### Basic Hard Delete

```python
# Hard delete a user (will fail if restrictions apply)
user = session.query(User).filter_by(user_id=123).first()
try:
    user.hard_delete(session=session, deleted_by_user="admin")
    session.commit()
except ValueError as e:
    print(f"Deletion restricted: {e}")
    session.rollback()
```

### Force Hard Delete

```python
# Force hard delete (bypasses restrictions - DANGEROUS!)
user.hard_delete(session=session, deleted_by_user="admin", force=True)
session.commit()
```

### Check Restrictions Before Deletion

```python
# Check what would prevent deletion
ingredient = session.query(Ingredient).filter_by(ingredient_id=456).first()
try:
    ingredient._check_hard_delete_restrictions(session)
    print("Deletion is allowed")
except ValueError as e:
    print(f"Cannot delete: {e}")
```

## Business Scenarios

### Scenario 1: Discontinuing an Ingredient

When an ingredient is no longer available from suppliers:

```python
# First, try to soft delete (recommended)
ingredient.soft_delete(deleted_by_user="admin", session=session, cascade=True)
# This will disable products using the ingredient

# Later, if you want to permanently remove it:
try:
    ingredient.hard_delete(session=session, deleted_by_user="admin")
except ValueError:
    # Still has active products - handle them first
    pass
```

### Scenario 2: Removing a Product

When discontinuing a menu item:

```python
# Products can usually be hard deleted safely
# Sales history is preserved with nullified product_id
product.hard_delete(session=session, deleted_by_user="admin")
session.commit()
```

### Scenario 3: Customer Account Closure

When a customer requests account deletion:

```python
# Hard delete removes user but preserves transaction history
user.hard_delete(session=session, deleted_by_user="admin")
session.commit()

# Sales records remain with consumer_id=NULL
# Historical reporting is still possible
```

## Safety Guidelines

### 1. Always Use Soft Delete First
```python
# Recommended workflow:
# 1. Soft delete first
entity.soft_delete(deleted_by_user="admin", session=session)

# 2. Monitor for issues
# 3. If no problems after a period, hard delete
entity.hard_delete(session=session, deleted_by_user="admin")
```

### 2. Backup Before Hard Deletes
```python
# Create backup before critical deletions
from services.database_backup import create_backup
backup_path = create_backup("manual", f"before_hard_delete_{entity_type}_{entity_id}")
```

### 3. Handle Restrictions Gracefully
```python
def safe_hard_delete(entity, session, deleted_by_user):
    try:
        entity.hard_delete(session=session, deleted_by_user=deleted_by_user)
        return True, "Deleted successfully"
    except ValueError as e:
        return False, str(e)
```

### 4. Check Dependencies
```python
# For ingredients, check which products would be affected
def check_ingredient_dependencies(ingredient_id, session):
    ingredient = session.query(Ingredient).filter_by(ingredient_id=ingredient_id).first()
    products = [pi.product for pi in ingredient.ingredient_products 
                if pi.product and pi.product.is_available]
    return products
```

## API Response Handling

When entities are hard deleted, related records may have NULL foreign keys. The `to_dict()` methods handle this gracefully:

### Sales with Deleted Product
```json
{
    "sale_id": 123,
    "product_id": null,
    "product_name": null,
    "product_available": false,
    "product_status": "deleted",
    "product_unavailable_reason": "Product has been permanently removed",
    "quantity": 2,
    "price_paid": 5.00,
    "timestamp": "2025-01-27T10:30:00Z"
}
```

### Sales with Deleted User
```json
{
    "sale_id": 456,
    "consumer_id": null,
    "consumer_name": null,
    "consumer_available": false,
    "consumer_status": "deleted",
    "consumer_unavailable_reason": "User account has been permanently removed",
    "product_name": "Coffee",
    "quantity": 1,
    "price_paid": 2.00
}
```

## Database Integrity

Hard deletes maintain referential integrity through:

1. **Cascade Order** - Ensures dependent records are handled first
2. **Nullification** - Sets foreign keys to NULL instead of leaving orphaned records
3. **Restriction Checks** - Prevents deletion when business rules would be violated
4. **Transaction Safety** - All operations happen within database transactions

## Testing

Use the comprehensive test suite to verify hard delete behavior:

```bash
cd backend/app
python testing/realistic_deletion_test_scenarios.py
```

This will run scenarios testing:
- Ingredient deletion with product dependencies
- User deletion with sales history preservation
- Product deletion with cascade effects
- Restriction enforcement
- API response formatting

## Migration Considerations

When deploying hard delete functionality:

1. **Review Existing Data** - Check for orphaned records
2. **Update Client Code** - Handle NULL foreign keys in API responses
3. **Train Users** - Explain difference between soft and hard delete
4. **Set Permissions** - Limit hard delete access to administrators
5. **Monitor Usage** - Log all hard delete operations

## Troubleshooting

### Common Issues

**Error: "Cannot hard delete: X active records exist"**
- Solution: Either soft delete first, or handle dependent records manually

**Foreign key constraint errors**
- Solution: Check cascade order, ensure dependent records are handled first

**Unexpected NULL values in API responses**
- Solution: Update frontend to handle deleted entity references gracefully

### Recovery

Hard deletes cannot be undone, but you can:
1. Restore from database backup
2. Recreate entities manually
3. Update historical records if needed

For these reasons, always backup before critical hard delete operations.
