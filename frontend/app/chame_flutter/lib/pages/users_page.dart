import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';

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
  String _role = 'User';
  bool _isSubmitting = false;
  final Map<int, TextEditingController> _depositControllers = {};
  final Map<int, TextEditingController> _withdrawControllers = {};
  String _txUserFilter = 'all';
  String _txTypeFilter = 'all';
  String _userTableNameFilter = '';

  @override
  void initState() {
    super.initState();
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
    setState(() => _isSubmitting = true);
    final error = await PyBridge().addUser(
      name: _nameController.text.trim(),
      balance: double.parse(_balanceController.text),
      role: _role,
    );
    setState(() => _isSubmitting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'User added successfully!');
      _nameController.clear();
      _balanceController.clear();
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
    for (final c in _depositControllers.values) {
      c.dispose();
    }
    for (final c in _withdrawControllers.values) {
      c.dispose();
    }
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
    return Scaffold(
      appBar: AppBar(title: const Text('Users')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FutureBuilder<List<Map<String, dynamic>>>(
                future: _usersFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final users = snapshot.data ?? [];
                  final filteredUsers = _userTableNameFilter.isEmpty
                      ? users
                      : users.where((u) => (u['name'] ?? '').toLowerCase().contains(_userTableNameFilter)).toList();
                  return SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('Name')),
                        DataColumn(label: Text('Balance')),
                        DataColumn(label: Text('Role')),
                        DataColumn(label: Text('Deposit')),
                        DataColumn(label: Text('Withdraw')),
                      ],
                      rows: [
                        ...filteredUsers.map((user) {
                          final userId = user['user_id'] as int;
                          _depositControllers.putIfAbsent(userId, () => TextEditingController());
                          _withdrawControllers.putIfAbsent(userId, () => TextEditingController());
                          return DataRow(cells: [
                            DataCell(Text(user['name']?.toString() ?? '')),
                            DataCell(Text(user['balance']?.toString() ?? '')),
                            DataCell(Text(user['role']?.toString() ?? '')),
                            DataCell(Row(
                              children: [
                                SizedBox(
                                  width: 70,
                                  child: TextField(
                                    controller: _depositControllers[userId],
                                    keyboardType: TextInputType.numberWithOptions(decimal: true),
                                    decoration: const InputDecoration(hintText: 'Amount', isDense: true),
                                  ),
                                ),
                                const SizedBox(width: 4),
                                ElevatedButton(
                                  onPressed: _isSubmitting ? null : () => _deposit(userId),
                                  child: const Text('Deposit'),
                                ),
                              ],
                            )),
                            DataCell(Row(
                              children: [
                                SizedBox(
                                  width: 70,
                                  child: TextField(
                                    controller: _withdrawControllers[userId],
                                    keyboardType: TextInputType.numberWithOptions(decimal: true),
                                    decoration: const InputDecoration(hintText: 'Amount', isDense: true),
                                  ),
                                ),
                                const SizedBox(width: 4),
                                ElevatedButton(
                                  onPressed: _isSubmitting ? null : () => _withdraw(userId),
                                  child: const Text('Withdraw'),
                                ),
                              ],
                            )),
                          ]);
                        }),
                        DataRow(cells: [
                          DataCell(SizedBox(
                            width: 120,
                            child: TextField(
                              controller: _nameController,
                              decoration: const InputDecoration(labelText: 'User Name'),
                            ),
                          )),
                          DataCell(SizedBox(
                            width: 90,
                            child: TextField(
                              controller: _balanceController,
                              keyboardType: TextInputType.numberWithOptions(decimal: true),
                              decoration: const InputDecoration(labelText: 'Balance'),
                            ),
                          )),
                          DataCell(DropdownButton<String>(
                            value: _role,
                            items: const [
                              DropdownMenuItem(value: 'User', child: Text('User')),
                              DropdownMenuItem(value: 'Admin', child: Text('Admin')),
                              DropdownMenuItem(value: 'Wirt', child: Text('Wirt')),
                            ],
                            onChanged: (val) => setState(() => _role = val!),
                          )),
                          DataCell(ElevatedButton(
                            onPressed: _isSubmitting ? null : _addUser,
                            child: _isSubmitting ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Add User'),
                          )),
                          const DataCell(SizedBox()),
                        ]),
                      ],
                    ),
                  );
                },
              ),
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
              SizedBox(
                height: 300,
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _transactionsFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    final txs = snapshot.data ?? [];
                    if (txs.isEmpty) {
                      return const Text('No transactions found.');
                    }
                    return SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: DataTable(
                        columns: const [
                          DataColumn(label: Text('User')),
                          DataColumn(label: Text('Type')),
                          DataColumn(label: Text('Amount')),
                          DataColumn(label: Text('Date')),
                        ],
                        rows: txs.map((tx) {
                          return DataRow(cells: [
                            DataCell(Text(tx['user']?['name'].toString() ?? '')),
                            DataCell(Text(tx['type']?.toString() ?? '')),
                            DataCell(Text(tx['amount']?.toString() ?? '')),
                            DataCell(Text(_formatTimestamp(tx['timestamp']))),
                          ]);
                        }).toList(),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
