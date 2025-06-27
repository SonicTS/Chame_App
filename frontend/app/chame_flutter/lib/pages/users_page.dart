import 'package:chame_flutter/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
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
  final _nameController = TextEditingController();
  final _balanceController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  String _role = 'User';
  bool _isSubmitting = false;
  final Map<int, TextEditingController> _depositControllers = {};
  final Map<int, TextEditingController> _withdrawControllers = {};
  String _txUserFilter = 'all';
  String _txTypeFilter = 'all';
  String _userTableNameFilter = '';
  // Add scroll controllers for users and transactions tables
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

  Future<void> _addUser() async {
    if (_nameController.text.trim().isEmpty || _balanceController.text.isEmpty) return;
    if (_role.isEmpty) {
      _showDialog('Error', 'Please select a role!');
      return;
    }
    if (_role == 'Wirt' && (_passwordController.text.isEmpty || _confirmPasswordController.text.isEmpty || _passwordController.text.length < 4)) {
      _showDialog('Error', 'Password must be at least 4 characters long!');
      return;
    }
    if (_role == 'Admin' && (_passwordController.text.isEmpty || _confirmPasswordController.text.isEmpty || _passwordController.text.length < 8)) {
      _showDialog('Error', 'Password must be at least 8 characters long!');
      return;
    }
    if (_passwordController.text != _confirmPasswordController.text) {
      _showDialog('Error', 'Passwords do not match!');
      return;
    }
    setState(() => _isSubmitting = true);
    final error = await PyBridge().addUser(
      name: _nameController.text.trim(),
      balance: double.parse(_balanceController.text),
      role: _role,
      password: _role == 'Wirt' || _role == 'Admin' ? _passwordController.text : null,
    );
    setState(() => _isSubmitting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'User added successfully!');
      _nameController.clear();
      _balanceController.clear();
      _passwordController.clear();
      _confirmPasswordController.clear();
      setState(() => _role = 'User');
      _reload();
    }
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
    _nameController.dispose();
    _balanceController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    for (final c in _depositControllers.values) {
      c.dispose();
    }
    for (final c in _withdrawControllers.values) {
      c.dispose();
    }
    // Dispose scroll controllers
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
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
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
                ),
                const SizedBox(height: 24),
                // --- USER ADD / FILTER CONTROLS ---
                if (auth.role == 'admin') ...[
                  Row(
                    children: [
                      SizedBox(
                        width: 120,
                        child: TextField(
                          controller: _nameController,
                          decoration: const InputDecoration(labelText: 'User Name'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      SizedBox(
                        width: 90,
                        child: TextField(
                          controller: _balanceController,
                          keyboardType: TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(labelText: 'Balance'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      DropdownButton<String>(
                        value: _role,
                        items: const [
                          DropdownMenuItem(value: 'User', child: Text('User')),
                          DropdownMenuItem(value: 'Admin', child: Text('Admin')),
                          DropdownMenuItem(value: 'Wirt', child: Text('Wirt')),
                        ],
                        onChanged: (val) => setState(() => _role = val!),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      if (_role == 'Wirt' || _role == 'Admin') ...[
                        SizedBox(
                          width: 100,
                          child: TextField(
                            controller: _passwordController,
                            decoration: const InputDecoration(labelText: 'Password'),
                            obscureText: true,
                            enabled: _role == 'Wirt' || _role == 'Admin',
                          ),
                        ),
                        const SizedBox(width: 12),
                        SizedBox(
                          width: 100,
                          child: TextField(
                            controller: _confirmPasswordController,
                            decoration: const InputDecoration(labelText: 'Confirm Password'),
                            obscureText: true,
                            enabled: _role == 'Wirt' || _role == 'Admin',
                          ),
                        ),
                      ],
                      const SizedBox(width: 12),
                      ElevatedButton(
                        onPressed: _isSubmitting ? null : _addUser,
                        child: _isSubmitting
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Text('Add User'),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 32),
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
  });

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
                // minimum width for horizontal scroll; adjust as needed
                width: 700,                  child: Scrollbar(
                    thumbVisibility: true,
                    controller: verticalScrollController,
                    child: SingleChildScrollView(
                      controller: verticalScrollController,
                      scrollDirection: Axis.vertical,
                      child: DataTable(
                      columns: const [
                        DataColumn(label: Text('Name')),
                        DataColumn(label: Text('Balance')),
                        DataColumn(label: Text('Role')),
                        DataColumn(label: Text('Deposit')),
                        DataColumn(label: Text('Withdraw')),
                      ],
                      rows: filteredUsers.map((user) {
                        final userId = user['user_id'] as int;
                        depositControllers.putIfAbsent(userId, () => TextEditingController());
                        withdrawControllers.putIfAbsent(userId, () => TextEditingController());
                        return DataRow(cells: [
                          DataCell(Text(user['name']?.toString() ?? '')),
                          DataCell(Text(user['balance']?.toString() ?? '')),
                          DataCell(Text(user['role']?.toString() ?? '')),
                          DataCell(Row(
                            children: [
                              SizedBox(
                                width: 70,
                                child: TextField(
                                  controller: depositControllers[userId],
                                  keyboardType: TextInputType.numberWithOptions(decimal: true),
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
                                  keyboardType: TextInputType.numberWithOptions(decimal: true),
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

  const TransactionsSection({
    super.key,
    required this.transactionsFuture,
    required this.tableHeight,
    required this.formatTimestamp,
    required this.scrollController,
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
