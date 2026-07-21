/// Display-rounding helpers for the purchase page.
///
/// The backend sends full-precision prices (no server-side rounding); these
/// helpers are purely about how a price is *shown* and *summed* on screen,
/// including the historical ".x9" checkout-total quirk used when a product
/// carries a per-unit rounding difference.
library;

double roundToVisibleAmount(double amount) {
  return double.parse(amount.toStringAsFixed(2));
}

String formatVisibleAmount(double amount) {
  var visible = roundToVisibleAmount(amount).toStringAsFixed(2);
  visible = visible.replaceFirst(RegExp(r'0+$'), '');
  visible = visible.replaceFirst(RegExp(r'\.$'), '');
  if (!visible.contains('.')) {
    visible = '$visible.0';
  }
  return visible;
}

double getVisibleUnitPrice(Map<String, dynamic> product) {
  final basePrice = (product['price_per_unit'] as num?)?.toDouble() ?? 0.0;
  final pfand = (product['pfand'] as num?)?.toDouble() ?? 0.0;
  return roundToVisibleAmount(basePrice + pfand);
}

double getCheckoutTotal(Map<String, dynamic> product, int quantity) {
  final visibleTotal = getVisibleUnitPrice(product) * quantity;
  final roundingDifference =
      (product['rounding_difference_per_unit'] as num?)?.toDouble() ?? 0.0;
  if (roundingDifference <= 0) {
    return roundToVisibleAmount(visibleTotal);
  }
  return double.parse('${formatVisibleAmount(visibleTotal)}9');
}
