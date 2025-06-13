import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';

class ToastRoundPage extends StatefulWidget {
  const ToastRoundPage({super.key});

  @override
  State<ToastRoundPage> createState() => _ToastRoundPageState();
}

class _ToastRoundPageState extends State<ToastRoundPage> {
  /// Marks every follower slot of a multi-slot product.
  static const int _OCCUPIED = -1;

  late Future<List<Map<String, dynamic>>> _usersFuture;
  late Future<List<Map<String, dynamic>>> _productsFuture;
  late Future<List<Map<String, dynamic>>> _toastRoundsFuture;

  final _selectedUserIds    = List<int?>.filled(6, null);
  final _selectedProductIds = List<int?>.filled(6, null);

  bool _isSubmitting = false;
  int? _globalUserId;
  int? _globalProductId;

  // ────────────────────────── lifecycle ──────────────────────────
  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    setState(() {
      _usersFuture       = PyBridge().getAllUsers();
      _productsFuture    = PyBridge().getAllToastProducts();
      _toastRoundsFuture = PyBridge().getAllToastRounds();
      for (var i = 0; i < 6; i++) {
        _selectedUserIds[i]    = null;
        _selectedProductIds[i] = null;
      }
    });
  }

  // ────────────────────────── helpers ──────────────────────────
  int _getToasterSpace(int? productId, List<Map<String, dynamic>> products) {
    if (productId == null || productId == _OCCUPIED) return 1;
    final prod = products.firstWhereOrNull((p) => p['product_id'] == productId);
    return (prod?['toaster_space'] as int?) ?? 1;
  }

  bool _isOccupiedSlot(int? productId) => productId == _OCCUPIED;

  // ────────────────────────── global fill ──────────────────────────
  void _applyGlobalProductSelection(int? productId, List<Map<String, dynamic>> products) {
    setState(() {
      _globalProductId = productId;

      // Clear all product and user fields first
      
      if (productId == null) return;
      for (var i = 0; i < 6; i++) {
        _selectedProductIds[i] = null;
      }
      int idx = 0;
      while (idx < 6) {
        final len = _getToasterSpace(productId, products);
        if (idx + len > 6) break;
        _selectedProductIds[idx] = productId;
        if(_selectedUserIds[idx] == null && _globalUserId != null) {
          _selectedUserIds[idx] = _globalUserId; // Set global user if not already set
        } 
        for (var k = 1; k < len; k++) {
          _selectedProductIds[idx + k] = _OCCUPIED;
          _selectedUserIds[idx + k] = null;
        }
        idx += len;
      }
    });
  }

  void _applyGlobalUserSelection(int? userId) {
  setState(() {
    _globalUserId = userId;

    for (var i = 0; i < 6; i++) {
      if (!_isOccupiedSlot(_selectedProductIds[i])) {
        _selectedUserIds[i] = userId;
      }
    }
  });
}


  // ────────────────────────── submission ──────────────────────────
  Future<void> _submit() async {
    final uidOut = <int>[];
    final pidOut = <int>[];

    for (var i = 0; i < 6; i++) {
      final pid = _selectedProductIds[i];
      final uid = _selectedUserIds[i];
      if (pid != null && pid != _OCCUPIED && uid != null) {
        uidOut.add(uid);
        pidOut.add(pid);
      }
    }

    if (uidOut.isEmpty || uidOut.length != pidOut.length) {
      _showDialog('Error', 'Please select a user and product for each row.');
      return;
    }

    setState(() => _isSubmitting = true);
    final err = await PyBridge().addToastRound(
      productIds: pidOut,
      userSelections: uidOut,
    );
    setState(() => _isSubmitting = false);

    err == null
        ? _showDialog('Success', 'Toast round submitted!')
        : _showDialog('Error', err);
    if (err == null) _reload();
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

  // ────────────────────────── build ──────────────────────────
  @override
Widget build(BuildContext context) {
  return Scaffold(
    appBar: AppBar(title: const Text('Toast Round')),
    body: SafeArea(
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            padding: const EdgeInsets.all(16),
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: constraints.maxHeight),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Toast Round', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
                  FutureBuilder<List<Map<String, dynamic>>>(
                    future: _usersFuture,
                    builder: (ctx, userSnap) {
                      if (userSnap.connectionState == ConnectionState.waiting)
                        return const Center(child: CircularProgressIndicator());
                      final users = userSnap.data ?? [];

                      return FutureBuilder<List<Map<String, dynamic>>>(
                        future: _productsFuture,
                        builder: (ctx, prodSnap) {
                          if (prodSnap.connectionState == ConnectionState.waiting)
                            return const Center(child: CircularProgressIndicator());
                          final products = prodSnap.data ?? [];

                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              // ── global selectors ──
                              Row(
                                children: [
                                  SizedBox(
                                    width: 180,
                                    child: _dropdownUser(
                                      label: 'Global User',
                                      users: users,
                                      selectedId: _globalUserId,
                                      onChanged: (id) => _applyGlobalUserSelection(id),
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  SizedBox(
                                    width: 180,
                                    child: _dropdownProduct(
                                      label: 'Global Product',
                                      products: products,
                                      selectedId: _globalProductId,
                                      onChanged: (id) => _applyGlobalProductSelection(id, products),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),

                              // ── 6 editable rows ──
                              ...List.generate(6, (i) {
                                final occupied = _isOccupiedSlot(_selectedProductIds[i]);
                                return SingleChildScrollView(
                                  scrollDirection: Axis.horizontal,
                                  child: Row(
                                    children: [
                                      const Text('User:'), const SizedBox(width: 8),
                                      SizedBox(
                                        width: 160,
                                        child: occupied
                                            ? _occupiedLabel()
                                            : _dropdownUser(
                                                label: 'User',
                                                users: users,
                                                selectedId: _selectedUserIds[i],
                                                onChanged: (id) => setState(() => _selectedUserIds[i] = id),
                                              ),
                                      ),
                                      const SizedBox(width: 16),
                                      const Text('Product:'), const SizedBox(width: 8),
                                      SizedBox(
                                        width: 160,
                                        child: occupied
                                            ? _occupiedLabel()
                                            : _dropdownProduct(
                                                label: 'Product',
                                                products: products,
                                                selectedId: _selectedProductIds[i],
                                                onChanged: (newPid) {
                                                  setState(() {
                                                    // 1. Update the product selection for this row
                                                    _selectedProductIds[i] = newPid;
                                                    // 2. Clear all OCCUPIED slots and user assignments
                                                    for (var j = 0; j < 6; j++) {
                                                      if (_selectedProductIds[j] == _OCCUPIED) _selectedProductIds[j] = null;
                                                      if (_selectedUserIds[j] == null || _isOccupiedSlot(_selectedProductIds[j])) _selectedUserIds[j] = null;
                                                    }
                                                    // 3. Re-apply all product blocks in order
                                                    int idx = 0;
                                                    while (idx < 6) {
                                                      final pid = _selectedProductIds[idx];
                                                      if (pid != null && pid != _OCCUPIED) {
                                                        final len = _getToasterSpace(pid, products);
                                                        // If not enough space, clear this selection
                                                        if (idx + len > 6) {
                                                          _selectedProductIds[idx] = null;
                                                          _selectedUserIds[idx] = null;
                                                          idx++;
                                                          continue;
                                                        }
                                                        // Mark followers as OCCUPIED
                                                        for (var k = 1; k < len; k++) {
                                                          _selectedProductIds[idx + k] = _OCCUPIED;
                                                          _selectedUserIds[idx + k] = null;
                                                        }
                                                        idx += len;
                                                      } else {
                                                        idx++;
                                                      }
                                                    }
                                                  });
                                                },
                                              ),
                                      ),
                                    ],
                                  ),
                                );
                              }),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: _isSubmitting ? null : _submit,
                                child: _isSubmitting
                                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                                    : const Text('Submit'),
                              ),
                              const SizedBox(height: 24),

                              // ── history table ──
                              const Text('Toast Round History', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                              SizedBox(
                                height: 300,
                                child: FutureBuilder<List<Map<String, dynamic>>>(
                                  future: _toastRoundsFuture,
                                  builder: (ctx, snap) {
                                    if (snap.connectionState == ConnectionState.waiting)
                                      return const Center(child: CircularProgressIndicator());
                                    final rounds = snap.data ?? [];
                                    if (rounds.isEmpty) return const Text('No toast rounds found.');
                                    return SingleChildScrollView(
                                      scrollDirection: Axis.horizontal,
                                      child: DataTable(
                                        columns: const [
                                          DataColumn(label: Text('Toast-Consumer')),
                                          DataColumn(label: Text('Time')),
                                        ],
                                        rows: rounds.map((round) {
                                          final sales = (round['sales'] as List?) ?? [];
                                          final summary = sales.map((s) {
                                            // Debug: show raw structure if missing
                                            final userField = s['user'];
                                            final productField = s['product'];
                                            final user = userField is Map && userField['name'] != null ? userField['name'] : userField?.toString() ?? '';
                                            final product = productField is Map && productField['name'] != null ? productField['name'] : productField?.toString() ?? '';
                                            return '[$user: $product]';
                                          }).join(', ');
                                          return DataRow(cells: [
                                            DataCell(Text(summary)),
                                            DataCell(Text(round['date_time']?.toString() ?? '')),
                                          ]);
                                        }).toList(),
                                      ),
                                    );
                                  },
                                ),
                              ),
                            ],
                          );
                        },
                      );
                    },
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


  // ────────────────────────── tiny widget helpers ──────────────────────────
  Widget _occupiedLabel() =>
      Text('Occupied', style: TextStyle(color: Colors.grey[600], fontStyle: FontStyle.italic));

  Widget _dropdownUser({
    required String label,
    required List<Map<String, dynamic>> users,
    required int? selectedId,
    required ValueChanged<int?> onChanged,
  }) =>
      DropdownSearch<Map<String, dynamic>>(
        items: (String? filter, _) => filter == null || filter.isEmpty
            ? users
            : users
                .where((u) => (u['name'] ?? '').toLowerCase().contains(filter.toLowerCase()))
                .toList(),
        selectedItem: users.firstWhereOrNull((u) => u['user_id'] == selectedId),
        itemAsString: (u) => u['name'] ?? '',
        compareFn: (a, b) => a['user_id'] == b['user_id'],
        onChanged: (val) => onChanged(val?['user_id'] as int?),
        popupProps: const PopupProps.menu(showSearchBox: true),
        decoratorProps: DropDownDecoratorProps(
          decoration: InputDecoration(labelText: label),
        ),
      );

  Widget _dropdownProduct({
    required String label,
    required List<Map<String, dynamic>> products,
    required int? selectedId,
    required ValueChanged<int?> onChanged,
  }) =>
      DropdownSearch<Map<String, dynamic>>(
        items: (String? filter, _) => filter == null || filter.isEmpty
            ? products
            : products
                .where((p) => (p['name'] ?? '').toLowerCase().contains(filter.toLowerCase()))
                .toList(),
        selectedItem: products.firstWhereOrNull((p) => p['product_id'] == selectedId),
        itemAsString: (p) => p['name'] ?? '',
        compareFn: (a, b) => a['product_id'] == b['product_id'],
        onChanged: (val) => onChanged(val?['product_id'] as int?),
        popupProps: const PopupProps.menu(showSearchBox: true),
        decoratorProps: DropDownDecoratorProps(
          decoration: InputDecoration(labelText: label),
        ),
      );
}
