import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/utils/formatters.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';

class BankPage extends StatefulWidget {
  const BankPage({super.key});

  @override
  State<BankPage> createState() => _BankPageState();
}

class _BankPageState extends State<BankPage> {
  late Future<Map<String, dynamic>?> _bankFuture;
  late Future<List<Map<String, dynamic>>> _transactionsFuture;
  Map<String, dynamic>? _bankData;
  final _withdrawAmountController = TextEditingController();
  final _withdrawDescriptionController = TextEditingController();
  bool _isSubmitting = false;

  List<Map<String, dynamic>> _editableBankFields = [];
  String? _selectedBankField;
  final _adjustNewValueController = TextEditingController();
  final _adjustCommentController = TextEditingController();
  bool _isAdjusting = false;

  @override
  void initState() {
    super.initState();
    _reload();
    _loadEditableBankFields();
  }

  Future<void> _loadEditableBankFields() async {
    final fields = await PyBridge().getEditableBankFields();
    if (!mounted) return;
    setState(() {
      _editableBankFields = fields;
      if (_editableBankFields.isNotEmpty) {
        _selectedBankField = _editableBankFields.first['field'] as String?;
      }
    });
  }

  void _reload() {
    final auth = Provider.of<AuthService>(context, listen: false);
    setState(() {
      _bankFuture = PyBridge().getBank();
      _transactionsFuture = PyBridge().getBankTransaction().then(auth.filterVisibleRecords);
    });
    _bankFuture.then((data) {
      if (mounted) setState(() => _bankData = data);
    });
  }

  Future<void> _submitWithdraw() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    final salesmanId = auth.currentUserId;
    if (salesmanId == null) {
      _showDialog('Error', 'Unable to identify current user');
      return;
    }
    
    final amount = double.tryParse(_withdrawAmountController.text);
    final description = _withdrawDescriptionController.text.trim();
    if (amount == null || amount <= 0) {
      _showDialog('Error', 'Enter a valid amount');
      return;
    }
    setState(() => _isSubmitting = true);
    final error = await PyBridge().bankWithdraw(amount: amount, description: description, salesmanId: salesmanId);
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

