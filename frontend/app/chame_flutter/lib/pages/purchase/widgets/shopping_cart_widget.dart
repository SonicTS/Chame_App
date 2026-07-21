import 'package:flutter/material.dart';
import 'cart_item_widget.dart';
import 'cart_total_widget.dart';

/// The full shopping cart: list of items plus the total/actions footer.
/// Renders nothing when the cart is empty.
class ShoppingCartWidget extends StatelessWidget {
  final List<Map<String, dynamic>> shoppingCart;
  final double totalCost;
  final bool isSubmitting;
  final VoidCallback onPurchaseAll;
  final VoidCallback onClearCart;
  final ValueChanged<int> onRemoveItem;
  final void Function(int index, int newQuantity) onUpdateQuantity;

  const ShoppingCartWidget({
    super.key,
    required this.shoppingCart,
    required this.totalCost,
    required this.isSubmitting,
    required this.onPurchaseAll,
    required this.onClearCart,
    required this.onRemoveItem,
    required this.onUpdateQuantity,
  });

  @override
  Widget build(BuildContext context) {
    if (shoppingCart.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Shopping Cart', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            children: [
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: shoppingCart.length,
                separatorBuilder: (context, index) => const Divider(height: 1),
                itemBuilder: (context, index) => CartItemWidget(
                  item: shoppingCart[index],
                  index: index,
                  onRemove: onRemoveItem,
                  onQuantityChanged: onUpdateQuantity,
                ),
              ),
              const Divider(),
              CartTotalWidget(
                totalCost: totalCost,
                isSubmitting: isSubmitting,
                onPurchaseAll: onPurchaseAll,
                onClearCart: onClearCart,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
