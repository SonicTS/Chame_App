import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:provider/provider.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/services/receipt_parsing_settings_service.dart';

import 'receipt_text_helpers.dart';
import 'widgets/parsed_items_section.dart';
import 'widgets/ingredient_matching_section.dart';

/// Scan a paper receipt, clean up the OCR'd purchase lines, collapse
/// duplicate products, match each one to an app Ingredient, and submit a
/// restock. All OCR row-grouping happens natively (AndroidOcr.kt); all
/// parsing/heuristics/aggregation happen in Python
/// (services/receipt_parser.py) via the PyBridge method channel.
class ReceiptScanPage extends StatefulWidget {
  const ReceiptScanPage({super.key});

  @override
  State<ReceiptScanPage> createState() => _ReceiptScanPageState();
}

class _ReceiptScanPageState extends State<ReceiptScanPage> {
  static const MethodChannel channel =
      MethodChannel("samples.flutter.dev/chame/python");

  final ImagePicker picker = ImagePicker();

  List<File> images = [];

  bool processing = false;

  // Raw OCR row text, indexed by line number (as produced by the Kotlin
  // y-only row grouping). Kept around so groups can fall back to the
  // original line(s) they came from when reconstructing display text.
  List<String> rowTexts = [];

  // Parsed purchase line groups, built from Python's parse_receipt_lines.
  // Each entry: {type: 'item'|'unmatched', count, product_number,
  // description, price, letter, line_numbers, verified, reason?,
  // text?, text_override?}
  List<Map<String, dynamic>> groups = [];

  // Snapshots of `groups` taken before each edit/delete/merge/re-parse, so
  // those actions can be undone.
  final List<List<Map<String, dynamic>>> _history = [];

  // User-adjustable OCR heuristics (Pfand product number, valid VAT
  // letters, letter misread corrections, decimal separator characters),
  // configured on the Receipt Parsing Settings page and re-loaded fresh
  // before every parse so changes made there take effect immediately.
  final _parsingSettingsService = ReceiptParsingSettingsService();

  // Step 2: collapsing + ingredient matching + restock submission.
  bool showMatchingStep = false;
  bool loadingIngredients = false;
  bool submittingRestock = false;
  List<Map<String, dynamic>> aggregatedItems = [];
  List<Map<String, dynamic>> ingredients = [];
  final Map<int, TextEditingController> _quantityControllers = {};
  final Map<int, TextEditingController> _priceControllers = {};

  void _disposeMatchingControllers() {
    for (final controller in _quantityControllers.values) {
      controller.dispose();
    }
    for (final controller in _priceControllers.values) {
      controller.dispose();
    }
    _quantityControllers.clear();
    _priceControllers.clear();
  }

  @override
  void dispose() {
    _disposeMatchingControllers();
    super.dispose();
  }

  /// Captures one or more photos in a row (e.g. a receipt that continues
  /// across multiple pages), cropping and OCR'ing each one, then combines
  /// all their rows into a single continuous line list for parsing.
  Future<void> pickImages() async {
    final List<File> newImages = [];
    final List<String> allRowTexts = [];
    bool keepGoing = true;

    while (keepGoing) {
      final XFile? file = await picker.pickImage(source: ImageSource.camera);
      if (file == null) break; // user cancelled the camera

      final CroppedFile? cropped = await ImageCropper().cropImage(
        sourcePath: file.path,
        uiSettings: [
          AndroidUiSettings(
            toolbarTitle: newImages.isEmpty
                ? 'Crop Receipt'
                : 'Crop Receipt (page ${newImages.length + 1})',
            lockAspectRatio: false, // let user pick any rectangle
          ),
        ],
      );
      if (cropped == null) break; // user cancelled the crop

      setState(() {
        processing = true;
      });

      try {
        final rowsForImage = await _recognizeRowsForImage(cropped.path);
        newImages.add(File(cropped.path));
        allRowTexts.addAll(rowsForImage);
      } on PlatformException catch (e) {
        _showDialog("OCR Error", e.message ?? e.toString());
        setState(() => processing = false);
        break;
      } catch (e) {
        _showDialog("OCR Error", e.toString());
        setState(() => processing = false);
        break;
      }

      setState(() => processing = false);

      keepGoing = await _confirmAddAnotherPage();
    }

    if (newImages.isEmpty) return;

    setState(() {
      images = newImages;
      rowTexts = allRowTexts;
      groups = [];
      _history.clear();
      showMatchingStep = false;
      processing = true;
    });

    // Item parsing/heuristics live in Python (services/receipt_parser.py),
    // not in Dart or Kotlin.
    await _parseReceipt(allRowTexts);

    setState(() {
      processing = false;
    });
  }

