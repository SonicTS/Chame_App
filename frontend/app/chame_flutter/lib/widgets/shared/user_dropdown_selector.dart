import 'package:flutter/material.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';

/// Searchable dropdown for picking a user out of a list.
///
/// This is intentionally generic (just users in, a selection out) so it can
/// be reused anywhere a user needs to be picked, e.g. the purchase page's
/// "consumer" selector or the login screen's quick-login selector (which is
/// just this widget with a role filter applied to [users]).
class UserDropdownSelector extends StatelessWidget {
  final List<Map<String, dynamic>> users;
  final int? selectedUserId;
  final ValueChanged<Map<String, dynamic>?> onChanged;
  final String label;

  /// Builds the label shown for each user in the list/search box.
  /// Defaults to just the user's name.
  final String Function(Map<String, dynamic> user)? itemLabelBuilder;

  const UserDropdownSelector({
    super.key,
    required this.users,
    required this.selectedUserId,
    required this.onChanged,
    this.label = 'Select User',
    this.itemLabelBuilder,
  });

  @override
  Widget build(BuildContext context) {
    return DropdownSearch<Map<String, dynamic>>(
      items: (String? filter, _) {
        final filtered = filter == null || filter.isEmpty
            ? users
            : users
                .where((u) => (u['name'] ?? '')
                    .toString()
                    .toLowerCase()
                    .contains(filter.toLowerCase()))
                .toList();
        return Future.value(filtered);
      },
      selectedItem: users.firstWhereOrNull((u) => u['user_id'] == selectedUserId),
      itemAsString: itemLabelBuilder ?? (u) => u['name'] ?? '',
      compareFn: (a, b) => a['user_id'] == b['user_id'],
      onChanged: onChanged,
      popupProps: const PopupProps.menu(
        showSearchBox: true,
      ),
      decoratorProps: DropDownDecoratorProps(
        decoration: InputDecoration(labelText: label),
      ),
    );
  }
}
