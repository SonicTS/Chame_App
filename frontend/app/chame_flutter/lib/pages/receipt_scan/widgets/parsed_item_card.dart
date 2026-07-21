import 'package:flutter/material.dart';

/// One parsed/unmatched receipt line group, with edit/delete/merge/re-parse
/// actions. Purely presentational -- all state lives in ReceiptScanPage.
class ParsedItemCard extends StatelessWidget {
  final String displayText;
  final List<int> lineNumbers;
  final bool isItem;
  final bool verified;
  final String? reason;
  final bool canMergeWithNext;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final VoidCallback? onMerge;
  final VoidCallback onReparse;

  const ParsedItemCard({
    super.key,
    required this.displayText,
    required this.lineNumbers,
    required this.isItem,
    required this.verified,
    required this.reason,
    required this.canMergeWithNext,
    required this.onEdit,
    required this.onDelete,
    required this.onMerge,
    required this.onReparse,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      color: !isItem
          ? Colors.red.shade50
          : (verified ? Colors.green.shade50 : Colors.orange.shade50),
      child: ListTile(
        title: Text(displayText),
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
              onPressed: onEdit,
            ),
            IconButton(
              icon: const Icon(Icons.delete),
              tooltip: "Delete entry",
              onPressed: onDelete,
            ),
            IconButton(
              icon: const Icon(Icons.merge),
              tooltip: "Merge with next line",
              onPressed: canMergeWithNext ? onMerge : null,
            ),
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: "Re-parse this entry",
              onPressed: onReparse,
            ),
          ],
        ),
      ),
    );
  }
}
