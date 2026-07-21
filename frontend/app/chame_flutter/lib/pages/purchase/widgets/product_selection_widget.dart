import 'package:flutter/material.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';

/// Product picker + quantity field for the purchase page.
class ProductSelectionWidget extends StatelessWidget {
  final List<Map<String, dynamic>> products;
  final int? selectedProductId;
  final int quantity;
  final ValueChanged<Map<String, dynamic>?> onProductChanged;
  final ValueChanged<int> onQuantityChanged;

  const ProductSelectionWidget({
    super.key,
    required this.products,
    required this.selectedProductId,
    required this.quantity,
    required this.onProductChanged,
    required this.onQuantityChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownSearch<Map<String, dynamic>>(
          items: (String? filter, _) {
            final filtered = filter == null || filter.isEmpty
                ? products
                : products.where((p) => (p['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
            return Future.value(filtered);
          },
          selectedItem: products.firstWhereOrNull((p) => p['product_id'] == selectedProductId),
          itemAsString: (p) => p['name'] ?? '',
          compareFn: (a, b) => a['product_id'] == b['product_id'],
          onChanged: onProductChanged,
          popupProps: const PopupProps.menu(
            showSearchBox: true,
          ),
          decoratorProps: const DropDownDecoratorProps(
            decoration: InputDecoration(labelText: 'Select Product'),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: 120,
          child: TextFormField(
            initialValue: quantity.toString(),
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Quantity'),
            onChanged: (v) => onQuantityChanged(int.tryParse(v) ?? 1),
          ),
        ),
      ],
    );
  }
}
