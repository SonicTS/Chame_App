# Historical Data Preservation Examples
# Demonstrating how sales records handle deleted/disabled entities

## Example Scenarios

### Scenario 1: Normal Sale (All entities available)
```json
{
  "sale_id": 123,
  "consumer_id": 5,
  "product_id": 10,
  "quantity": 2,
  "total_price": 5.00,
  "timestamp": "2025-06-29T10:30:00",
  "consumer": {
    "user_id": 5,
    "name": "John Doe",
    "is_available": true
  },
  "consumer_available": true,
  "product": {
    "product_id": 10,
    "name": "Cheese Toast",
    "price_per_unit": 2.50,
    "is_available": true
  },
  "product_available": true
}
```

### Scenario 2: Sale with Deleted Product
When a product is soft-deleted AFTER the sale was made:

```json
{
  "sale_id": 123,
  "consumer_id": 5,
  "product_id": 10,
  "quantity": 2,
  "total_price": 5.00,
  "timestamp": "2025-06-29T10:30:00",
  "consumer": {
    "user_id": 5,
    "name": "John Doe",
    "is_available": true
  },
  "consumer_available": true,
  "product": {
    "product_id": 10,
    "name": "Cheese Toast",
    "price_per_unit": 2.50,
    "is_available": false,  // ⚠️ Product is no longer available
    "is_deleted": true
  },
  "product_available": false,  // ⚠️ Clear indicator
  "product_status": "deleted"  // ⚠️ Reason
}
```

### Scenario 3: Sale with Disabled Product (due to ingredient deletion)
When an ingredient is deleted, products using it become disabled:

```json
{
  "sale_id": 123,
  "consumer_id": 5,
  "product_id": 10,
  "quantity": 2,
  "total_price": 5.00,
  "timestamp": "2025-06-29T10:30:00",
  "consumer": {
    "user_id": 5,
    "name": "John Doe",
    "is_available": true
  },
  "consumer_available": true,
  "product": {
    "product_id": 10,
    "name": "Cheese Toast",
    "price_per_unit": 2.50,
    "is_available": false,  // ⚠️ Product disabled
    "is_deleted": false,
    "is_disabled": true
  },
  "product_available": false,  // ⚠️ Clear indicator
  "product_status": "disabled",  // ⚠️ Reason
  "product_unavailable_reason": "Related Ingredient was deleted"  // ⚠️ Detailed reason
}
```

### Scenario 4: Sale with Deleted User
When a user is soft-deleted AFTER making purchases:

```json
{
  "sale_id": 123,
  "consumer_id": 5,
  "product_id": 10,
  "quantity": 2,
  "total_price": 5.00,
  "timestamp": "2025-06-29T10:30:00",
  "consumer": {
    "user_id": 5,
    "name": "John Doe",
    "is_available": false,  // ⚠️ User no longer available
    "is_deleted": true
  },
  "consumer_available": false,  // ⚠️ Clear indicator
  "consumer_status": "deleted",  // ⚠️ Reason
  "product": {
    "product_id": 10,
    "name": "Cheese Toast",
    "price_per_unit": 2.50,
    "is_available": true
  },
  "product_available": true
}
```

## How This Solves the Historical Data Problem

### ✅ **Data Preservation**
- Sales records are NEVER deleted (CASCADE_IGNORE)
- Foreign key relationships remain intact
- All original data (IDs, prices, quantities, timestamps) is preserved

### ✅ **Clear Status Indication**
- `*_available` fields clearly show if related entities are still usable
- `*_status` fields explain WHY something is unavailable ("deleted", "disabled", "not_found")
- `*_unavailable_reason` provides detailed explanations

### ✅ **Frontend-Friendly**
```javascript
// Frontend can easily handle different states
if (sale.product_available) {
  // Show normal product
  showProduct(sale.product);
} else {
  // Show with indication
  switch(sale.product_status) {
    case 'deleted':
      showDeletedProduct(sale.product, "This product has been removed");
      break;
    case 'disabled':
      showDisabledProduct(sale.product, sale.product_unavailable_reason);
      break;
    case 'not_found':
      showMissingProduct(sale.product_id, "Product data not found");
      break;
  }
}
```

### ✅ **Audit Trail**
- Complete history of what was sold, when, and to whom
- Can track impact of product/ingredient deletions
- Financial records remain accurate and complete

### ✅ **Reporting Capabilities**
```sql
-- Find sales affected by deleted products
SELECT * FROM sales s 
JOIN products p ON s.product_id = p.product_id 
WHERE p.is_deleted = true;

-- Find sales affected by disabled products (ingredient issues)
SELECT * FROM sales s 
JOIN products p ON s.product_id = p.product_id 
WHERE p.is_disabled = true;
```

## API Usage Examples

```python
# Get sales with full context
sales = session.query(Sale).all()
for sale in sales:
    sale_data = sale.to_dict(include_user=True, include_product=True)
    
    if not sale_data['product_available']:
        print(f"Sale {sale.sale_id} involves unavailable product: {sale_data['product_status']}")
        if 'product_unavailable_reason' in sale_data:
            print(f"Reason: {sale_data['product_unavailable_reason']}")

# Filter for only sales with available products (for current analysis)
available_sales = session.query(Sale).join(Product).filter(
    ~Product.is_deleted, 
    ~Product.is_disabled
).all()

# Get all sales (including those with deleted entities) for historical reporting
all_sales = session.query(Sale).all()
```

This approach ensures that:
1. **Historical integrity** is maintained
2. **Current status** is clearly communicated  
3. **Business logic** can differentiate between available and unavailable entities
4. **Audit trails** remain complete
5. **Frontend** can provide appropriate user feedback
