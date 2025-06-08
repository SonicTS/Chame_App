import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';

class BankPage extends StatefulWidget {
  const BankPage({super.key});

  @override
  State<BankPage> createState() => _BankPageState();
}

class _BankPageState extends State<BankPage> {
  late Future<Map<String, dynamic>?> _bankFuture;
  late Future<List<Map<String, dynamic>>> _transactionsFuture;
  final _withdrawAmountController = TextEditingController();
  final _withdrawDescriptionController = TextEditingController();
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    setState(() {
      _bankFuture = PyBridge().getBank();
      _transactionsFuture = PyBridge().getBankTransaction();
    });
  }

  Future<void> _submitWithdraw() async {
    final amount = double.tryParse(_withdrawAmountController.text);
    final description = _withdrawDescriptionController.text.trim();
    if (amount == null || amount <= 0) {
      _showDialog('Error', 'Enter a valid amount');
      return;
    }
    setState(() => _isSubmitting = true);
    final error = await PyBridge().bankWithdraw(amount: amount, description: description);
    setState(() => _isSubmitting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'Withdrawal successful!');
      _withdrawAmountController.clear();
      _withdrawDescriptionController.clear();
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
    _withdrawAmountController.dispose();
    _withdrawDescriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bank Entry')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FutureBuilder<Map<String, dynamic>?>(
                future: _bankFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final bank = snapshot.data;
                  if (bank == null) {
                    return const Text('No bank data available.');
                  }
                  return SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('Total Balance')),
                        DataColumn(label: Text('Available Balance')),
                        DataColumn(label: Text('Ingredient Value')),
                        DataColumn(label: Text('Restocking Cost')),
                        DataColumn(label: Text('Profit Balance')),
                      ],
                      rows: [
                        DataRow(cells: [
                          DataCell(Text(bank['total_balance']?.toString() ?? '')),
                          DataCell(Text(bank['available_balance']?.toString() ?? '')),
                          DataCell(Text(bank['ingredient_value']?.toString() ?? '')),
                          DataCell(Text(bank['restocking_cost']?.toString() ?? '')),
                          DataCell(Text(bank['profit_balance']?.toString() ?? '')),
                        ]),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(height: 24),
              const Text('Withdraw Money', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    SizedBox(
                      width: 120,
                      child: TextField(
                        controller: _withdrawAmountController,
                        keyboardType: TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Amount'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 200,
                      child: TextField(
                        controller: _withdrawDescriptionController,
                        decoration: const InputDecoration(labelText: 'Description (optional)'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    ElevatedButton(
                      onPressed: _isSubmitting ? null : _submitWithdraw,
                      child: _isSubmitting
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Text('Withdraw'),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              const Text('Bank Transactions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
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
                          DataColumn(label: Text('Type')),
                          DataColumn(label: Text('Amount')),
                          DataColumn(label: Text('Description')),
                          DataColumn(label: Text('Date')),
                        ],
                        rows: txs.map((tx) {
                          return DataRow(cells: [
                            DataCell(Text(tx['type']?.toString() ?? '')),
                            DataCell(Text(tx['amount']?.toString() ?? '')),
                            DataCell(Text(tx['description']?.toString() ?? '')),
                            DataCell(Text(tx['timestamp']?.toString() ?? '')),
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
