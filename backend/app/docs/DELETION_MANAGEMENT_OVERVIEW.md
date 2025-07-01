# Comprehensive Deletion Management System

## Overview

The Chame Cafe system implements a sophisticated deletion management system that supports both soft and hard deletion with configurable cascade rules. This system is designed to handle realistic business scenarios while preserving data integrity and historical information.

## System Architecture

### Core Components

1. **EnhancedSoftDeleteMixin** - Base mixin providing deletion functionality
2. **Cascade Rules** - Configurable rules defining how deletions propagate
3. **Model Integration** - All major models inherit deletion capabilities
4. **API Response Enhancement** - Deleted/disabled entity status in responses
5. **Testing Framework** - Comprehensive test scenarios

### Key Features

- ✅ Soft deletion with cascading disable/restrict/ignore rules
- ✅ Hard deletion with cascading nullify/restrict/delete rules  
- ✅ Historical data preservation during deletions
- ✅ API response formatting for deleted/disabled entities
- ✅ Restoration capabilities for soft-deleted entities
- ✅ Comprehensive restriction checks
- ✅ Transaction safety and rollback support
- ✅ Realistic business scenario testing

## Deletion Types

### Soft Deletion
- **Purpose**: Mark records as unavailable while preserving data
- **Use Cases**: Temporary removal, ingredient out of stock, seasonal menu items
- **Benefits**: Reversible, preserves relationships, maintains historical accuracy
- **API Impact**: Records marked as `is_available: false`

### Hard Deletion  
- **Purpose**: Permanently remove records from database
- **Use Cases**: GDPR compliance, data cleanup, permanent discontinuation
- **Benefits**: Reduces database size, ensures complete removal
- **API Impact**: Foreign key references become null, handled gracefully

## Cascade Rules System

### Soft Delete Cascade Rules

| Rule Type | Behavior | Use Case |
|-----------|----------|----------|
| `CASCADE_SOFT_DELETE` | Also soft delete related records | User deletion cascades to personal data |
| `CASCADE_DISABLE` | Mark related records as disabled | Ingredient deletion disables products |
| `CASCADE_NULLIFY` | Set foreign key to null | Order cancellation nullifies product reference |
| `CASCADE_RESTRICT` | Prevent deletion if related records exist | Prevent deleting categories with products |
| `CASCADE_IGNORE` | Do nothing | Sales history should remain untouched |

### Hard Delete Cascade Rules

| Rule Type | Behavior | Use Case |
|-----------|----------|----------|
| `CASCADE_HARD_DELETE` | Also permanently delete related records | Remove user and all personal associations |
| `CASCADE_NULLIFY` | Set foreign key to null (preserve records) | Delete product but keep sales history |
| `CASCADE_RESTRICT` | Prevent deletion if related records exist | Prevent deleting ingredients still in use |
| `CASCADE_SOFT_DELETE` | Soft delete related records instead | Compromise between hard and soft deletion |

## Model Configuration

### Product Model
```python
class Product(Base, EnhancedSoftDeleteMixin):
    # Soft delete rules
    _cascade_rules = [
        SoftDeleteCascadeRule("sales", SoftDeleteCascadeRule.CASCADE_IGNORE),
        SoftDeleteCascadeRule("pfand_history", SoftDeleteCascadeRule.CASCADE_IGNORE)
    ]
    
    # Hard delete rules  
    _hard_delete_rules = [
        HardDeleteCascadeRule("sales", HardDeleteCascadeRule.CASCADE_NULLIFY, cascade_order=1),
        HardDeleteCascadeRule("pfand_history", HardDeleteCascadeRule.CASCADE_NULLIFY, cascade_order=1),
        HardDeleteCascadeRule("product_ingredients", HardDeleteCascadeRule.CASCADE_HARD_DELETE, cascade_order=0)
    ]
```

### Ingredient Model
```python
class Ingredient(Base, EnhancedSoftDeleteMixin):
    # Soft delete rules
    _cascade_rules = [
        SoftDeleteCascadeRule(
            "ingredient_products", 
            SoftDeleteCascadeRule.CASCADE_DISABLE,
            condition_callback=lambda pi: hasattr(pi, 'product') and pi.product and pi.product.is_available
        )
    ]
    
    # Hard delete rules
    _hard_delete_rules = [
        HardDeleteCascadeRule(
            "ingredient_products",
            HardDeleteCascadeRule.CASCADE_RESTRICT,
            condition_callback=lambda pi: pi.product and pi.product.is_available,
            cascade_order=0
        )
    ]
```

