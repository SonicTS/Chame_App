// lib/utils/formatters.dart
//
// The backend always sends full-precision numeric values (no server-side
// rounding). Rounding is a display-only concern, so any widget that shows a
// money or quantity value to the user should format it here rather than
// calling `.toString()` directly on the raw value.

/// Formats a numeric value (or null) for display with a fixed number of
/// decimals. Falls back to [fallback] when [value] is null or not a number.
String formatMoney(dynamic value, {int decimals = 2, String fallback = ''}) {
  if (value == null) return fallback;
  if (value is num) return value.toStringAsFixed(decimals);
  final parsed = num.tryParse(value.toString());
  if (parsed == null) return fallback;
  return parsed.toStringAsFixed(decimals);
}

/// Parses a quantity input that may be a plain decimal ("0.33") or a literal
/// fraction ("1/3"). Fractions are resolved via normal floating point
/// division, so "1/3" becomes the full-precision double 0.3333333333333333
/// instead of relying on the user (or some heuristic) to guess how many
/// decimal digits to type. Returns null if the input is empty or invalid.
double? parseQuantityInput(String input) {
  final trimmed = input.trim();
  if (trimmed.isEmpty) return null;

  if (trimmed.contains('/')) {
    final parts = trimmed.split('/');
    if (parts.length != 2) return null;
    final numerator = double.tryParse(parts[0].trim());
    final denominator = double.tryParse(parts[1].trim());
    if (numerator == null || denominator == null || denominator == 0) {
      return null;
    }
    return numerator / denominator;
  }

  return double.tryParse(trimmed);
}