  /// Runs OCR on a single image and returns its rows' text, in order.
  /// "rows" is our custom y-only grouping (one entry per visual row on the
  /// receipt, regardless of horizontal whitespace).
  Future<List<String>> _recognizeRowsForImage(String imagePath) async {
    final String? response = await channel.invokeMethod<String>(
      "recognize_image",
      {
        "image_path": imagePath,
      },
    );

    if (response == null) {
      throw Exception("OCR returned null");
    }

    final Map<String, dynamic> json =
        jsonDecode(response) as Map<String, dynamic>;
    final List<dynamic> rows = json["rows"] as List<dynamic>? ?? [];
    return rows
        .map((row) => (row as Map<String, dynamic>)["text"] as String? ?? "")
        .toList();
  }

  Future<bool> _confirmAddAnotherPage() async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Add another page?"),
        content: const Text(
          "If this receipt continues on another photo, you can scan it now "
          "and it will be appended to this one.",
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text("No, done"),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("Add another page"),
          ),
        ],
      ),
    );
    return result ?? false;
  }

  /// Sends the OCR'd row text to Python (services/admin_api.parse_receipt_lines
  /// -> services/receipt_parser.parse_receipt_lines) for item/heuristic
  /// parsing, then flattens the result into a single editable list of groups.
  Future<void> _parseReceipt(List<String> lines) async {
    try {
      final settings = await _parsingSettingsService.loadSettings();
      final String? response = await channel.invokeMethod<String>(
        "parse_receipt_lines",
        {
          "lines": jsonEncode(lines),
          "pfand_product_number": settings.pfandProductNumber,
          "valid_letters": jsonEncode(settings.validLetters),
          "letter_corrections": jsonEncode(settings.letterCorrections),
          "decimal_separator_chars": jsonEncode(settings.decimalSeparatorChars),
        },
      );
      if (response == null) return;

      final Map<String, dynamic> parsed =
          jsonDecode(response) as Map<String, dynamic>;

      final List<Map<String, dynamic>> newGroups = [];
      for (final raw in (parsed["items"] as List<dynamic>? ?? [])) {
        final group = Map<String, dynamic>.from(raw as Map);
        group["type"] = "item";
        newGroups.add(group);
      }
      for (final raw in (parsed["unmatched"] as List<dynamic>? ?? [])) {
        final group = Map<String, dynamic>.from(raw as Map);
        group["type"] = "unmatched";
        newGroups.add(group);
      }
      newGroups.sort((a, b) {
        final aLine = (a["line_numbers"] as List).first as int;
        final bLine = (b["line_numbers"] as List).first as int;
        return aLine.compareTo(bLine);
      });

      setState(() {
        groups = newGroups;
      });
    } catch (e) {
      // Leave existing groups (likely empty) untouched; row text above is
      // still visible for manual inspection even if parsing fails.
    }
  }

  /// Deep-copies `groups` (plain JSON-compatible maps/lists only) so it can
  /// be restored later via [_undo].
  List<Map<String, dynamic>> _snapshotGroups() {
    return (jsonDecode(jsonEncode(groups)) as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  void _pushHistory() {
    _history.add(_snapshotGroups());
    if (_history.length > 50) {
      _history.removeAt(0);
    }
  }

  void _undo() {
    if (_history.isEmpty) return;
    setState(() {
      groups = _history.removeLast();
    });
  }

  Future<void> _editGroup(int index) async {
    final initialText = displayTextFor(groups[index], rowTexts);
    final controller = TextEditingController(text: initialText)
      // Explicitly collapse the selection to the end of the text. Left
      // unset, the controller's initial selection is invalid (offset -1),
      // which some Android keyboards (e.g. Gboard) misinterpret once the
      // field is focused: instead of a later tap just placing the caret,
      // they extend a selection from that stale anchor (effectively the
      // end of the text) to wherever was tapped.
      ..selection = TextSelection.collapsed(offset: initialText.length);
    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Edit Entry"),
        content: TextField(
          controller: controller,
          maxLines: null,
          decoration: const InputDecoration(border: OutlineInputBorder()),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, controller.text),
            child: const Text("Save"),
          ),
        ],
      ),
    );
    if (result == null) return;
    _pushHistory();
    setState(() {
      groups[index]["text_override"] = result;
    });
  }

  void _deleteGroup(int index) {
    _pushHistory();
    setState(() {
      groups.removeAt(index);
    });
  }

  void _mergeWithNext(int index) {
    if (index >= groups.length - 1) return;
    _pushHistory();
    final current = groups[index];
    final next = groups[index + 1];

    final combinedLineNumbers = <int>{
      ...(current["line_numbers"] as List).cast<int>(),
      ...(next["line_numbers"] as List).cast<int>(),
    }.toList()
      ..sort();

    final merged = <String, dynamic>{
      "type": "unmatched",
      "line_numbers": combinedLineNumbers,
      "text_override":
          "${rawTextFor(current, rowTexts)}\n${rawTextFor(next, rowTexts)}",
      "reason": "Manually merged",
      "verified": false,
    };

    setState(() {
      groups
        ..removeAt(index + 1)
        ..removeAt(index)
        ..insert(index, merged);
    });
  }

  /// Re-sends this single group's current (possibly manually edited) text
  /// through Python's parse_receipt_lines, replacing it with whatever
  /// structured result comes back (one item, several items, or still
  /// unmatched). Useful after fixing a typo/garbled character by hand.
  Future<void> _reparseGroup(int index) async {
    final originalLineNumbers =
        (groups[index]["line_numbers"] as List).cast<int>();
    final lines = rawTextFor(groups[index], rowTexts).split("\n");

    try {
      final settings = await _parsingSettingsService.loadSettings();
      final String? response = await channel.invokeMethod<String>(
        "parse_receipt_lines",
        {
          "lines": jsonEncode(lines),
          "pfand_product_number": settings.pfandProductNumber,
          "valid_letters": jsonEncode(settings.validLetters),
          "letter_corrections": jsonEncode(settings.letterCorrections),
          "decimal_separator_chars": jsonEncode(settings.decimalSeparatorChars),
        },
      );
      if (response == null) return;

      final Map<String, dynamic> parsed =
          jsonDecode(response) as Map<String, dynamic>;

      // Local line numbers (indices into `lines`) are remapped back to the
      // original receipt line numbers where possible, so traceability is
      // kept consistent with the rest of the groups.
      List<int> remap(List<dynamic> localLineNumbers) {
        return localLineNumbers.map((local) {
          final i = local as int;
          return (i >= 0 && i < originalLineNumbers.length)
              ? originalLineNumbers[i]
              : -1;
        }).toList();
      }

      final List<Map<String, dynamic>> replacement = [];
      for (final raw in (parsed["items"] as List<dynamic>? ?? [])) {
        final group = Map<String, dynamic>.from(raw as Map);
        group["type"] = "item";
        group["line_numbers"] = remap(group["line_numbers"] as List);
        replacement.add(group);
      }
      for (final raw in (parsed["unmatched"] as List<dynamic>? ?? [])) {
        final group = Map<String, dynamic>.from(raw as Map);
        group["type"] = "unmatched";
        group["line_numbers"] = remap(group["line_numbers"] as List);
        replacement.add(group);
      }
      if (replacement.isEmpty) return;

      // Items are appended before unmatched entries above regardless of
      // which original lines they actually came from -- e.g. if line 0
      // failed to parse but lines 1-2 formed a valid item, the item would
      // otherwise end up listed before line 0's still-unmatched entry.
      // Sorting by each group's first (smallest) original line number here
      // keeps the list -- and anything adjacent-merged from it afterwards
      // -- in the receipt's actual line order.
      replacement.sort((a, b) {
        final aLine = (a["line_numbers"] as List).first as int;
        final bLine = (b["line_numbers"] as List).first as int;
        return aLine.compareTo(bLine);
      });

      _pushHistory();
      setState(() {
        groups
          ..removeAt(index)
          ..insertAll(index, replacement);
      });
    } catch (e) {
      // Keep the existing entry unchanged if re-parsing fails.
    }
  }

  void _showDialog(String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  bool _sameItem(Map<String, dynamic> a, Map<String, dynamic> b) {
    return a["product_number"] == b["product_number"] &&
        listEquals(
          (a["line_numbers"] as List).cast<int>(),
          (b["line_numbers"] as List).cast<int>(),
        );
  }

  /// Looks for aggregated items that don't share an exact product_number
  /// but are suspected to be the same product (see
  /// services/receipt_parser.find_fuzzy_merge_candidates: same
  /// price-per-package, enough matching/commonly-misread digits). Each
  /// cluster found is shown to the user as a checklist to confirm/reject
  /// before actually merging. Returns the (possibly updated) item list.
  Future<List<Map<String, dynamic>>> _reviewFuzzyMergeCandidates(
    List<Map<String, dynamic>> items,
    ReceiptParsingSettings settings,
  ) async {
    List<Map<String, dynamic>> clusters;
    try {
      clusters = await PyBridge().findReceiptMergeCandidates(
        items: items,
        minMatchingDigits: settings.minMatchingDigits,
        confusableDigitPairs: settings.confusableDigitPairs,
        expectedIdLength: settings.expectedIdLength,
      );
    } catch (e) {
      // Don't let a failure in this optional heuristic block the flow.
      return items;
    }
    if (clusters.isEmpty) return items;

    final result = List<Map<String, dynamic>>.from(items);

    for (final cluster in clusters) {
      final clusterItems =
          (cluster["items"] as List<dynamic>).cast<Map<String, dynamic>>();
      // A prior cluster's merge may have already consumed some of these
      // items (e.g. a chain of 3+ mutually fuzzy-matching product numbers).
      final stillPresent = clusterItems
          .where((ci) => result.any((r) => _sameItem(r, ci)))
          .toList();
      if (stillPresent.length < 2) continue;

      final checkedItems = await _showMergeCandidateDialog(stillPresent);
      if (checkedItems == null || checkedItems.length < 2) continue;

      try {
        final merged = await PyBridge().mergeReceiptItems(checkedItems);
        result.removeWhere((r) => checkedItems.any((ci) => _sameItem(r, ci)));
        result.add(merged);
      } catch (e) {
        // Leave the items as separate entries if merging fails.
      }
    }

    return result;
  }

  /// Shows a checklist of candidate items suspected to be the same product,
  /// letting the user uncheck any that aren't. Returns the checked subset
  /// to merge, or null if the user skipped this cluster entirely.
  Future<List<Map<String, dynamic>>?> _showMergeCandidateDialog(
    List<Map<String, dynamic>> items,
  ) async {
    final checked = List<bool>.filled(items.length, true);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text("Possible Duplicate Items"),
          content: SizedBox(
            width: double.maxFinite,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "These items have the same price and similar product "
                  "numbers (likely a misread digit). Uncheck any that are "
                  "NOT actually the same item.",
                  style: TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 12),
                ...items.asMap().entries.map((entry) {
                  final index = entry.key;
                  final item = entry.value;
                  final price = (item["price"] as num).toStringAsFixed(2);
                  return CheckboxListTile(
                    value: checked[index],
                    onChanged: (val) =>
                        setDialogState(() => checked[index] = val ?? false),
                    title: Text(
                      "#${item['product_number']}  ${item['description']}",
                    ),
                    subtitle: Text("${item['count']}x  \u20ac$price"),
                    controlAffinity: ListTileControlAffinity.leading,
                    dense: true,
                  );
                }),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text("Skip"),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text("Merge Checked"),
            ),
          ],
        ),
      ),
    );

    if (confirmed != true) return null;
    final checkedItems = <Map<String, dynamic>>[
      for (int i = 0; i < items.length; i++)
        if (checked[i]) items[i],
    ];
    return checkedItems;
  }

  /// Step 2: collapses the current items by product_number (Python
  /// services/receipt_parser.aggregate_items), then loads the app's
  /// ingredients so each collapsed item can be manually matched to one
  /// before submitting a restock. This is a separate, explicit step from
  /// parsing so the user can finish cleaning up (edit/delete/merge/re-parse)
  /// the raw per-line results first.
  Future<void> _collapseAndMatch() async {
    final unmatchedCount =
        groups.where((g) => g["type"] == "unmatched").length;
    if (unmatchedCount > 0) {
      final proceed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text("Unresolved lines"),
          content: Text(
            "There are $unmatchedCount unresolved line(s) that will be "
            "excluded from the restock. Continue anyway?",
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text("Cancel"),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text("Continue"),
            ),
          ],
        ),
      );
      if (proceed != true) return;
    }

    final itemsOnly = groups.where((g) => g["type"] == "item").toList();
    if (itemsOnly.isEmpty) {
      _showDialog("Nothing to match", "There are no parsed items to collapse.");
      return;
    }

    setState(() {
      loadingIngredients = true;
    });

    try {
      final String? response = await channel.invokeMethod<String>(
        "aggregate_receipt_items",
        {"items": jsonEncode(itemsOnly)},
      );
      if (response == null) return;

      final List<dynamic> aggregated = jsonDecode(response) as List<dynamic>;
      var aggregatedList = aggregated.cast<Map<String, dynamic>>();

      final settings = await _parsingSettingsService.loadSettings();
      aggregatedList =
          await _reviewFuzzyMergeCandidates(aggregatedList, settings);

      final fetchedIngredients = await PyBridge().getIngredients();

      // Prefill each item's ingredient dropdown with a best-guess match
      // (fuzzy word matching against descriptions) -- the user still
      // reviews/confirms every suggestion before submitting.
      Map<String, int?> suggestions = {};
      try {
        suggestions = await PyBridge().suggestReceiptIngredientMatches(
          items: aggregatedList,
          ingredients: fetchedIngredients,
        );
      } catch (e) {
        // Prefilling is a convenience only; fall back to unmatched.
      }

      _disposeMatchingControllers();
      final newAggregatedItems = aggregatedList.asMap().entries.map((entry) {
        return Map<String, dynamic>.from(entry.value)
          ..["matched_ingredient_id"] = suggestions[entry.key.toString()];
      }).toList();

      for (int i = 0; i < newAggregatedItems.length; i++) {
        final count = newAggregatedItems[i]["count"] as int;
        final price = (newAggregatedItems[i]["price"] as num).toDouble();
        final pricePerPackage = count > 0 ? price / count : price;
        _quantityControllers[i] =
            TextEditingController(text: count.toString());
        _priceControllers[i] =
            TextEditingController(text: pricePerPackage.toStringAsFixed(2));
      }

      setState(() {
        ingredients = fetchedIngredients;
        aggregatedItems = newAggregatedItems;
        loadingIngredients = false;
        showMatchingStep = true;
      });
    } catch (e) {
      setState(() {
        loadingIngredients = false;
      });
      _showDialog("Error", "Failed to collapse/match items: $e");
    }
  }

  Future<void> _submitRestock() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    final salesmanId = auth.currentUserId;
    if (salesmanId == null) {
      _showDialog("Error", "Unable to identify current user.");
      return;
    }

    final restockData = <Map<String, dynamic>>[];
    final summaryLines = <String>[];
    double totalSum = 0.0;
    for (int i = 0; i < aggregatedItems.length; i++) {
      final ingredientId = aggregatedItems[i]["matched_ingredient_id"] as int?;
      if (ingredientId == null) continue;
      final quantity = int.tryParse(_quantityControllers[i]?.text.trim() ?? "");
      final price = double.tryParse(_priceControllers[i]?.text.trim() ?? "");
      if (quantity == null || quantity < 1) continue;
      restockData.add({
        "id": ingredientId,
        "restock": quantity,
        if (price != null) "price": price,
      });

      final ingredient = ingredients.firstWhere(
        (ing) => ing["ingredient_id"] == ingredientId,
        orElse: () => <String, dynamic>{},
      );
      final name = ingredient["name"] as String? ?? "Unknown";
      final effectivePrice = price ?? 0.0;
      final lineTotal = effectivePrice * quantity;
      totalSum += lineTotal;
      summaryLines.add(
        '$name x$quantity: \u20ac${effectivePrice.toStringAsFixed(2)} = '
        '\u20ac${lineTotal.toStringAsFixed(2)}',
      );
    }

    if (restockData.isEmpty) {
      _showDialog("Error", "No items matched to ingredients yet.");
      return;
    }

    final confirmed = await _showRestockConfirmationDialog(summaryLines, totalSum);
    if (!confirmed) return;

    setState(() => submittingRestock = true);
    final error = await PyBridge().restockIngredients(restockData, salesmanId);
    setState(() => submittingRestock = false);

    if (error != null) {
      _showDialog("Error", "Restock failed: $error");
    } else {
      _showDialog(
        "Success",
        "Restock submitted for ${restockData.length} ingredient(s).",
      );
    }
  }

  /// Shows a summary of what's about to be restocked (name, quantity, price,
  /// total) before actually submitting -- mirrors restock_ingredients_page's
  /// confirmation dialog so this flow ends the same way the normal restock
  /// flow does.
  Future<bool> _showRestockConfirmationDialog(
    List<String> summaryLines,
    double totalSum,
  ) async {
    return await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text("Confirm Restock"),
            content: ConstrainedBox(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(ctx).size.height * 0.6,
              ),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "List:",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    ...summaryLines.map((line) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 6),
                          child: Text(line, style: const TextStyle(fontSize: 13)),
                        )),
                    const SizedBox(height: 12),
                    Text(
                      "Total sum: \u20ac${totalSum.toStringAsFixed(2)}",
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text("Cancel"),
              ),
              ElevatedButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                child: const Text("Confirm"),
              ),
            ],
          ),
        ) ??
        false;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Scan Receipt"),
        actions: [
          if (!showMatchingStep) ...[
            IconButton(
              icon: const Icon(Icons.undo),
              tooltip: "Undo last edit/merge/delete",
              onPressed: _history.isNotEmpty ? _undo : null,
            ),
            IconButton(
              icon: const Icon(Icons.settings),
              tooltip: "Receipt Parsing Settings",
              onPressed: () =>
                  Navigator.pushNamed(context, '/receipt_parsing_settings'),
            ),
          ],
        ],
      ),
      floatingActionButton: showMatchingStep
          ? null
          : FloatingActionButton.extended(
              onPressed: processing ? null : pickImages,
              icon: const Icon(Icons.image),
              label: const Text("Scan Page(s)"),
            ),
      body: SafeArea(
        child: showMatchingStep ? _buildMatchingBody() : _buildScanBody(),
      ),
    );
  }

  Widget _buildScanBody() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (images.isNotEmpty)
            SizedBox(
              height: 150,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: images.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (_, i) => ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(images[i], height: 150),
                ),
              ),
            ),
          const SizedBox(height: 20),
          if (processing)
            const Center(
              child: CircularProgressIndicator(),
            ),
          ParsedItemsSection(
            groups: groups,
            displayTextFor: (group) => displayTextFor(group, rowTexts),
            onEdit: _editGroup,
            onDelete: _deleteGroup,
            onMerge: _mergeWithNext,
            onReparse: _reparseGroup,
            onNext: _collapseAndMatch,
          ),
        ],
      ),
    );
  }

  Widget _buildMatchingBody() {
    return IngredientMatchingSection(
      aggregatedItems: aggregatedItems,
      ingredients: ingredients,
      quantityControllers: _quantityControllers,
      priceControllers: _priceControllers,
      loadingIngredients: loadingIngredients,
      submittingRestock: submittingRestock,
      onBack: () => setState(() => showMatchingStep = false),
      onSubmit: _submitRestock,
      onIngredientChanged: (index, ingredientId) => setState(() {
        aggregatedItems[index]["matched_ingredient_id"] = ingredientId;
      }),
    );
  }
}
