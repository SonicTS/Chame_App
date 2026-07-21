import 'package:flutter/material.dart';

import 'ingredient_match_card.dart';

/// Step 2: one IngredientMatchCard per collapsed item, and the final
/// "Submit Restock" button. The restock is always attributed to the
/// currently logged-in user (this page is admin-only), so there's no
/// separate salesman field here.
///
/// This is meant to be used directly as a Scaffold `body` (not nested
/// inside another scrollable), so it can give its card list a bounded
/// height via Expanded + ListView -- keeping the list independently
/// scrollable and the submit button always pinned and visible, instead of
/// everything sharing one unbounded page-level scroll view (which caused
/// layout/overflow glitches with many cards and open dropdowns/keyboard).
class IngredientMatchingSection extends StatelessWidget {
  final List<Map<String, dynamic>> aggregatedItems;
  final List<Map<String, dynamic>> ingredients;
  final Map<int, TextEditingController> quantityControllers;
  final Map<int, TextEditingController> priceControllers;
  final bool loadingIngredients;
  final bool submittingRestock;
  final VoidCallback onBack;
  final VoidCallback onSubmit;
  final void Function(int index, int? ingredientId) onIngredientChanged;

  const IngredientMatchingSection({
    super.key,
    required this.aggregatedItems,
    required this.ingredients,
    required this.quantityControllers,
    required this.priceControllers,
    required this.loadingIngredients,
    required this.submittingRestock,
    required this.onBack,
    required this.onSubmit,
    required this.onIngredientChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back),
                tooltip: "Back to editing",
                onPressed: onBack,
              ),
              const Text(
                "Match Ingredients & Restock",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
            ],
          ),
        ),
        Expanded(
          child: loadingIngredients
              ? const Center(child: CircularProgressIndicator())
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: aggregatedItems.length,
                  itemBuilder: (context, index) {
                    return IngredientMatchCard(
                      item: aggregatedItems[index],
                      ingredients: ingredients,
                      quantityController: quantityControllers[index]!,
                      priceController: priceControllers[index]!,
                      onIngredientChanged: (val) =>
                          onIngredientChanged(index, val),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.inventory),
              label: const Text("Submit Restock"),
              onPressed: submittingRestock ? null : onSubmit,
            ),
          ),
        ),
      ],
    );
  }
}
