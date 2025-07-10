import 'package:chame_flutter/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/widgets/simple_deletion_dialog.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';
import 'package:provider/provider.dart';

class UsersPage extends StatefulWidget {
  const UsersPage({super.key});

  @override
  State<UsersPage> createState() => _UsersPageState();
}

class _UsersPageState extends State<UsersPage> {
  late Future<List<Map<String, dynamic>>> _usersFuture;
  late Future<List<Map<String, dynamic>>> _transactionsFuture;
  bool _isSubmitting = false;
  final Map<int, TextEditingController> _depositControllers = {};
  final Map<int, TextEditingController> _withdrawControllers = {};
  String _txUserFilter = 'all';
  String _txTypeFilter = 'all';
  String _userTableNameFilter = '';
  // Add scroll controllers for users and transactions tables
  final ScrollController _mainScrollController = ScrollController();
  final ScrollController _transactionsTableScrollController = ScrollController();
  final ScrollController _usersTableHorizontalController = ScrollController();
  final ScrollController _usersTableVerticalController = ScrollController();

  @override
  void initState() {
    super.initState();
    // Initialize scroll controllers here to ensure they're ready
    // No additional initialization needed as they're already created
    _reload();
  }

  void _reload() {
    setState(() {
      _usersFuture = PyBridge().getAllUsers();
      _transactionsFuture = PyBridge().getFilteredTransaction(userId: _txUserFilter, txType: _txTypeFilter);
    });
  }

