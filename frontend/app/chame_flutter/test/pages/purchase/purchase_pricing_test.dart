// Unit tests for the purchase page's display-rounding helpers.
//
// These mirror the intent of the backend's `test_product_rounding.py`:
// verify that money values shown to the user are rounded/formatted
// consistently, and that the ".x9" checkout-total quirk only kicks in when
// a product actually carries a per-unit rounding difference.
import 'package:flutter_test/flutter_test.dart';
import 'package:chame_flutter/pages/purchase/purchase_pricing.dart';

void main() {
  group('roundToVisibleAmount', () {
    test('rounds to 2 decimal places', () {
      expect(roundToVisibleAmount(1.999), closeTo(2.0, 1e-9));
      expect(roundToVisibleAmount(2.554), closeTo(2.55, 1e-9));
      expect(roundToVisibleAmount(2.0), closeTo(2.0, 1e-9));
    });
  });

  group('formatVisibleAmount', () {
    test('strips trailing zeros but keeps one decimal place', () {
      expect(formatVisibleAmount(2.30), '2.3');
      expect(formatVisibleAmount(2.50), '2.5');
    });

    test('keeps a single trailing zero as ".0" for whole numbers', () {
      expect(formatVisibleAmount(2.00), '2.0');
    });

    test('keeps two decimal places when both are significant', () {
      expect(formatVisibleAmount(2.31), '2.31');
    });
  });

  group('getVisibleUnitPrice', () {
    test('is base price plus pfand, rounded', () {
      final product = {'price_per_unit': 2.0, 'pfand': 0.15};
      expect(getVisibleUnitPrice(product), closeTo(2.15, 1e-9));
    });

    test('defaults missing price/pfand fields to 0', () {
      expect(getVisibleUnitPrice(<String, dynamic>{}), 0.0);
    });
  });

  group('getCheckoutTotal', () {
    test('equals the visible total when there is no rounding difference', () {
      final product = {
        'price_per_unit': 2.31,
        'pfand': 0.0,
        'rounding_difference_per_unit': 0.0,
      };
      expect(getCheckoutTotal(product, 3), closeTo(6.93, 1e-9));
    });

    test('treats a missing rounding_difference_per_unit as disabled', () {
      final product = {'price_per_unit': 2.31, 'pfand': 0.0};
      expect(getCheckoutTotal(product, 2), closeTo(4.62, 1e-9));
    });

    test('appends the historical ".x9" quirk when a rounding difference is present', () {
      final product = {
        'price_per_unit': 1.9,
        'pfand': 0.0,
        'rounding_difference_per_unit': 0.01,
      };
      // visible unit price 1.9 * qty 2 = 3.8 -> "3.8" + "9" -> 3.89
      expect(getCheckoutTotal(product, 2), closeTo(3.89, 1e-9));
    });

    test('scales with quantity', () {
      final product = {'price_per_unit': 1.5, 'pfand': 0.5};
      expect(getCheckoutTotal(product, 1), closeTo(2.0, 1e-9));
      expect(getCheckoutTotal(product, 4), closeTo(8.0, 1e-9));
    });
  });
}
