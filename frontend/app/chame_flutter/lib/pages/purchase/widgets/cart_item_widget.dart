import 'package:flutter/material.dart';
import '../purchase_pricing.dart';
import 'quantity_controls.dart';

/// A single line item row inside the shopping cart list.
class CartItemWidget extends StatelessWidget {
  final Map<String, dynamic> item;
  final int index;
  final ValueChanged<int> onRemove;
  final void Function(int index, int newQuantity) onQuantityChanged;

  const CartItemWidget({
    super.key,
    required this.item,
    required this.index,
    required this.onRemove,
    required this.onQuantityChanged,
  });

  @override
  Widget build(BuildContext context) {
    final product = item['product'] as Map<String, dynamic>;
    final quantity = item['quantity'] as int;
    final basePrice = (product['price_per_unit'] as num?)?.toDouble() ?? 0.0;
    final pfand = (product['pfand'] as num?)?.toDouble() ?? 0.0;
    final visibleUnitPrice = getVisibleUnitPrice(product);
    final total = getCheckoutTotal(product, quantity);

    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  product['name'] ?? '',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete, color: Colors.red),
                onPressed: () => onRemove(index),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            pfand > 0
                ? '€${visibleUnitPrice.toStringAsFixed(2)} each (€${basePrice.toStringAsFixed(2)} + €${pfand.toStringAsFixed(2)} pfand)'
                : '€${visibleUnitPrice.toStringAsFixed(2)} each',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              QuantityControls(
                quantity: quantity,
                onChanged: (newQuantity) => onQuantityChanged(index, newQuantity),
              ),
              Text(
                '€${total.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Colors.green,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
