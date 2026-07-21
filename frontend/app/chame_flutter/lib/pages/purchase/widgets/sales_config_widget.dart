import 'package:flutter/material.dart';

/// "All / Raw / Toast" filter dropdown shown above the sales table.
class SalesConfigWidget extends StatelessWidget {
  final String salesConfig;
  final ValueChanged<String> onConfigChanged;

  const SalesConfigWidget({
    super.key,
    required this.salesConfig,
    required this.onConfigChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Text('Configure Sales Table:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(width: 12),
        Expanded(
          child: DropdownButton<String>(
            value: salesConfig,
            isExpanded: true,
            items: const [
              DropdownMenuItem(value: 'all', child: Text('All')),
              DropdownMenuItem(value: 'raw', child: Text('Raw')),
              DropdownMenuItem(value: 'toast', child: Text('Toast')),
            ],
            onChanged: (val) => onConfigChanged(val!),
          ),
        ),
      ],
    );
  }
}
