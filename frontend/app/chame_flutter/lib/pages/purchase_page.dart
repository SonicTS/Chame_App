import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';

class PurchasePage extends StatefulWidget {
  const PurchasePage({super.key});

  @override
  State<PurchasePage> createState() => _PurchasePageState();
}

class _PurchasePageState extends State<PurchasePage> {
  late Future<List<Map<String, dynamic>>> _usersFuture;
  late Future<List<Map<String, dynamic>>> _productsFuture;
  late Future<List<Map<String, dynamic>>> _salesFuture;
  int? _selectedUserId;
  int? _selectedProductId;
  int _quantity = 1;
  bool _isSubmitting = false;
  String _salesConfig = 'all';

  @override
  void initState() {
    super.initState();
    _fetchAll();
  }

  void _fetchAll() {
    setState(() {
      _usersFuture = PyBridge().getAllUsers();
      _productsFuture = PyBridge().getAllProducts();
      _salesFuture = PyBridge().getAllSales();
    });
  }

  void _reloadSales() {
    setState(() {
      _salesFuture = PyBridge().getAllSales();
    });
  }

  Future<void> _submit() async {
    if (_selectedUserId == null || _selectedProductId == null || _quantity < 1) {
      _showDialog('Error', 'Please select user, product, and enter a valid quantity.');
      return;
    }
    setState(() => _isSubmitting = true);
    final error = await PyBridge().makePurchase(
      userId: _selectedUserId!,
      productId: _selectedProductId!,
      quantity: _quantity,
    );
    setState(() => _isSubmitting = false);
    if (error != null) {
      _showDialog('Error', error);
    } else {
      _showDialog('Success', 'Purchase successful!');
      _reloadSales();
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

  String _formatTimestamp(dynamic ts) {
    if (ts == null) return '';
    if (ts is DateTime) return ts.toString();
    if (ts is String) return ts;
    // If it's a Firestore timestamp, try toString
    return ts.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Purchase')),
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
                    const Text('Purchase Form', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
                    FutureBuilder<List<Map<String, dynamic>>>(
                      future: _usersFuture,
                      builder: (context, userSnap) {
                        if (userSnap.connectionState == ConnectionState.waiting) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        final users = userSnap.data ?? [];
                        return FutureBuilder<List<Map<String, dynamic>>>(
                          future: _productsFuture,
                          builder: (context, prodSnap) {
                            if (prodSnap.connectionState == ConnectionState.waiting) {
                              return const Center(child: CircularProgressIndicator());
                            }
                            final products = prodSnap.data ?? [];
                            return Form(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  DropdownSearch<Map<String, dynamic>>(
                                    items: (String? filter, _) {
                                      final filtered = filter == null || filter.isEmpty
                                          ? users
                                          : users.where((u) => (u['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
                                      return Future.value(filtered);
                                    },
                                    selectedItem: users.firstWhereOrNull((u) => u['user_id'] == _selectedUserId),
                                    itemAsString: (u) => u['name'] ?? '',
                                    compareFn: (a, b) => a['user_id'] == b['user_id'],
                                    onChanged: (val) => setState(() => _selectedUserId = val?['user_id'] as int?),
                                    popupProps: const PopupProps.menu(
                                      showSearchBox: true,
                                    ),
                                    decoratorProps: const DropDownDecoratorProps(
                                      decoration: InputDecoration(labelText: 'Select User'),
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  DropdownSearch<Map<String, dynamic>>(
                                    items: (String? filter, _) {
                                      final filtered = filter == null || filter.isEmpty
                                          ? products
                                          : products.where((p) => (p['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
                                      return Future.value(filtered);
                                    },
                                    selectedItem: products.firstWhereOrNull((p) => p['product_id'] == _selectedProductId),
                                    itemAsString: (p) => p['name'] ?? '',
                                    compareFn: (a, b) => a['product_id'] == b['product_id'],
                                    onChanged: (val) => setState(() => _selectedProductId = val?['product_id'] as int?),
                                    popupProps: const PopupProps.menu(
                                      showSearchBox: true,
                                    ),
                                    decoratorProps: const DropDownDecoratorProps(
                                      decoration: InputDecoration(labelText: 'Select Product'),
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  SizedBox(
                                    width: 120,
                                    child: TextFormField(
                                      initialValue: '1',
                                      keyboardType: TextInputType.number,
                                      decoration: const InputDecoration(labelText: 'Quantity'),
                                      onChanged: (v) => _quantity = int.tryParse(v) ?? 1,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  ElevatedButton(
                                    onPressed: _isSubmitting ? null : _submit,
                                    child: _isSubmitting
                                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                                        : const Text('Submit'),
                                  ),
                                ],
                              ),
                            );
                          },
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                    Row(
                      children: [
                        const Text('Configure Sales Table:', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(width: 12),
                        DropdownButton<String>(
                          value: _salesConfig,
                          items: const [
                            DropdownMenuItem(value: 'all', child: Text('All')),
                            DropdownMenuItem(value: 'raw', child: Text('Raw')),
                            DropdownMenuItem(value: 'toast', child: Text('Toast')),
                          ],
                          onChanged: (val) {
                            setState(() {
                              _salesConfig = val!;
                            });
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Text('Sales', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                    SizedBox(
                      height: 300,
                      child: FutureBuilder<List<Map<String, dynamic>>>(
                        future: _salesFuture,
                        builder: (context, snapshot) {
                          if (snapshot.connectionState == ConnectionState.waiting) {
                            return const Center(child: CircularProgressIndicator());
                          }
                          final sales = snapshot.data ?? [];
                          final filteredSales = _salesConfig == 'all'
                              ? sales
                              : sales.where((s) => s['product']?['category'] == _salesConfig).toList();
                          if (filteredSales.isEmpty) {
                            return const Text('No sales found.');
                          }
                          return SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: DataTable(
                              columns: const [
                                DataColumn(label: Text('Sale ID')),
                                DataColumn(label: Text('User')),
                                DataColumn(label: Text('Product')),
                                DataColumn(label: Text('Quantity')),
                                DataColumn(label: Text('Total Price')),
                                DataColumn(label: Text('Timestamp')),
                              ],
                              rows: filteredSales.map((sale) {
                                return DataRow(cells: [
                                  DataCell(Text(sale['sale_id']?.toString() ?? '')),
                                  DataCell(Text(sale['user']?['name']?.toString() ?? '')),
                                  DataCell(Text(sale['product']?['name']?.toString() ?? '')),
                                  DataCell(Text(sale['quantity']?.toString() ?? '')),
                                  DataCell(Text(sale['total_price']?.toString() ?? '')),
                                  DataCell(Text(_formatTimestamp(sale['timestamp']))),
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