  Future<void> _submitBankFieldAdjustment() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    final salesmanId = auth.currentUserId;
    if (salesmanId == null) {
      _showDialog('Error', 'Unable to identify current user');
      return;
    }
    final field = _selectedBankField;
    if (field == null) {
      _showDialog('Error', 'Select a field to edit');
      return;
    }
    final newValue = double.tryParse(_adjustNewValueController.text);
    if (newValue == null) {
      _showDialog('Error', 'Enter a valid number');
      return;
    }
    final comment = _adjustCommentController.text.trim();
    if (comment.isEmpty) {
      _showDialog('Error', 'Please enter a comment explaining this adjustment');
      return;
    }
    setState(() => _isAdjusting = true);
    final error = await PyBridge().adjustBankField(
      field: field,
      newValue: newValue,
      comment: comment,
      salesmanId: salesmanId,
    );
    setState(() => _isAdjusting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'Bank field updated!');
      _adjustNewValueController.clear();
      _adjustCommentController.clear();
      _reload();
    }
  }

  @override
  void dispose() {
    _withdrawAmountController.dispose();
    _withdrawDescriptionController.dispose();
    _adjustNewValueController.dispose();
    _adjustCommentController.dispose();
    super.dispose();
  }

  Widget _buildBankBarChart(Map<String, dynamic> bank) {
    final double coveredCosts = (bank['break_even_covered_costs'] ?? 0).toDouble();
    final double remainingCosts = (bank['break_even_remaining'] ?? 0).toDouble();
    final double breakEvenSurplus = (bank['break_even_surplus'] ?? 0).toDouble();
    final double costsTotal = (bank['costs_total'] ?? 0).toDouble();
    final double revenueTotal = (bank['revenue_total'] ?? 0).toDouble();
    final double chartMax = [costsTotal, revenueTotal, coveredCosts + remainingCosts, coveredCosts + breakEvenSurplus]
            .reduce((a, b) => a > b ? a : b) *
        1.2 +
        1;

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
                maxY: chartMax,
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
                            return const Text('Costs');
                          case 1:
                            return const Text('Revenue');
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
                        toY: coveredCosts + remainingCosts,
                        rodStackItems: [
                          BarChartRodStackItem(0, coveredCosts, Colors.green),
                          BarChartRodStackItem(coveredCosts, coveredCosts + remainingCosts, Colors.redAccent),
                        ],
                        width: 32,
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ],
                  ),
                  BarChartGroupData(
                    x: 1,
                    barRods: [
                      BarChartRodData(
                        toY: coveredCosts + breakEvenSurplus,
                        rodStackItems: [
                          if (coveredCosts > 0)
                            BarChartRodStackItem(0, coveredCosts, Colors.blue),
                          if (breakEvenSurplus > 0)
                            BarChartRodStackItem(coveredCosts, coveredCosts + breakEvenSurplus, Colors.amber),
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
      _summaryTile('Business Balance', bank['business_balance'], Colors.deepPurple),
      _summaryTile('Break-Even Left', bank['break_even_remaining'], Colors.redAccent),
      _summaryTile('Surplus', bank['break_even_surplus'], Colors.green),
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
            Text(formatMoney(value, fallback: '-'), style: TextStyle(fontSize: 15, color: color)),
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
        Text(formatMoney(value, fallback: '-'), style: TextStyle(fontSize: 15, color: color)),
      ],
    );
  }


  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
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
                            Text(
                              (bank['break_even_reached'] ?? false)
                                  ? 'Break-even reached'
                                  : 'Break-even progress: ${(((bank['break_even_progress'] ?? 0) as num) * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 8),
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  _legendDot(Colors.green, 'Costs Covered'),
                                  const SizedBox(width: 12),
                                  _legendDot(Colors.redAccent, 'Still To Cover'),
                                  const SizedBox(width: 12),
                                  _legendDot(Colors.blue, 'Revenue Applied'),
                                  const SizedBox(width: 12),
                                  _legendDot(Colors.amber, 'Surplus After Break-Even'),
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
                    if (auth.hasAdminRights) ...[
                      const Text('Adjust Bank Field', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      const Text(
                        'Directly correct a source-of-truth value (e.g. after a bookkeeping mistake). '
                        'Derived figures (profit, business balance, break-even) are recalculated automatically.',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                      const SizedBox(height: 8),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            SizedBox(
                              width: 180,
                              child: DropdownButtonFormField<String>(
                                value: _selectedBankField,
                                decoration: const InputDecoration(labelText: 'Field'),
                                items: _editableBankFields
                                    .map((f) => DropdownMenuItem<String>(
                                          value: f['field'] as String,
                                          child: Text(f['label']?.toString() ?? f['field'].toString()),
                                        ))
                                    .toList(),
                                onChanged: (val) {
                                  setState(() {
                                    _selectedBankField = val;
                                    final current = val != null ? (_bankData?[val]) : null;
                                    _adjustNewValueController.text = current != null ? formatMoney(current) : '';
                                  });
                                },
                              ),
                            ),
                            const SizedBox(width: 12),
                            SizedBox(
                              width: 140,
                              child: TextField(
                                controller: _adjustNewValueController,
                                keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                                decoration: const InputDecoration(labelText: 'New Value'),
                              ),
                            ),
                            const SizedBox(width: 12),
                            SizedBox(
                              width: 220,
                              child: TextField(
                                controller: _adjustCommentController,
                                decoration: const InputDecoration(labelText: 'Comment (required)'),
                              ),
                            ),
                            const SizedBox(width: 12),
                            ElevatedButton(
                              onPressed: _isAdjusting ? null : _submitBankFieldAdjustment,
                              child: _isAdjusting
                                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                                  : const Text('Save'),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 32),
                    ],
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
                                DataColumn(label: Text('Salesman')),
                                DataColumn(label: Text('Date')),
                              ],
                              rows: txs.map((tx) {
                                // Extract salesman name
                                String salesman = '';
                                final salesmanField = tx['salesman'];
                                if (salesmanField is Map && salesmanField['name'] != null) {
                                  salesman = salesmanField['name'].toString();
                                } else if (salesmanField != null) {
                                  salesman = salesmanField.toString();
                                }
                                
                                return DataRow(cells: [
                                  DataCell(Text(tx['type']?.toString() ?? '')),
                                  DataCell(Text(formatMoney(tx['amount']))),
                                  DataCell(
                                    InkWell(
                                      onTap: () {
                                        showDialog(
                                          context: context,
                                          builder: (ctx) => AlertDialog(
                                            title: const Text('Description'),
                                            content: SingleChildScrollView(
                                              child: Text(tx['description']?.toString() ?? ''),
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
                                      child: Text(
                                        tx['description']?.toString() ?? '',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ),
                                  DataCell(Text(salesman)),
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
            );
          },
        ),
      ),
    );
  }

}