  Future<void> _deposit(int userId) async {
    final controller = _depositControllers[userId]!;
    final amount = double.tryParse(controller.text);
    if (amount == null || amount <= 0) return;
    setState(() => _isSubmitting = true);
    final error = await PyBridge().deposit(userId: userId, amount: amount);
    setState(() => _isSubmitting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'Deposit successful!');
      controller.clear();
      _reload();
    }
  }

  Future<void> _withdraw(int userId) async {
    final controller = _withdrawControllers[userId]!;
    final amount = double.tryParse(controller.text);
    if (amount == null || amount <= 0) return;
    setState(() => _isSubmitting = true);
    final error = await PyBridge().withdraw(userId: userId, amount: amount);
    setState(() => _isSubmitting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'Withdraw successful!');
      controller.clear();
      _reload();
    }
  }

  // Show restore dialog with deleted users
  void _showRestoreUsersDialog(BuildContext context) async {
    try {
      final deletedUsers = await PyBridge().getDeletedUsers();
      
      if (!context.mounted) return;
      
      if (deletedUsers.isEmpty) {
        _showDialog('No Deleted Users', 'There are no deleted users to restore.');
        return;
      }

      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Restore Deleted Users'),
          content: SizedBox(
            width: double.maxFinite,
            height: 400,
            child: ListView.builder(
              itemCount: deletedUsers.length,
              itemBuilder: (context, index) {
                final user = deletedUsers[index];
                return Card(
                  child: ListTile(
                    title: Text(user['name']?.toString() ?? 'Unknown'),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Role: ${user['role']?.toString() ?? 'N/A'}'),
                        Text('Balance: ${user['balance']?.toString() ?? 'N/A'}'),
                        Text('Deleted: ${user['deleted_at']?.toString().split('T')[0] ?? 'N/A'}'),
                        Text('By: ${user['deleted_by']?.toString() ?? 'Unknown'}'),
                      ],
                    ),
                    trailing: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        _performUserRestore(
                          context,
                          user['user_id'] as int,
                          user['name']?.toString() ?? 'Unknown',
                        );
                      },
                      child: const Text('Restore'),
                    ),
                  ),
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (context.mounted) {
        _showDialog('Error', 'Failed to load deleted users: $e');
      }
    }
  }

  // Perform user restoration
  Future<void> _performUserRestore(BuildContext context, int userId, String userName) async {
    try {
      final error = await PyBridge().restoreUser(userId: userId);
      
      if (error != null) {
        // Check if this is a dependency-related error and show appropriate message
        if (error.toLowerCase().contains('cannot be restored') || 
            error.toLowerCase().contains('dependency') ||
            error.toLowerCase().contains('required')) {
          _showDialog('Cannot Restore User', error);
        } else {
          _showDialog('Error', 'Failed to restore user: $error');
        }
      } else {
        _showDialog('Success', 'User "$userName" restored successfully!');
        _reload();
      }
    } catch (e) {
      _showDialog('Error', 'Failed to restore user: $e');
    }
  }

  void _showDialog(String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))],
      ),
    );
  }

  @override
  void dispose() {
    for (final c in _depositControllers.values) {
      c.dispose();
    }
    for (final c in _withdrawControllers.values) {
      c.dispose();
    }
    // Dispose scroll controllers
    _mainScrollController.dispose();
    _transactionsTableScrollController.dispose();
    _usersTableVerticalController.dispose();
    _usersTableHorizontalController.dispose();
    super.dispose();
  }

  // Helper for formatting timestamp in transactions
  String _formatTimestamp(dynamic ts) {
    if (ts == null) return '';
    if (ts is DateTime) return ts.toString();
    if (ts is String) return ts;
    return ts.toString();
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    final double tableHeight = MediaQuery.of(context).size.height * 0.3;
    return Scaffold(
      appBar: AppBar(title: const Text('Users')),
      body: SafeArea(
        child: SingleChildScrollView(
          controller: _mainScrollController,
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. USERS TABLE SECTION HEADER
                if (auth.role == 'admin' || auth.role == 'wirt')
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16.0),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Expanded(
                          child: Text('Users', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                        ),
                        Row(
                          children: [
                            ElevatedButton.icon(
                              onPressed: () {
                                Navigator.of(context).pushNamed('/add_user').then((_) {
                                  // Reload users when coming back from add user page
                                  _reload();
                                });
                              },
                              icon: const Icon(Icons.person_add),
                              label: const Text('Add User'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                            ),
                            if (auth.role == 'admin') ...[
                              const SizedBox(width: 8),
                              ElevatedButton(
                                onPressed: () => _showRestoreUsersDialog(context),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.orange,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                ),
                                child: const Text('Restore', style: TextStyle(fontSize: 12)),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                // 1. USERS TABLE SECTION
                UsersTableSection(
                  usersFuture: _usersFuture,
                  depositControllers: _depositControllers,
                  withdrawControllers: _withdrawControllers,
                  isSubmitting: _isSubmitting,
                  onDeposit: _deposit,
                  onWithdraw: _withdraw,
                  userTableNameFilter: _userTableNameFilter,
                  horizontalScrollController: _usersTableHorizontalController,
                  verticalScrollController: _usersTableVerticalController,
                  mainController: _mainScrollController,
                  authService: auth,
                  onReload: _reload,
                ),
                const SizedBox(height: 24),
                
                TextField(
                  decoration: const InputDecoration(
                    labelText: 'Filter users by name',
                    prefixIcon: Icon(Icons.search),
                    isDense: true,
                  ),
                  onChanged: (v) => setState(() => _userTableNameFilter = v.trim().toLowerCase()),
                ),
                const SizedBox(height: 8),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      const Text('User:'),
                      const SizedBox(width: 8),
                      FutureBuilder<List<Map<String, dynamic>>>(
                        future: _usersFuture,
                        builder: (context, snapshot) {
                          final txUsers = snapshot.data ?? [];
                          return SizedBox(
                            width: 220,
                            child: DropdownSearch<Map<String, dynamic>>(
                              items: (String? filter, _) {
                                final filtered = filter == null || filter.isEmpty
                                    ? txUsers
                                    : txUsers.where((u) => (u['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
                                return Future.value(filtered);
                              },
                              selectedItem: txUsers.firstWhereOrNull((u) => u['user_id'].toString() == _txUserFilter),
                              itemAsString: (u) => u['name'] ?? '',
                              compareFn: (a, b) => a['user_id'].toString() == b['user_id'].toString(),
                              onChanged: (val) {
                                setState(() {
                                  _txUserFilter = val?['user_id'].toString() ?? 'all';
                                  _transactionsFuture = PyBridge().getFilteredTransaction(userId: _txUserFilter, txType: _txTypeFilter);
                                });
                              },
                              popupProps: const PopupProps.menu(
                                showSearchBox: true,
                              ),
                              decoratorProps: const DropDownDecoratorProps(
                                decoration: InputDecoration(labelText: 'Filter by User'),
                              ),
                            ),
                          );
                        },
                      ),
                      const SizedBox(width: 16),
                      const Text('Type:'),
                      const SizedBox(width: 8),
                      DropdownButton<String>(
                        value: _txTypeFilter,
                        items: const [
                          DropdownMenuItem(value: 'all', child: Text('All')),
                          DropdownMenuItem(value: 'deposit', child: Text('Deposit')),
                          DropdownMenuItem(value: 'withdraw', child: Text('Withdraw')),
                        ],
                        onChanged: (val) {
                          setState(() {
                            _txTypeFilter = val!;
                            _transactionsFuture = PyBridge().getFilteredTransaction(userId: _txUserFilter, txType: _txTypeFilter);
                          });
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                const Text('Transactions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                // 2. TRANSACTIONS SECTION
                TransactionsSection(
                  transactionsFuture: _transactionsFuture,
                  tableHeight: tableHeight,
                  formatTimestamp: _formatTimestamp,
                  scrollController: _transactionsTableScrollController,
                  mainController: _mainScrollController,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ------------------- USERS TABLE SECTION WIDGET -------------------

class UsersTableSection extends StatelessWidget {
  final Future<List<Map<String, dynamic>>> usersFuture;
  final Map<int, TextEditingController> depositControllers;
  final Map<int, TextEditingController> withdrawControllers;
  final bool isSubmitting;
  final Function(int) onDeposit;
  final Function(int) onWithdraw;
  final String userTableNameFilter;
  final ScrollController horizontalScrollController;
  final ScrollController verticalScrollController;
  final ScrollController mainController;
  final AuthService authService;
  final VoidCallback onReload;

  const UsersTableSection({
    super.key,
    required this.usersFuture,
    required this.depositControllers,
    required this.withdrawControllers,
    required this.isSubmitting,
    required this.onDeposit,
    required this.onWithdraw,
    required this.userTableNameFilter,
    required this.horizontalScrollController,
    required this.verticalScrollController,
    required this.mainController,
    required this.authService,
    required this.onReload,
  });

  // Static method to show dialog
  static void _showDialog(BuildContext context, String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))],
      ),
    );
  }

  // Show role change confirmation dialog
  void _showRoleChangeConfirmation(BuildContext context, int userId, String userName, String newRole) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirm Role Change'),
        content: Text('Are you sure you want to change the role of "$userName" to "$newRole"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await _changeUserRole(context, userId, newRole);
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }

  // Change user role
  Future<void> _changeUserRole(BuildContext context, int userId, String newRole) async {
    try {
      final error = await PyBridge().changeUserRole(userId: userId, newRole: newRole);
      if (error != null) {
        _showDialog(context, 'Error', error);
      } else {
        _showDialog(context, 'Success', 'Role changed successfully!');
        onReload();
      }
    } catch (e) {
      _showDialog(context, 'Error', 'Failed to change role: $e');
    }
  }

  // Show simple deletion dialog for users
  void _showDeletionDialog(BuildContext context, int userId, String userName) async {
    final result = await showSimpleDeletionDialog(
      context: context,
      entityType: 'user',
      entityId: userId,
      entityName: userName,
    );
    
    if (result == true) {
      // Deletion was successful, reload the users
      onReload();
    }
  }

  @override
  Widget build(BuildContext context) {
    final double tableHeight = MediaQuery.of(context).size.height * 0.3;
    return SizedBox(
      height: tableHeight,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: usersFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          final users = snapshot.data ?? [];
          final filteredUsers = userTableNameFilter.isEmpty
              ? users
              : users.where((u) => (u['name'] ?? '').toLowerCase().contains(userTableNameFilter)).toList();

          // Only build scrollable content if we have data
          if (filteredUsers.isEmpty) {
            return const Center(child: Text('No users found.'));
          }
          
          return Scrollbar(
            thumbVisibility: true,
            controller: horizontalScrollController,
            child: SingleChildScrollView(
              controller: horizontalScrollController,
              scrollDirection: Axis.horizontal,
              child: SizedBox(
                // Increased width to accommodate new columns
                width: 1000,
                child: Scrollbar(
                  thumbVisibility: true,
                  controller: verticalScrollController,
                  child: SingleChildScrollView(
                    controller: verticalScrollController,
                    scrollDirection: Axis.vertical,
                    physics: _CoordinatedScrollPhysics(
                      mainController: mainController,
                    ),
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('Name')),
                        DataColumn(label: Text('Balance')),
                        DataColumn(label: Text('Role')),
                        DataColumn(label: Text('Deposit')),
                        DataColumn(label: Text('Withdraw')),
                        DataColumn(label: Text('Actions')),
                      ],
                      rows: filteredUsers.map((user) {
                        final userId = user['user_id'] as int;
                        final userRole = user['role']?.toString() ?? 'user';
                        depositControllers.putIfAbsent(userId, () => TextEditingController());
                        withdrawControllers.putIfAbsent(userId, () => TextEditingController());
                        return DataRow(cells: [
                          DataCell(Text(user['name']?.toString() ?? '')),
                          DataCell(Text(user['balance']?.toString() ?? '')),
                          // Role dropdown (only for admin users)
                          DataCell(
                            authService.role == 'admin' 
                              ? DropdownButton<String>(
                                  value: userRole,
                                  isDense: true,
                                  items: const [
                                    DropdownMenuItem(value: 'user', child: Text('User')),
                                    DropdownMenuItem(value: 'admin', child: Text('Admin')),
                                    DropdownMenuItem(value: 'wirt', child: Text('Wirt')),
                                  ],
                                  onChanged: (newRole) {
                                    if (newRole != null && newRole != userRole) {
                                      _showRoleChangeConfirmation(context, userId, user['name']?.toString() ?? '', newRole);
                                    }
                                  },
                                )
                              : Text(userRole)
                          ),
                          DataCell(Row(
                            children: [
                              SizedBox(
                                width: 70,
                                child: TextField(
                                  controller: depositControllers[userId],
                                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                  decoration: const InputDecoration(hintText: 'Amount', isDense: true),
                                ),
                              ),
                              const SizedBox(width: 4),
                              ElevatedButton(
                                onPressed: isSubmitting ? null : () => onDeposit(userId),
                                child: const Text('Deposit'),
                              ),
                            ],
                          )),
                          DataCell(Row(
                            children: [
                              SizedBox(
                                width: 70,
                                child: TextField(
                                  controller: withdrawControllers[userId],
                                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                  decoration: const InputDecoration(hintText: 'Amount', isDense: true),
                                ),
                              ),
                              const SizedBox(width: 4),
                              ElevatedButton(
                                onPressed: isSubmitting ? null : () => onWithdraw(userId),
                                child: const Text('Withdraw'),
                              ),
                            ],
                          )),
                          // Actions column (only for admin users)
                          DataCell(
                            authService.role == 'admin'
                              ? IconButton(
                                  icon: const Icon(Icons.delete, color: Colors.red),
                                  tooltip: 'Delete User',
                                  onPressed: isSubmitting 
                                    ? null 
                                    : () => _showDeletionDialog(context, userId, user['name']?.toString() ?? ''),
                                )
                              : const SizedBox.shrink()
                          ),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}


// ------------------- TRANSACTIONS SECTION WIDGET -------------------

class TransactionsSection extends StatelessWidget {
  final Future<List<Map<String, dynamic>>> transactionsFuture;
  final double tableHeight;
  final String Function(dynamic) formatTimestamp;
  final ScrollController scrollController;
  final ScrollController mainController;

  const TransactionsSection({
    super.key,
    required this.transactionsFuture,
    required this.tableHeight,
    required this.formatTimestamp,
    required this.scrollController,
    required this.mainController,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: tableHeight,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: transactionsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          final txs = snapshot.data ?? [];
          if (txs.isEmpty) {
            return const Center(child: Text('No transactions found.'));
          }
          return Scrollbar(
            thumbVisibility: true,
            controller: scrollController,
            child: SingleChildScrollView(
              controller: scrollController,
              scrollDirection: Axis.horizontal,
              child: ConstrainedBox(
                // Set a minimum width so it scrolls if needed
                constraints: BoxConstraints(minWidth: MediaQuery.of(context).size.width),
                child: SingleChildScrollView(
                  scrollDirection: Axis.vertical,
                  physics: _CoordinatedScrollPhysics(
                    mainController: mainController,
                  ),
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('User')),
                      DataColumn(label: Text('Type')),
                      DataColumn(label: Text('Amount')),
                      DataColumn(label: Text('Comment')),
                      DataColumn(label: Text('Date')),
                    ],
                    rows: txs.map((tx) {
                      return DataRow(cells: [
                        DataCell(Text(tx['user']?['name'].toString() ?? '')),
                        DataCell(Text(tx['type']?.toString() ?? '')),
                        DataCell(Text(tx['amount']?.toString() ?? '')),
                        DataCell(
                          InkWell(
                            onTap: () {
                              showDialog(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('Comment'),
                                  content: SingleChildScrollView(
                                    child: Text(tx['comment']?.toString() ?? ''),
                                  ),
                                  actions: [
                                    TextButton(
                                      onPressed: () => Navigator.of(ctx).pop(),
                                      child: const Text('Close'),
                                    ),
                                  ],
                                ),
                              );
                            },
                            child: SizedBox(
                              width: 120, // Control width of the comment column
                              child: Text(
                                tx['comment']?.toString() ?? '',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ),
                        ),
                        DataCell(Text(formatTimestamp(tx['timestamp']))),
                      ]);
                    }).toList(),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _CoordinatedScrollPhysics extends ScrollPhysics {
  final ScrollController mainController;
  
  const _CoordinatedScrollPhysics({
    required this.mainController,
    super.parent,
  });

  @override
  _CoordinatedScrollPhysics applyTo(ScrollPhysics? ancestor) {
    return _CoordinatedScrollPhysics(
      mainController: mainController,
      parent: buildParent(ancestor),
    );
  }

  @override
  double applyPhysicsToUserOffset(ScrollMetrics position, double offset) {
    // If we're at the top of the table and trying to scroll up
    if (position.pixels <= 0 && offset > 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the table
      }
    }
    // If we're at the bottom of the table and trying to scroll down
    else if (position.pixels >= position.maxScrollExtent && offset < 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the table
      }
    }
    return super.applyPhysicsToUserOffset(position, offset);
  }
}