### User Model
```python
class User(Base, EnhancedSoftDeleteMixin):
    # Soft delete rules
    _cascade_rules = [
        SoftDeleteCascadeRule("sales", SoftDeleteCascadeRule.CASCADE_IGNORE),
        SoftDeleteCascadeRule("donated_sales", SoftDeleteCascadeRule.CASCADE_IGNORE),
        SoftDeleteCascadeRule("pfand_history", SoftDeleteCascadeRule.CASCADE_IGNORE)
    ]
    
    # Hard delete rules
    _hard_delete_rules = [
        HardDeleteCascadeRule("sales", HardDeleteCascadeRule.CASCADE_NULLIFY, cascade_order=1),
        HardDeleteCascadeRule("donated_sales", HardDeleteCascadeRule.CASCADE_NULLIFY, cascade_order=1),
        HardDeleteCascadeRule("pfand_history", HardDeleteCascadeRule.CASCADE_NULLIFY, cascade_order=1)
    ]
```

## API Response Enhancement

### Product API Response
```json
{
    "product_id": 123,
    "name": "Cheese Toast",
    "price_per_unit": 3.50,
    "is_available": true,
    "is_deleted": false,
    "is_disabled": false,
    "disabled_reason": null,
    "ingredients": [
        {
            "ingredient_id": 456,
            "name": "Cheese",
            "is_available": true
        }
    ]
}
```

### Sales History with Deleted Entities
```json
{
    "sale_id": 789,
    "product_id": null,
    "product_name": null,
    "product_available": false,
    "product_status": "deleted",
    "product_unavailable_reason": "Product has been permanently removed",
    "consumer_id": 123,
    "consumer_name": "Alice Johnson",
    "consumer_available": true,
    "consumer_status": "active",
    "quantity": 2,
    "price_paid": 7.00,
    "timestamp": "2025-01-27T10:30:00Z"
}
```

## Business Scenarios

### Scenario 1: Seasonal Menu Management
```python
# Remove seasonal items (soft delete)
pumpkin_spice_latte.soft_delete(deleted_by_user="admin", session=session, cascade=True)

# Bring back next season
pumpkin_spice_latte.restore()
```

### Scenario 2: Supplier Issues
```python
# Ingredient unavailable from supplier
organic_milk.soft_delete(deleted_by_user="admin", session=session, cascade=True)
# This automatically disables all products using organic milk

# Find new supplier and restore
organic_milk.restore()
# Products need to be manually re-enabled or auto-restoration logic implemented
```

### Scenario 3: Customer Account Deletion (GDPR)
```python
# Customer requests data deletion
try:
    customer.hard_delete(session=session, deleted_by_user="admin")
    session.commit()
    # Sales history preserved but anonymized (consumer_id = null)
except ValueError as e:
    # Handle any restrictions
    logger.error(f"Cannot delete customer: {e}")
```

### Scenario 4: Product Discontinuation
```python
# First soft delete to test impact
old_product.soft_delete(deleted_by_user="admin", session=session, cascade=True)

# After confirming no issues, permanently remove
old_product.hard_delete(session=session, deleted_by_user="admin")
session.commit()
# Sales history preserved, product-ingredient associations removed
```

## Query Patterns

### Getting Available Entities
```python
# Only available products
available_products = Product.available_only(session.query(Product)).all()

# Only available ingredients
available_ingredients = Ingredient.available_only(session.query(Ingredient)).all()

# Deleted products
deleted_products = Product.deleted_only(session.query(Product)).all()

# Disabled products
disabled_products = Product.disabled_only(session.query(Product)).all()
```

### Checking Entity Status
```python
# Check if entity is available for use
if product.is_available:
    # Can be sold
    pass

# Check specific states
if product.is_deleted:
    # Soft deleted
    pass
    
if product.is_disabled:
    # Disabled due to dependency
    print(f"Disabled because: {product.disabled_reason}")
```

## Frontend Integration

### Product List Component
```typescript
interface Product {
    product_id: number;
    name: string;
    price_per_unit: number;
    is_available: boolean;
    is_deleted: boolean;
    is_disabled: boolean;
    disabled_reason?: string;
}

// Filter available products for ordering
const availableProducts = products.filter(p => p.is_available);

// Show status in admin interface
const getProductStatus = (product: Product) => {
    if (product.is_deleted) return "Deleted";
    if (product.is_disabled) return `Disabled: ${product.disabled_reason}`;
    return "Available";
};
```

### Sales History Component
```typescript
interface Sale {
    sale_id: number;
    product_id?: number;
    product_name?: string;
    product_available: boolean;
    product_status: string;
    product_unavailable_reason?: string;
    consumer_id?: number;
    consumer_name?: string;
    consumer_available: boolean;
    consumer_status: string;
    consumer_unavailable_reason?: string;
    quantity: number;
    price_paid: number;
}

// Display sale with deleted entity handling
const SaleItem = ({ sale }: { sale: Sale }) => (
    <div>
        <span>
            {sale.product_available 
                ? sale.product_name 
                : `[Deleted Product] (${sale.product_unavailable_reason})`
            }
        </span>
        <span>
            {sale.consumer_available 
                ? sale.consumer_name 
                : `[Deleted Customer] (${sale.consumer_unavailable_reason})`
            }
        </span>
        <span>€{sale.price_paid}</span>
    </div>
);
```

