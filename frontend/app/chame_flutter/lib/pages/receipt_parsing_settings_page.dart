import 'package:flutter/material.dart';

import '../data/py_bride.dart';
import '../services/receipt_parsing_settings_service.dart';

/// Lets an admin adjust the OCR-heuristic rules used while parsing scanned
/// receipts (see backend/app/services/receipt_parser.py's
/// ReceiptParsingRules): which letters/VAT categories are valid, which
/// characters get misread in their place (e.g. '8' for 'B'), which
/// characters can appear as a price's decimal separator, and the
/// store-specific Pfand (bottle deposit) product number.
class ReceiptParsingSettingsPage extends StatefulWidget {
  const ReceiptParsingSettingsPage({super.key});

  @override
  State<ReceiptParsingSettingsPage> createState() =>
      _ReceiptParsingSettingsPageState();
}

class _ReceiptParsingSettingsPageState
    extends State<ReceiptParsingSettingsPage> {
  final _settingsService = ReceiptParsingSettingsService();
  final _pfandController = TextEditingController();
  final _minMatchingDigitsController = TextEditingController();
  final _expectedIdLengthController = TextEditingController();

  bool _loading = true;
  bool _saving = false;
  List<String> _validLetters = [];
  Map<String, String> _letterCorrections = {};
  List<String> _decimalSeparatorChars = [];
  List<List<String>> _confusableDigitPairs = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _pfandController.dispose();
    _minMatchingDigitsController.dispose();
    _expectedIdLengthController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final settings = await _settingsService.loadSettings();
    if (!mounted) return;
    setState(() {
      _pfandController.text = settings.pfandProductNumber;
      _validLetters = List<String>.from(settings.validLetters);
      _letterCorrections = Map<String, String>.from(settings.letterCorrections);
      _decimalSeparatorChars = List<String>.from(settings.decimalSeparatorChars);
      _minMatchingDigitsController.text = settings.minMatchingDigits.toString();
      _confusableDigitPairs =
          settings.confusableDigitPairs.map((p) => List<String>.from(p)).toList();
      _expectedIdLengthController.text =
          settings.expectedIdLength?.toString() ?? '';
      _loading = false;
    });
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final minMatchingDigits =
        int.tryParse(_minMatchingDigitsController.text.trim()) ??
            ReceiptParsingSettings.defaults.minMatchingDigits;
    final expectedIdLength =
        int.tryParse(_expectedIdLengthController.text.trim());
    await _settingsService.saveSettings(ReceiptParsingSettings(
      pfandProductNumber: _pfandController.text.trim(),
      validLetters: _validLetters,
      letterCorrections: _letterCorrections,
      decimalSeparatorChars: _decimalSeparatorChars,
      minMatchingDigits: minMatchingDigits,
      confusableDigitPairs: _confusableDigitPairs,
      expectedIdLength: expectedIdLength,
    ));
    if (!mounted) return;
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Receipt parsing settings saved.'),
        backgroundColor: Colors.green,
      ),
    );
  }

  Future<void> _resetToDefaults() async {
    Map<String, dynamic> defaults;
    try {
      defaults = await PyBridge().getDefaultReceiptParsingSettings();
    } catch (e) {
      defaults = {
        'valid_letters': ReceiptParsingSettings.defaults.validLetters,
        'letter_corrections': ReceiptParsingSettings.defaults.letterCorrections,
        'decimal_separator_chars':
            ReceiptParsingSettings.defaults.decimalSeparatorChars,
        'min_matching_digits': ReceiptParsingSettings.defaults.minMatchingDigits,
        'confusable_digit_pairs':
            ReceiptParsingSettings.defaults.confusableDigitPairs,
        'expected_id_length': ReceiptParsingSettings.defaults.expectedIdLength,
      };
    }
    if (!mounted) return;
    setState(() {
      _validLetters =
          (defaults['valid_letters'] as List<dynamic>? ?? []).cast<String>();
      _letterCorrections = Map<String, String>.from(
        defaults['letter_corrections'] as Map<dynamic, dynamic>? ?? {},
      );
      _decimalSeparatorChars =
          (defaults['decimal_separator_chars'] as List<dynamic>? ?? [])
              .cast<String>();
      _minMatchingDigitsController.text =
          (defaults['min_matching_digits'] as num?)?.toString() ??
              ReceiptParsingSettings.defaults.minMatchingDigits.toString();
      _confusableDigitPairs = (defaults['confusable_digit_pairs']
                  as List<dynamic>? ??
              [])
          .map((pair) => (pair as List<dynamic>).cast<String>())
          .toList();
      _expectedIdLengthController.text =
          (defaults['expected_id_length'] as num?)?.toString() ?? '';
    });
  }

  Future<String?> _promptSingleCharacter({
    required String title,
    required String label,
  }) async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          maxLength: 1,
          decoration: InputDecoration(labelText: label),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, controller.text),
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (result == null || result.isEmpty) return null;
    return result;
  }

  Future<void> _addValidLetter() async {
    final letter = await _promptSingleCharacter(
      title: 'Add Valid Letter',
      label: 'e.g. D',
    );
    if (letter == null) return;
    final upper = letter.toUpperCase();
    if (_validLetters.contains(upper)) return;
    setState(() => _validLetters.add(upper));
  }

  Future<void> _addLetterCorrection() async {
    final fromController = TextEditingController();
    final toController = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Add Misread Correction'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: fromController,
              maxLength: 1,
              decoration: const InputDecoration(
                labelText: 'Misread character',
                hintText: 'e.g. 4',
              ),
              autofocus: true,
            ),
            TextField(
              controller: toController,
              maxLength: 1,
              decoration: const InputDecoration(
                labelText: 'Should be corrected to',
                hintText: 'e.g. A',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (result != true) return;
    final from = fromController.text;
    final to = toController.text.toUpperCase();
    if (from.isEmpty || to.isEmpty) return;
    setState(() => _letterCorrections[from] = to);
  }

  Future<void> _addDecimalSeparatorChar() async {
    final char = await _promptSingleCharacter(
      title: 'Add Decimal Separator Character',
      label: "e.g. ';' or a space",
    );
    if (char == null) return;
    if (_decimalSeparatorChars.contains(char)) return;
    setState(() => _decimalSeparatorChars.add(char));
  }

  Future<void> _addConfusableDigitPair() async {
    final firstController = TextEditingController();
    final secondController = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Add Confusable Digit Pair'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Two digits that are often misread as each other (e.g. 3 and 8).',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: firstController,
              maxLength: 1,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Digit'),
              autofocus: true,
            ),
            TextField(
              controller: secondController,
              maxLength: 1,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Often misread as'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (result != true) return;
    final first = firstController.text;
    final second = secondController.text;
    if (first.isEmpty || second.isEmpty || first == second) return;
    setState(() => _confusableDigitPairs.add([first, second]));
  }

  String _displayChar(String c) => c == ' ' ? '(space)' : c;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Receipt Parsing Settings')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Pfand (Deposit) Product Number',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "The store-specific product number identifying a "
                      "bottle deposit line (its description text can vary, "
                      "but the number stays the same). Used automatically "
                      "on every receipt scan.",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _pfandController,
                      decoration: const InputDecoration(
                        labelText: 'Pfand product number (optional)',
                        hintText: 'e.g. 80000291',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                    ),
                    const SizedBox(height: 24),

                    const Text(
                      'Valid VAT Letters',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Single letters expected at the end of an item line '
                      '(e.g. A, B). Add more (like D) if your receipts use '
                      'additional categories.',
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        ..._validLetters.map((letter) => Chip(
                              label: Text(letter),
                              onDeleted: () =>
                                  setState(() => _validLetters.remove(letter)),
                            )),
                        ActionChip(
                          avatar: const Icon(Icons.add, size: 18),
                          label: const Text('Add'),
                          onPressed: _addValidLetter,
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    const Text(
                      'Letter Misread Corrections',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "Characters OCR sometimes reads instead of a valid "
                      "letter (e.g. '8' for 'B', or '4' for 'A'), "
                      "auto-corrected during parsing.",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        ..._letterCorrections.entries.map((entry) => Chip(
                              label: Text('${entry.key} \u2192 ${entry.value}'),
                              onDeleted: () => setState(
                                  () => _letterCorrections.remove(entry.key)),
                            )),
                        ActionChip(
                          avatar: const Icon(Icons.add, size: 18),
                          label: const Text('Add'),
                          onPressed: _addLetterCorrection,
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    const Text(
                      'Price Decimal Separator Characters',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "Characters that can separate a price's whole and "
                      "decimal digits, including OCR misreads (e.g. a comma "
                      "misread as a plain space).",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        ..._decimalSeparatorChars.map((char) => Chip(
                              label: Text(_displayChar(char)),
                              onDeleted: () => setState(
                                  () => _decimalSeparatorChars.remove(char)),
                            )),
                        ActionChip(
                          avatar: const Icon(Icons.add, size: 18),
                          label: const Text('Add'),
                          onPressed: _addDecimalSeparatorChar,
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    const Text(
                      'Fuzzy Item Merge Heuristic',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "When collapsing items, product numbers that don't "
                      "match exactly but have the same price-per-package and "
                      "are otherwise close (enough matching digits, and only "
                      "\"commonly misread\" digit differences) are proposed "
                      "as a merge for you to confirm or reject.",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _minMatchingDigitsController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Minimum matching digits',
                              border: OutlineInputBorder(),
                              isDense: true,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: _expectedIdLengthController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Expected ID length (optional)',
                              hintText: 'e.g. 6',
                              border: OutlineInputBorder(),
                              isDense: true,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "Expected ID length lets a product number missing one "
                      "digit (e.g. 5 read instead of 6) still be matched "
                      "against the rest. Leave blank to disable.",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Confusable Digit Pairs',
                      style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        ..._confusableDigitPairs.map((pair) => Chip(
                              label: Text('${pair[0]} \u2194 ${pair[1]}'),
                              onDeleted: () => setState(
                                  () => _confusableDigitPairs.remove(pair)),
                            )),
                        ActionChip(
                          avatar: const Icon(Icons.add, size: 18),
                          label: const Text('Add'),
                          onPressed: _addConfusableDigitPair,
                        ),
                      ],
                    ),
                    const SizedBox(height: 32),

                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: _saving ? null : _save,
                            child: _saving
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Text('Save'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: _saving ? null : _resetToDefaults,
                            child: const Text('Reset to Defaults'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
