import 'package:flutter/material.dart';

/// "Add to Cart" / "Buy Now" buttons, stacked on narrow screens.
class ActionButtonsWidget extends StatelessWidget {
  final bool isSubmitting;
  final bool canAddToCart;
  final VoidCallback? onAddToCart;
  final VoidCallback? onBuyNow;

  const ActionButtonsWidget({
    super.key,
    required this.isSubmitting,
    required this.canAddToCart,
    this.onAddToCart,
    this.onBuyNow,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 400) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ElevatedButton(
                onPressed: canAddToCart ? onAddToCart : null,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: const Text('Add to Cart'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: isSubmitting ? null : onBuyNow,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: isSubmitting
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Buy Now'),
              ),
            ],
          );
        } else {
          return Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: canAddToCart ? onAddToCart : null,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: const Text('Add to Cart'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: isSubmitting ? null : onBuyNow,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: isSubmitting
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Buy Now'),
                ),
              ),
            ],
          );
        }
      },
    );
  }
}
