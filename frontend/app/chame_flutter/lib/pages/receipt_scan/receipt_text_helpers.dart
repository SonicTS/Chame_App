/// Pure text-reconstruction helpers for receipt scanning groups.
///
/// A "group" is a parsed/unmatched entry as returned by
/// services/receipt_parser.py (via the parse_receipt_lines /
/// aggregate_receipt_items bridge calls), e.g.:
/// {type: 'item'|'unmatched', count, product_number, description, price,
///  letter, line_numbers, verified, reason?, text?, text_override?}
library;

/// Text to display/edit for a group: a manual override if the user has
/// edited it, otherwise the parsed structured fields for a matched item,
/// otherwise the raw text (falling back to the original OCR line(s)).
String displayTextFor(Map<String, dynamic> group, List<String> rowTexts) {
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
  return _rawLinesFor(group, rowTexts);
}

/// Text to use as input for merging/re-parsing: a manual override if the
/// user has edited it, otherwise the raw "text" the parser attached
/// (mismatched multiplier pairs and unmatched lines keep their original
/// text), otherwise the original OCR line(s). Unlike [displayTextFor], this
/// NEVER reconstructs the prettified "1x #number description €price A"
/// summary for matched items, since that summary doesn't match the parser's
/// expected line format and would need to be manually stripped before
/// merging/re-parsing could work.
String rawTextFor(Map<String, dynamic> group, List<String> rowTexts) {
  if (group["text_override"] != null) {
    return group["text_override"] as String;
  }
  if (group["text"] != null) {
    return group["text"] as String;
  }
  return _rawLinesFor(group, rowTexts);
}

String _rawLinesFor(Map<String, dynamic> group, List<String> rowTexts) {
  final lineNumbers = (group["line_numbers"] as List).cast<int>();
  return lineNumbers
      .map((n) => (n >= 0 && n < rowTexts.length) ? rowTexts[n] : "")
      .join("\n");
}
