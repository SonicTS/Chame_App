import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// User-adjustable heuristics for OCR'd receipt parsing
/// (see backend/app/services/receipt_parser.py's ReceiptParsingRules and
/// find_fuzzy_merge_candidates).
class ReceiptParsingSettings {
  final String pfandProductNumber;
  final List<String> validLetters;
  final Map<String, String> letterCorrections;
  final List<String> decimalSeparatorChars;

  // Fuzzy product-number merge heuristic: when collapsing items, product
  // numbers that don't match exactly but are otherwise close (same
  // price-per-package, enough matching digits, and only "commonly
  // misread" digit differences) are proposed as a merge for the user to
  // confirm/reject.
  final int minMatchingDigits;
  final List<List<String>> confusableDigitPairs;
  final int? expectedIdLength;

  const ReceiptParsingSettings({
    required this.pfandProductNumber,
    required this.validLetters,
    required this.letterCorrections,
    required this.decimalSeparatorChars,
    required this.minMatchingDigits,
    required this.confusableDigitPairs,
    required this.expectedIdLength,
  });

  static const defaults = ReceiptParsingSettings(
    pfandProductNumber: '',
    validLetters: ['A', 'B', 'C', 'D', 'E'],
    letterCorrections: {'8': 'B'},
    decimalSeparatorChars: [',', '.', ' ', ', ', '. '],
    minMatchingDigits: 3,
    confusableDigitPairs: [
      ['3', '8'],
      ['5', '6'],
      ['1', '7'],
      ['0', '8'],
    ],
    expectedIdLength: null,
  );

  ReceiptParsingSettings copyWith({
    String? pfandProductNumber,
    List<String>? validLetters,
    Map<String, String>? letterCorrections,
    List<String>? decimalSeparatorChars,
    int? minMatchingDigits,
    List<List<String>>? confusableDigitPairs,
    int? expectedIdLength,
    bool clearExpectedIdLength = false,
  }) {
    return ReceiptParsingSettings(
      pfandProductNumber: pfandProductNumber ?? this.pfandProductNumber,
      validLetters: validLetters ?? this.validLetters,
      letterCorrections: letterCorrections ?? this.letterCorrections,
      decimalSeparatorChars:
          decimalSeparatorChars ?? this.decimalSeparatorChars,
      minMatchingDigits: minMatchingDigits ?? this.minMatchingDigits,
      confusableDigitPairs: confusableDigitPairs ?? this.confusableDigitPairs,
      expectedIdLength: clearExpectedIdLength
          ? null
          : (expectedIdLength ?? this.expectedIdLength),
    );
  }
}

/// Persists (via secure storage) the user-adjustable receipt parsing rules,
/// so they survive app restarts and don't need to be re-entered on every
/// scan (e.g. the Pfand product number, previously typed on the scan page
/// itself).
class ReceiptParsingSettingsService {
  static const _pfandProductNumberKey = 'receipt_parsing_pfand_product_number';
  static const _validLettersKey = 'receipt_parsing_valid_letters';
  static const _letterCorrectionsKey = 'receipt_parsing_letter_corrections';
  static const _decimalSeparatorCharsKey =
      'receipt_parsing_decimal_separator_chars';
  static const _minMatchingDigitsKey = 'receipt_parsing_min_matching_digits';
  static const _confusableDigitPairsKey =
      'receipt_parsing_confusable_digit_pairs';
  static const _expectedIdLengthKey = 'receipt_parsing_expected_id_length';

  final FlutterSecureStorage _storage;

  ReceiptParsingSettingsService({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<ReceiptParsingSettings> loadSettings() async {
    final pfandProductNumber =
        await _storage.read(key: _pfandProductNumberKey) ?? '';
    final validLettersRaw = await _storage.read(key: _validLettersKey);
    final letterCorrectionsRaw =
        await _storage.read(key: _letterCorrectionsKey);
    final decimalSeparatorCharsRaw =
        await _storage.read(key: _decimalSeparatorCharsKey);
    final minMatchingDigitsRaw =
        await _storage.read(key: _minMatchingDigitsKey);
    final confusableDigitPairsRaw =
        await _storage.read(key: _confusableDigitPairsKey);
    final expectedIdLengthRaw =
        await _storage.read(key: _expectedIdLengthKey);

    return ReceiptParsingSettings(
      pfandProductNumber: pfandProductNumber,
      validLetters: validLettersRaw != null
          ? (jsonDecode(validLettersRaw) as List<dynamic>).cast<String>()
          : List<String>.from(ReceiptParsingSettings.defaults.validLetters),
      letterCorrections: letterCorrectionsRaw != null
          ? Map<String, String>.from(jsonDecode(letterCorrectionsRaw) as Map)
          : Map<String, String>.from(
              ReceiptParsingSettings.defaults.letterCorrections),
      decimalSeparatorChars: decimalSeparatorCharsRaw != null
          ? (jsonDecode(decimalSeparatorCharsRaw) as List<dynamic>)
              .cast<String>()
          : List<String>.from(
              ReceiptParsingSettings.defaults.decimalSeparatorChars),
      minMatchingDigits: int.tryParse(minMatchingDigitsRaw ?? '') ??
          ReceiptParsingSettings.defaults.minMatchingDigits,
      confusableDigitPairs: confusableDigitPairsRaw != null
          ? (jsonDecode(confusableDigitPairsRaw) as List<dynamic>)
              .map((pair) => (pair as List<dynamic>).cast<String>())
              .toList()
          : ReceiptParsingSettings.defaults.confusableDigitPairs
              .map((pair) => List<String>.from(pair))
              .toList(),
      expectedIdLength: expectedIdLengthRaw != null
          ? int.tryParse(expectedIdLengthRaw)
          : ReceiptParsingSettings.defaults.expectedIdLength,
    );
  }

  Future<void> saveSettings(ReceiptParsingSettings settings) async {
    await _storage.write(
      key: _pfandProductNumberKey,
      value: settings.pfandProductNumber,
    );
    await _storage.write(
      key: _validLettersKey,
      value: jsonEncode(settings.validLetters),
    );
    await _storage.write(
      key: _letterCorrectionsKey,
      value: jsonEncode(settings.letterCorrections),
    );
    await _storage.write(
      key: _decimalSeparatorCharsKey,
      value: jsonEncode(settings.decimalSeparatorChars),
    );
    await _storage.write(
      key: _minMatchingDigitsKey,
      value: settings.minMatchingDigits.toString(),
    );
    await _storage.write(
      key: _confusableDigitPairsKey,
      value: jsonEncode(settings.confusableDigitPairs),
    );
    if (settings.expectedIdLength != null) {
      await _storage.write(
        key: _expectedIdLengthKey,
        value: settings.expectedIdLength.toString(),
      );
    } else {
      await _storage.delete(key: _expectedIdLengthKey);
    }
  }
}
