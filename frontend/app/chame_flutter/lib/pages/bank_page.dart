import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:fl_chart/fl_chart.dart';

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

  Widget _buildBankBarChart(Map<String, dynamic> bank) {
    final double userFunds = (bank['customer_funds'] ?? 0).toDouble();
    final double revenueFunds = (bank['revenue_funds'] ?? 0).toDouble();
    final double costsReserved = (bank['costs_reserved'] ?? 0).toDouble();
    final double profitRetained = (bank['profit_retained'] ?? 0).toDouble();

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: SizedBox(
        height: 220,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: 360,
            child: BarChart(
              BarChartData(
                alignment: BarChartAlignment.spaceAround,
                maxY: [userFunds, revenueFunds].reduce((a, b) => a > b ? a : b) * 1.2 + 1,
                barTouchData: BarTouchData(enabled: false),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: true, reservedSize: 40),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        switch (value.toInt()) {
                          case 0:
                            return const Text('User Funds');
                          case 1:
                            return const Text('Revenue Funds');
                          default:
                            return const SizedBox.shrink();
                        }
                      },
                    ),
                  ),
                  rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: false),
                barGroups: [
                  BarChartGroupData(
                    x: 0,
                    barRods: [
                      BarChartRodData(
                        toY: userFunds,
                        color: Colors.blue,
                        width: 32,
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ],
                  ),
                  BarChartGroupData(
                    x: 1,
                    barRods: [
                      BarChartRodData(
                        toY: costsReserved + profitRetained,
                        rodStackItems: [
                          BarChartRodStackItem(0, costsReserved, Colors.redAccent),
                          BarChartRodStackItem(costsReserved, costsReserved + profitRetained, Colors.green),
                        ],
                        width: 32,
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }


  Widget _buildBankStats(Map<String, dynamic> bank) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12.0),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            _statCard('Total Revenue', bank['revenue_total']),
            const SizedBox(width: 12),
            _statCard('Total Costs', bank['costs_total']),
            const SizedBox(width: 12),
            _statCard('Total Profit', bank['profit_total']),
            const SizedBox(width: 12),
            _statCard('Ingredient Value', bank['ingredient_value'], color: Colors.orange),
          ],
        ),
      ),
    );
  }


  Widget _buildBankSummary(Map<String, dynamic> bank) {
    final summaryItems = [
      _summaryTile('Total Balance', bank['total_balance'], Colors.black),
      _summaryTile('User Funds', bank['customer_funds'], Colors.blue),
      _summaryTile('Revenue Funds', bank['revenue_funds'], Colors.deepPurple),
      _summaryTile('Costs Reserved', bank['costs_reserved'], Colors.redAccent),
      _summaryTile('Profit Retained', bank['profit_retained'], Colors.green),
    ];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            ...summaryItems.map((tile) => Padding(
                  padding: const EdgeInsets.only(right: 12.0),
                  child: Card(child: Padding(padding: const EdgeInsets.all(8.0), child: tile)),
                )),
          ],
        ),
      ),
    );
  }


  Widget _statCard(String label, dynamic value, {Color? color}) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(label, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 13)),
            const SizedBox(height: 4),
            Text(value?.toString() ?? '-', style: TextStyle(fontSize: 15, color: color)),
          ],
        ),
      ),
    );
  }


  Widget _legendDot(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 14, height: 14, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Text(label),
      ],
    );
  }


  Widget _summaryTile(String label, dynamic value, Color color) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(label, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 13)),
        const SizedBox(height: 4),
        Text(value?.toString() ?? '-', style: TextStyle(fontSize: 15, color: color)),
      ],
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bank Entry')),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
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
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildBankSummary(bank),
                            _buildBankBarChart(bank),
                            const SizedBox(height: 8),
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  _legendDot(Colors.blue, 'User Funds'),
                                  const SizedBox(width: 12),
                                  _legendDot(Colors.redAccent, 'Costs Reserved'),
                                  const SizedBox(width: 12),
                                  _legendDot(Colors.green, 'Profit Retained'),
                                ],
                              ),
                            ),
                            _buildBankStats(bank),
                          ],
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                    const Text('Withdraw Money', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                    // Make the withdraw form horizontally scrollable
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
                                  DataCell(Text(tx['date']?.toString() ?? '')),
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
            );
          },
        ),
      ),
    );
  }

}
