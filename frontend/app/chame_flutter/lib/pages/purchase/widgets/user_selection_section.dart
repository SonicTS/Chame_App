import 'package:flutter/material.dart';
import 'package:chame_flutter/widgets/shared/user_dropdown_selector.dart';
import 'package:chame_flutter/widgets/shared/user_balance_card.dart';

/// Consumer picker for the purchase page: a searchable user dropdown plus a
/// balance card (with a preview of the pending cart deduction) for whoever
/// is selected.
class UserSelectionSection extends StatelessWidget {
  final List<Map<String, dynamic>> users;
  final int? selectedUserId;
  final Map<String, dynamic>? selectedUser;
  final double? pendingDeduction;
  final ValueChanged<Map<String, dynamic>?> onUserChanged;

  const UserSelectionSection({
    super.key,
    required this.users,
    required this.selectedUserId,
    required this.selectedUser,
    required this.pendingDeduction,
    required this.onUserChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        UserDropdownSelector(
          users: users,
          selectedUserId: selectedUserId,
          onChanged: onUserChanged,
          label: 'Select User',
        ),
        if (selectedUser != null) ...[
          const SizedBox(height: 12),
          UserBalanceCard(
            balance: (selectedUser!['balance'] as num?)?.toDouble() ?? 0.0,
            pendingDeduction: pendingDeduction,
          ),
        ],
      ],
    );
  }
}
