import 'package:flutter/material.dart';

import 'parsed_item_card.dart';

/// Step 1: the "Parsed Items" list (clean up OCR'd lines by editing,
/// deleting, merging, or re-parsing them) plus the button that moves on to
/// collapsing + ingredient matching.
class ParsedItemsSection extends StatelessWidget {
  final List<Map<String, dynamic>> groups;
  final String Function(Map<String, dynamic> group) displayTextFor;
  final void Function(int index) onEdit;
  final void Function(int index) onDelete;
  final void Function(int index) onMerge;
  final void Function(int index) onReparse;
  final VoidCallback? onNext;

  const ParsedItemsSection({
    super.key,
    required this.groups,
    required this.displayTextFor,
    required this.onEdit,
    required this.onDelete,
    required this.onMerge,
    required this.onReparse,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Parsed Items (from Python)",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        const SizedBox(height: 8),
        if (groups.isEmpty)
          const Text("No parsed items yet.")
        else
          ...groups.asMap().entries.map((entry) {
            final index = entry.key;
            final group = entry.value;
            return ParsedItemCard(
              displayText: displayTextFor(group),
              lineNumbers: (group["line_numbers"] as List).cast<int>(),
              isItem: group["type"] == "item",
              verified: group["verified"] == true,
              reason: group["reason"] as String?,
              canMergeWithNext: index < groups.length - 1,
              onEdit: () => onEdit(index),
              onDelete: () => onDelete(index),
              onMerge: () => onMerge(index),
              onReparse: () => onReparse(index),
            );
          }),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          icon: const Icon(Icons.arrow_forward),
          label: const Text("Next: Collapse & Match Ingredients"),
          onPressed: groups.isEmpty ? null : onNext,
        ),
      ],
    );
  }
}
