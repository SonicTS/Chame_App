# Enhanced Soft Delete Implementation Guide

## Overview

The enhanced soft delete system provides comprehensive deletion management with cascading rules and relationship filtering. This system addresses your requirements for handling soft-deleted entities and their relationships.

## Key Features

### 1. **Cascading Soft Delete Types**

- **CASCADE_SOFT_DELETE**: Also soft delete related records
- **CASCADE_DISABLE**: Mark related records as disabled/unavailable 
- **CASCADE_NULLIFY**: Set foreign key relationships to null
- **CASCADE_RESTRICT**: Prevent deletion if related records exist
- **CASCADE_IGNORE**: Do nothing (for historical records)

### 2. **Enhanced Status Management**

Each model now has:
- `is_deleted`: Traditional soft delete flag
- `is_disabled`: Marks records as unavailable due to cascading
- `disabled_reason`: Explains why the record was disabled
- `is_available`: Property that checks both deleted and disabled status

### 3. **Filtered Relationships**

Models can now get filtered relationships that exclude soft-deleted/disabled records:
```python
# Get only available related records
available_ingredients = product.get_filtered_relationship('product_ingredients')

# Include deleted records if needed
all_ingredients = product.get_filtered_relationship('product_ingredients', 
                                                  include_deleted=True)
```

## Implementation Examples

### Ingredient Deletion
When an ingredient is soft-deleted:
1. The ingredient is marked as `is_deleted = True`
2. All products using this ingredient are marked as `is_disabled = True` 
3. Products become unavailable for sale but historical data is preserved
4. The disabled_reason explains which ingredient caused the issue

### Product Deletion  
When a product is soft-deleted:
1. The product is marked as `is_deleted = True`
2. Sales history is preserved (CASCADE_IGNORE)
3. Pfand history is preserved (CASCADE_IGNORE)

### User Deletion
When a user is soft-deleted:
1. The user is marked as `is_deleted = True`
2. All sales history is preserved (CASCADE_IGNORE)
3. All donation history is preserved (CASCADE_IGNORE)
4. All pfand history is preserved (CASCADE_IGNORE)

## Model Configuration

### Setting Up Cascade Rules

Each model defines its cascade rules:

```python
class Ingredient(Base, EnhancedSoftDeleteMixin):
    _cascade_rules = [
        SoftDeleteCascadeRule(
            "ingredient_products", 
            SoftDeleteCascadeRule.CASCADE_DISABLE,
            condition_callback=lambda pi: pi.product and pi.product.is_available
        )
    ]

class Product(Base, EnhancedSoftDeleteMixin):
    _cascade_rules = [
        SoftDeleteCascadeRule("sales", SoftDeleteCascadeRule.CASCADE_IGNORE),
        SoftDeleteCascadeRule("pfand_history", SoftDeleteCascadeRule.CASCADE_IGNORE)
    ]
```

### Updated to_dict Methods

The `to_dict` methods now:
1. Include `is_available` status
2. Use filtered relationships to exclude unavailable records
3. Allow including historical records when needed

## Using the Enhanced Deletion Service

```python
from services.enhanced_deletion_service import EnhancedDeletionService

# Create service instance
deletion_service = EnhancedDeletionService(session)

# Soft delete an ingredient (will disable dependent products)
deletion_service.soft_delete_ingredient(ingredient_id=1, deleted_by_user="admin")

# Check product availability
availability = deletion_service.check_product_availability(product_id=1)
if not availability['available']:
    print(f"Unavailable due to: {availability['disabled_reason']}")

# Get only available items for frontend
available_products = deletion_service.get_available_products()
available_ingredients = deletion_service.get_available_ingredients()

# Restore a deleted item
deletion_service.restore_item(Ingredient, item_id=1)
```

## Database Queries

### Get Available Records Only
```python
# Old way
products = session.query(Product).filter(~Product.is_deleted).all()

# New way - excludes both deleted and disabled
products = session.query(Product).filter(
    ~Product.is_deleted, 
    ~Product.is_disabled
).all()

# Or use the mixin method
products = Product.available_only(session.query(Product)).all()
```

### Frontend Integration

For your Flutter app, the API endpoints should:
1. Use `get_available_*()` methods to return only usable items
2. Include `is_available` status in responses
3. Provide detailed availability information when needed

## Migration Strategy

1. **Add new columns**: Run database migration to add `is_disabled`, `disabled_reason`
2. **Update imports**: Change from `SoftDeleteMixin` to `EnhancedSoftDeleteMixin`
3. **Add cascade rules**: Define appropriate rules for each model
4. **Update API endpoints**: Use enhanced deletion service
5. **Update to_dict methods**: Use filtered relationships
6. **Test cascading**: Verify deletion cascades work as expected

## Benefits

1. **Consistent behavior**: All models follow the same deletion patterns
2. **Data integrity**: Historical records are preserved while maintaining referential logic
3. **Flexibility**: Different cascade types for different relationship needs
4. **Transparency**: Clear status and reasons for unavailability
5. **Easy restoration**: Can restore deleted items and their dependencies
6. **Performance**: Filtered queries prevent displaying unavailable items

This system provides the robust deletion management you requested while maintaining data integrity and providing clear status information for your application.
