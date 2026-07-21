import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:chame_flutter/data/py_bride.dart';

void main() {
  runApp(const OcrTestApp());
}

class OcrTestApp extends StatelessWidget {
  const OcrTestApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "OCR Test",
      theme: ThemeData(
        colorSchemeSeed: Colors.blue,
      ),
      home: const OcrTestPage(),
    );
  }
}

class OcrTestPage extends StatefulWidget {
  const OcrTestPage({super.key});

  @override
  State<OcrTestPage> createState() => _OcrTestPageState();
}

class _OcrTestPageState extends State<OcrTestPage> {
  static const MethodChannel channel =
      MethodChannel("samples.flutter.dev/chame/python");

  final ImagePicker picker = ImagePicker();

  File? image;

  String recognizedText = "";
  String rowGroupedText = "";
  String rawJson = "";
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

  // Store-specific product number that identifies a "Pfand" (bottle
  // deposit) line on the receipt. The description text for these lines can
  // vary, so the user provides the fixed product number instead.
  final TextEditingController _pfandCodeController = TextEditingController();

  // Step 2: collapsing + ingredient matching + restock submission.
  bool showMatchingStep = false;
  bool loadingIngredients = false;
  bool submittingRestock = false;
  List<Map<String, dynamic>> aggregatedItems = [];
  List<Map<String, dynamic>> ingredients = [];
  final TextEditingController _salesmanIdController = TextEditingController();
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
    _pfandCodeController.dispose();
    _salesmanIdController.dispose();
    _disposeMatchingControllers();
    super.dispose();
  }

  Future<void> pickImage() async {
    final XFile? file = await picker.pickImage(
    source: ImageSource.camera,
  );

    if (file == null) return;

    final CroppedFile? cropped = await ImageCropper().cropImage(
      sourcePath: file.path,
      uiSettings: [
        AndroidUiSettings(
          toolbarTitle: 'Crop Receipt',
          lockAspectRatio: false, // let user pick any rectangle
        ),
      ],
    );
    if (cropped == null) return; // user cancelled

    setState(() {
      image = File(cropped.path);
      processing = true;
      recognizedText = "";
      rowGroupedText = "";
      rawJson = "";
      rowTexts = [];
      groups = [];
      _history.clear();
    });

    try {
      final String? response = await channel.invokeMethod<String>(
        "recognize_image",
        {
          "image_path": cropped.path,
        },
      );

      if (response == null) {
        throw Exception("OCR returned null");
      }

      final Map<String, dynamic> json =
          jsonDecode(response) as Map<String, dynamic>;

      // "rows" is our custom y-only grouping (one entry per visual row on
      // the receipt, regardless of horizontal whitespace). "text" is ML
      // Kit's own raw reconstruction, which DOES split on whitespace/columns
      // and is kept here only for comparison.
      final List<dynamic> rows = json["rows"] as List<dynamic>? ?? [];
      final List<String> rowTextList = rows
          .map((row) => (row as Map<String, dynamic>)["text"] as String? ?? "")
          .toList();
      final String groupedText = rowTextList.join("\n");

      setState(() {
        rawJson = const JsonEncoder.withIndent("  ").convert(json);
        recognizedText = json["text"] ?? "";
        rowGroupedText = groupedText;
        rowTexts = rowTextList;
      });

      // Item parsing/heuristics live in Python (services/receipt_parser.py),
      // not in Dart or Kotlin.
      await _parseReceipt(rowTextList);
    } on PlatformException catch (e) {
      setState(() {
        recognizedText = "Platform Error:\n${e.message}";
      });
    } catch (e) {
      setState(() {
        recognizedText = e.toString();
      });
    }

    setState(() {
      processing = false;
    });
  }

  /// Sends the OCR'd row text to Python (services/admin_api.parse_receipt_lines
  /// -> services/receipt_parser.parse_receipt_lines) for item/heuristic
  /// parsing, then flattens the result into a single editable list of groups.
  Future<void> _parseReceipt(List<String> lines) async {
    try {
      final String? response = await channel.invokeMethod<String>(
        "parse_receipt_lines",
        {
          "lines": jsonEncode(lines),
          "pfand_product_number": _pfandCodeController.text.trim(),
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

  /// Text to display/edit for a group: a manual override if the user has
  /// edited it, otherwise the parsed structured fields for a matched item,
  /// otherwise the raw text (falling back to the original OCR line(s)).
  String _displayTextFor(Map<String, dynamic> group) {
    if (group["text_override"] != null) {
      return group["text_override"] as String;
    }
    if (group["type"] == "item") {
      final count = group["count"];
      final productNumber = group["product_number"];
      final description = group["description"];
      final price = (group["price"] as num).toStringAsFixed(2);
      final letter = group["letter"];
      final pfandPrice = group["pfand_price"] as num?;
      final pfandSuffix =
          pfandPrice != null ? " (+€${pfandPrice.toStringAsFixed(2)} PF)" : "";
      return "${count}x  #$productNumber  $description  €$price$pfandSuffix $letter";
    }
    if (group["text"] != null) {
      return group["text"] as String;
    }
    final lineNumbers = (group["line_numbers"] as List).cast<int>();
    return lineNumbers
        .map((n) => (n >= 0 && n < rowTexts.length) ? rowTexts[n] : "")
        .join("\n");
  }

  /// Text to use as input for merging/re-parsing: a manual override if the
  /// user has edited it, otherwise the raw "text" the parser attached
  /// (mismatched multiplier pairs and unmatched lines keep their original
  /// text), otherwise the original OCR line(s). Unlike [_displayTextFor],
  /// this NEVER reconstructs the prettified "1x #number description €price
  /// A" summary for matched items, since that summary doesn't match the
  /// parser's expected line format and would need to be manually stripped
  /// before merging/re-parsing could work.
  String _rawTextFor(Map<String, dynamic> group) {
    if (group["text_override"] != null) {
      return group["text_override"] as String;
    }
    if (group["text"] != null) {
      return group["text"] as String;
    }
    final lineNumbers = (group["line_numbers"] as List).cast<int>();
    return lineNumbers
        .map((n) => (n >= 0 && n < rowTexts.length) ? rowTexts[n] : "")
        .join("\n");
  }

  Future<void> _editGroup(int index) async {
    final controller =
        TextEditingController(text: _displayTextFor(groups[index]));
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
      "text_override": "${_rawTextFor(current)}\n${_rawTextFor(next)}",
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
    final lines = _rawTextFor(groups[index]).split("\n");

    try {
      final String? response = await channel.invokeMethod<String>(
        "parse_receipt_lines",
        {
          "lines": jsonEncode(lines),
          "pfand_product_number": _pfandCodeController.text.trim(),
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

  /// Step 2: collapses the current items by product_number (Python
  /// services/receipt_parser.aggregate_items), then loads the app's
  /// ingredients so each collapsed item can be manually matched to one
  /// before submitting a restock. This is a separate, explicit step from
  /// parsing so the user can finish cleaning up (edit/delete/merge/re-parse)
  /// the raw per-line results first.
  Future<void> _collapseAndMatch() async {
    final unmatchedCount = groups.where((g) => g["type"] == "unmatched").length;
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
      final fetchedIngredients = await PyBridge().getIngredients();

      _disposeMatchingControllers();
      final newAggregatedItems = aggregated
          .cast<Map<String, dynamic>>()
          .map((raw) => Map<String, dynamic>.from(raw)..["matched_ingredient_id"] = null)
          .toList();

      for (int i = 0; i < newAggregatedItems.length; i++) {
        final count = newAggregatedItems[i]["count"] as int;
        final price = (newAggregatedItems[i]["price"] as num).toDouble();
        final pricePerPackage = count > 0 ? price / count : price;
        _quantityControllers[i] = TextEditingController(text: count.toString());
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
    final salesmanId = int.tryParse(_salesmanIdController.text.trim());
    if (salesmanId == null) {
      _showDialog("Error", "Please enter a valid salesman user ID.");
      return;
    }

    final restockData = <Map<String, dynamic>>[];
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
    }

    if (restockData.isEmpty) {
      _showDialog("Error", "No items matched to ingredients yet.");
      return;
    }

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

  Widget _buildAggregatedItemCard(int index) {
    final item = aggregatedItems[index];
    final lineNumbers = (item["line_numbers"] as List).cast<int>();
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
            Text("lines: ${lineNumbers.join(', ')}"),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              decoration: const InputDecoration(labelText: "Match to ingredient"),
              value: item["matched_ingredient_id"] as int?,
              items: ingredients
                  .map((ing) => DropdownMenuItem<int>(
                        value: ing["ingredient_id"] as int,
                        child: Text(ing["name"] as String? ?? "Unknown"),
                      ))
                  .toList(),
              onChanged: (val) =>
                  setState(() => item["matched_ingredient_id"] = val),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _quantityControllers[index],
                    decoration:
                        const InputDecoration(labelText: "Restock quantity"),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _priceControllers[index],
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

  Widget _buildMatchingStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            IconButton(
              icon: const Icon(Icons.arrow_back),
              tooltip: "Back to editing",
              onPressed: () => setState(() => showMatchingStep = false),
            ),
            const Text(
              "Match Ingredients & Restock",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _salesmanIdController,
          decoration: const InputDecoration(
            labelText: "Salesman user ID",
            hintText: "Your user_id for this restock",
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 16),
        if (loadingIngredients)
          const Center(child: CircularProgressIndicator())
        else
          ...aggregatedItems
              .asMap()
              .keys
              .map((index) => _buildAggregatedItemCard(index)),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          icon: const Icon(Icons.inventory),
          label: const Text("Submit Restock"),
          onPressed: submittingRestock ? null : _submitRestock,
        ),
      ],
    );
  }

  Widget _buildGroupCard(int index) {
    final group = groups[index];
    final bool isItem = group["type"] == "item";
    final bool verified = group["verified"] == true;
    final lineNumbers = (group["line_numbers"] as List).cast<int>();
    final String? reason = group["reason"] as String?;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      color: !isItem
          ? Colors.red.shade50
          : (verified ? Colors.green.shade50 : Colors.orange.shade50),
      child: ListTile(
        title: Text(_displayTextFor(group)),
        subtitle: Text(
          "lines: ${lineNumbers.join(', ')}"
          "${reason != null ? '\nReason: $reason' : ''}",
        ),
        isThreeLine: reason != null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.edit),
              tooltip: "Edit text",
              onPressed: () => _editGroup(index),
            ),
            IconButton(
              icon: const Icon(Icons.delete),
              tooltip: "Delete entry",
              onPressed: () => _deleteGroup(index),
            ),
            IconButton(
              icon: const Icon(Icons.merge),
              tooltip: "Merge with next line",
              onPressed:
                  index < groups.length - 1 ? () => _mergeWithNext(index) : null,
            ),
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: "Re-parse this entry",
              onPressed: () => _reparseGroup(index),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("OCR Test"),
        actions: [
          IconButton(
            icon: const Icon(Icons.undo),
            tooltip: "Undo last edit/merge/delete",
            onPressed: _history.isNotEmpty ? _undo : null,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: processing ? null : pickImage,
        icon: const Icon(Icons.image),
        label: const Text("Take / Select Image"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _pfandCodeController,
              decoration: const InputDecoration(
                labelText: "Pfand product number (optional)",
                hintText: "e.g. 80000291",
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
            ),

            const SizedBox(height: 16),

            if (image != null)
              Image.file(
                image!,
                height: 250,
              ),

            const SizedBox(height: 20),

            if (processing)
              const Center(
                child: CircularProgressIndicator(),
              ),

            if (showMatchingStep)
              _buildMatchingStep()
            else ...[
              const Text(
                "Parsed Items (from Python)",
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),

              const SizedBox(height: 8),

              if (groups.isEmpty)
                const Text("No parsed items yet.")
              else
                ...groups.asMap().keys.map((index) => _buildGroupCard(index)),

              const SizedBox(height: 16),

              ElevatedButton.icon(
                icon: const Icon(Icons.arrow_forward),
                label: const Text("Next: Collapse & Match Ingredients"),
                onPressed: groups.isEmpty ? null : _collapseAndMatch,
              ),
            ],

            const SizedBox(height: 30),

            const Text(
              "Rows (grouped by Y only)",
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),

            const SizedBox(height: 8),

            SelectableText(rowGroupedText),

            const SizedBox(height: 30),

            const Text(
              "Recognized Text (ML Kit raw, for comparison)",
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),

            const SizedBox(height: 8),

            SelectableText(recognizedText),

            const SizedBox(height: 30),

            const Text(
              "Raw JSON",
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),

            const SizedBox(height: 8),

            SelectableText(rawJson),
          ],
        ),
      ),
    );
  }
}