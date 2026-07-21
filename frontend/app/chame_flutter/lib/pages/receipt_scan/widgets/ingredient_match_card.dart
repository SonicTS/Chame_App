import 'package:flutter/material.dart';

/// One collapsed receipt item (step 2), letting the user pick which app
/// Ingredient it corresponds to and adjust the restock quantity/price
/// before submitting.
class IngredientMatchCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final List<Map<String, dynamic>> ingredients;
  final TextEditingController quantityController;
  final TextEditingController priceController;
  final ValueChanged<int?> onIngredientChanged;

  const IngredientMatchCard({
    super.key,
    required this.item,
    required this.ingredients,
    required this.quantityController,
    required this.priceController,
    required this.onIngredientChanged,
  });

  @override
  Widget build(BuildContext context) {
    final pfandPrice = item["pfand_price"] as num?;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "#${item['product_number']}  ${item['description']}"
              "${pfandPrice != null ? ' (+€${pfandPrice.toStringAsFixed(2)} PF)' : ''}",
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              isExpanded: true,
              decoration:
                  const InputDecoration(labelText: "Match to ingredient"),
              value: item["matched_ingredient_id"] as int?,
              items: ingredients
                  .map((ing) => DropdownMenuItem<int>(
                        value: ing["ingredient_id"] as int,
                        child: Text(
                          ing["name"] as String? ?? "Unknown",
                          overflow: TextOverflow.ellipsis,
                        ),
                      ))
                  .toList(),
              onChanged: onIngredientChanged,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: quantityController,
                    decoration:
                        const InputDecoration(labelText: "Restock quantity"),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: priceController,
                    decoration: const InputDecoration(
                      labelText: "Price per package (€)",
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