## Testing Framework

### Comprehensive Test Scenarios
The system includes a comprehensive test suite (`realistic_deletion_test_scenarios.py`) that covers:

1. **Soft Delete Cascade Testing**
   - Ingredient deletion disabling dependent products
   - Verification of cascade rules
   - API response validation

2. **Hard Delete Restriction Testing**
   - Attempting to delete ingredients in use
   - Force override functionality
   - Error handling

3. **User Deletion with History Preservation**
   - Hard deleting users
   - Verifying sales history preservation
   - Nullified foreign key handling

4. **Product Deletion Cascade Effects**
   - Product hard deletion
   - Association cleanup
   - Sales history preservation

5. **Restoration Testing**
   - Soft delete restoration
   - Dependent entity re-enabling
   - Status verification

6. **Availability Query Testing**
   - Available vs unavailable filtering
   - Status categorization
   - Query performance

7. **API Response Testing**
   - Deleted entity representation
   - Status information inclusion
   - Error handling

### Running Tests
```bash
cd backend/app
python testing/realistic_deletion_test_scenarios.py
```

## Performance Considerations

### Database Indexes
```sql
-- Ensure proper indexing for deletion status queries
CREATE INDEX idx_products_deleted ON products(is_deleted);
CREATE INDEX idx_products_disabled ON products(is_disabled);
CREATE INDEX idx_products_available ON products(is_deleted, is_disabled);

-- Similar indexes for other entities
CREATE INDEX idx_ingredients_available ON ingredients(is_deleted, is_disabled);
CREATE INDEX idx_users_available ON users(is_deleted, is_disabled);
```

### Query Optimization
```python
# Use database-level filtering instead of Python filtering
available_products = session.query(Product).filter(
    Product.is_deleted == False,
    Product.is_disabled == False
).all()

# Instead of:
# all_products = session.query(Product).all()
# available_products = [p for p in all_products if p.is_available]
```

## Security Considerations

### Access Control
```python
# Restrict hard delete to administrators
def hard_delete_product(product_id: int, user: User, session: Session):
    if user.role != "admin":
        raise PermissionError("Only administrators can perform hard deletes")
    
    product = session.query(Product).filter_by(product_id=product_id).first()
    if not product:
        raise NotFoundError("Product not found")
    
    product.hard_delete(session=session, deleted_by_user=user.name)
    session.commit()
```

### Audit Logging
```python
# Log all deletion operations
def log_deletion(entity_type: str, entity_id: int, deletion_type: str, user: str):
    log_info(f"DELETION: {deletion_type} delete of {entity_type} {entity_id} by {user}")
```

## Migration and Deployment

### Database Migration
When deploying the deletion management system:

1. **Add New Columns**
   ```sql
   ALTER TABLE products ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
   ALTER TABLE products ADD COLUMN deleted_at TIMESTAMP NULL;
   ALTER TABLE products ADD COLUMN deleted_by VARCHAR(255) NULL;
   ALTER TABLE products ADD COLUMN is_disabled BOOLEAN DEFAULT FALSE;
   ALTER TABLE products ADD COLUMN disabled_reason VARCHAR(255) NULL;
   ```

2. **Update Existing Data**
   ```sql
   UPDATE products SET is_deleted = FALSE, is_disabled = FALSE WHERE is_deleted IS NULL;
   ```

3. **Create Indexes**
   ```sql
   CREATE INDEX idx_products_available ON products(is_deleted, is_disabled);
   ```

### API Versioning
Consider versioning APIs when changing response formats:
```python
# v1: Simple availability
{"product_id": 123, "available": true}

# v2: Detailed status
{
    "product_id": 123, 
    "is_available": true, 
    "is_deleted": false, 
    "is_disabled": false
}
```

## Monitoring and Maintenance

### Key Metrics
- Number of soft vs hard deletions per period
- Restoration frequency
- API errors related to deleted entities
- Database size impact of soft deletes

### Cleanup Jobs
```python
# Periodic cleanup of old soft-deleted records
def cleanup_old_soft_deletes(days_old: int = 90):
    cutoff_date = datetime.now() - timedelta(days=days_old)
    old_deleted = session.query(Product).filter(
        Product.is_deleted == True,
        Product.deleted_at < cutoff_date
    ).all()
    
    for product in old_deleted:
        # Optionally convert to hard delete
        product.hard_delete(session=session, deleted_by_user="system_cleanup")
```

## Conclusion

The comprehensive deletion management system provides:

- **Flexibility** - Choose between soft and hard deletion based on business needs
- **Safety** - Restriction checks prevent accidental data loss
- **Transparency** - Clear API responses show entity status
- **Reversibility** - Soft deletes can be restored
- **Compliance** - Hard deletes support data protection requirements
- **Testing** - Comprehensive test coverage ensures reliability

This system handles realistic business scenarios while maintaining data integrity and providing a smooth user experience across both API and frontend interfaces.
