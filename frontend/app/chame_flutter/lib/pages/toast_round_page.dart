import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';
import 'package:provider/provider.dart';

class ToastRoundPage extends StatefulWidget {
  const ToastRoundPage({super.key});

  @override
  State<ToastRoundPage> createState() => _ToastRoundPageState();
}

class _ToastRoundPageState extends State<ToastRoundPage> {
  static const int _OCCUPIED = -1;

  late Future<List<Map<String, dynamic>>> _usersFuture;
  late Future<List<Map<String, dynamic>>> _productsFuture;
  late Future<List<Map<String, dynamic>>> _toastRoundsFuture;

  final _selectedUserIds = List<int?>.filled(6, null);
  final _selectedDonatorIds = List<int?>.filled(6, null);
  final _selectedProductIds = List<int?>.filled(6, null);

  bool _isSubmitting = false;
  int? _globalUserId;
  int? _globalProductId;
  bool _showDonatorColumn = false;

  // Scroll controllers for coordinated scrolling
  late ScrollController _mainScrollController;
  late ScrollController _historyScrollController;

  @override
  void initState() {
    super.initState();
    _fetchAll();
    
    // Initialize scroll controllers
    _mainScrollController = ScrollController();
    _historyScrollController = ScrollController();
  }

  @override
  void dispose() {
    _mainScrollController.dispose();
    _historyScrollController.dispose();
    super.dispose();
  }

  void _fetchAll() {
    setState(() {
      _usersFuture = PyBridge().getAllUsers();
      _productsFuture = PyBridge().getAllToastProducts();
      _toastRoundsFuture = PyBridge().getAllToastRounds();
      for (var i = 0; i < 6; i++) {
        _selectedUserIds[i] = null;
        _selectedDonatorIds[i] = null;
        _selectedProductIds[i] = null;
      }
    });
  }

  int _getToasterSpace(int? productId, List<Map<String, dynamic>> products) {
    if (productId == null || productId == _OCCUPIED) return 1;
    final prod = products.firstWhereOrNull((p) => p['product_id'] == productId);
    return (prod?['toaster_space'] as int?) ?? 1;
  }

  bool _isOccupiedSlot(int? productId) => productId == _OCCUPIED;

  void _applyGlobalProductSelection(int? productId, List<Map<String, dynamic>> products) {
    setState(() {
      _globalProductId = productId;
      if (productId == null) return;
      for (var i = 0; i < 6; i++) {
        _selectedProductIds[i] = null;
      }
      int idx = 0;
      while (idx < 6) {
        final len = _getToasterSpace(productId, products);
        if (idx + len > 6) break;
        _selectedProductIds[idx] = productId;
        if (_selectedUserIds[idx] == null && _globalUserId != null) {
          _selectedUserIds[idx] = _globalUserId;
        }
        for (var k = 1; k < len; k++) {
          _selectedProductIds[idx + k] = _OCCUPIED;
          _selectedUserIds[idx + k] = null;
          _selectedDonatorIds[idx + k] = null;
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

  void _handleProductChange(int index, int? newPid, List<Map<String, dynamic>> products) {
    setState(() {
      _selectedProductIds[index] = newPid;
      // Clear all occupied slots
      for (var j = 0; j < 6; j++) {
        if (_selectedProductIds[j] == _OCCUPIED) _selectedProductIds[j] = null;
        if (_selectedUserIds[j] == null || _isOccupiedSlot(_selectedProductIds[j])) _selectedUserIds[j] = null;
        if (_selectedDonatorIds[j] == null || _isOccupiedSlot(_selectedProductIds[j])) _selectedDonatorIds[j] = null;
      }
      // Recalculate occupied slots based on toaster space
      int idx = 0;
      while (idx < 6) {
        final pid = _selectedProductIds[idx];
        if (pid != null && pid != _OCCUPIED) {
          final len = _getToasterSpace(pid, products);
          if (idx + len > 6) {
            _selectedProductIds[idx] = null;
            _selectedUserIds[idx] = null;
            _selectedDonatorIds[idx] = null;
            idx++;
            continue;
          }
          for (var k = 1; k < len; k++) {
            _selectedProductIds[idx + k] = _OCCUPIED;
            _selectedUserIds[idx + k] = null;
            _selectedDonatorIds[idx + k] = null;
          }
          idx += len;
        } else {
          idx++;
        }
      }
    });
  }

  Future<void> _submit() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    final salesmanId = auth.currentUserId;
    if (salesmanId == null) {
      _showDialog('Error', 'Unable to identify current user');
      return;
    }
    
    final uidOut = <int>[];
    final pidOut = <int>[];
    final donatorOut = <int?>[];

    for (var i = 0; i < 6; i++) {
      final pid = _selectedProductIds[i];
      final consumer = _selectedUserIds[i];
      final donator = _selectedDonatorIds[i];
      if (pid != null && pid != _OCCUPIED && consumer != null) {
        uidOut.add(consumer);
        pidOut.add(pid);
        donatorOut.add(donator);
      }
    }

    if (uidOut.isEmpty || uidOut.length != pidOut.length) {
      _showDialog('Error', 'Please select a consumer and product for each row.');
      return;
    }

    setState(() => _isSubmitting = true);
    final err = await PyBridge().addToastRound(
      productIds: pidOut,
      consumer_selections: uidOut,
      donator_selections: donatorOut.map((e) => e ?? 0).toList(),
      salesmanId: salesmanId,
    );
    setState(() => _isSubmitting = false);

    err == null ? _showDialog('Success', 'Toast round submitted!') : _showDialog('Error', err);
    if (err == null) _fetchAll();
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
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Toast Round')),
      body: SafeArea(
        child: SingleChildScrollView(
          controller: _mainScrollController,
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Toast Round', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
              const SizedBox(height: 16),
              Row(
                children: [
                  TextButton(
                    onPressed: () {
                      setState(() {
                        _showDonatorColumn = !_showDonatorColumn;
                      });
                    },
                    child: Text(_showDonatorColumn ? 'Hide Donator Column' : 'Show Donator Column'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
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
                          // Global controls with horizontal scrolling
                          SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: [
                                SizedBox(
                                  width: 180,
                                  child: _dropdownUser(
                                    label: 'Global Consumer',
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
                          ),
                          const SizedBox(height: 16),
                          // Toaster slots with scrollable container
                          Container(
                            height: 400,
                            child: SingleChildScrollView(
                              child: Column(
                                children: List.generate(6, (i) {
                                  final occupied = _isOccupiedSlot(_selectedProductIds[i]);
                                  return Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 4.0),
                                    child: SingleChildScrollView(
                                      scrollDirection: Axis.horizontal,
                                      child: Row(
                                        children: [
                                          const Text('Consumer:'),
                                          const SizedBox(width: 8),
                                          SizedBox(
                                            width: 160,
                                            child: occupied ? _occupiedLabel() : _dropdownUser(
                                              label: 'Consumer',
                                              users: users,
                                              selectedId: _selectedUserIds[i],
                                              onChanged: (id) => setState(() => _selectedUserIds[i] = id),
                                            ),
                                          ),
                                          if (_showDonatorColumn) ...[
                                            const SizedBox(width: 8),
                                            const Text('Donator:'),
                                            const SizedBox(width: 8),
                                            SizedBox(
                                              width: 160,
                                              child: occupied ? _occupiedLabel() : _dropdownUser(
                                                label: 'Donator',
                                                users: users,
                                                selectedId: _selectedDonatorIds[i],
                                                onChanged: (id) => setState(() => _selectedDonatorIds[i] = id),
                                              ),
                                            ),
                                          ],
                                          const SizedBox(width: 16),
                                          const Text('Product:'),
                                          const SizedBox(width: 8),
                                          SizedBox(
                                            width: 160,
                                            child: occupied ? _occupiedLabel() : _dropdownProduct(
                                              label: 'Product',
                                              products: products,
                                              selectedId: _selectedProductIds[i],
                                              onChanged: (newPid) => _handleProductChange(i, newPid, products),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                }),
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: _isSubmitting ? null : _submit,
                            child: _isSubmitting
                                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                                : const Text('Submit'),
                          ),
                          const SizedBox(height: 24),
                          const Text('Toast Round History', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                          const SizedBox(height: 12),
                          // History table with coordinated scrolling
                          _buildHistoryTable(),
                        ],
                      );
                    },
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _occupiedLabel() => Text('Occupied', style: TextStyle(color: Colors.grey[600], fontStyle: FontStyle.italic));

  Widget _dropdownUser({
    required String label,
    required List<Map<String, dynamic>> users,
    required int? selectedId,
    required ValueChanged<int?> onChanged,
  }) => DropdownSearch<Map<String, dynamic>>(
    items: (String? filter, _) {
      final filtered = filter == null || filter.isEmpty
          ? users
          : users.where((u) => (u['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
      return Future.value(filtered);
    },
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
  }) => DropdownSearch<Map<String, dynamic>>(
    items: (String? filter, _) {
      final filtered = filter == null || filter.isEmpty
          ? products
          : products.where((p) => (p['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
      return Future.value(filtered);
    },
    selectedItem: products.firstWhereOrNull((p) => p['product_id'] == selectedId),
    itemAsString: (p) => p['name'] ?? '',
    compareFn: (a, b) => a['product_id'] == b['product_id'],
    onChanged: (val) => onChanged(val?['product_id'] as int?),
    popupProps: const PopupProps.menu(showSearchBox: true),
    decoratorProps: DropDownDecoratorProps(
      decoration: InputDecoration(labelText: label),
    ),
  );

  /// Builds the history table with coordinated scroll behavior
  Widget _buildHistoryTable() {
    return Container(
      height: 300,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: _toastRoundsFuture,
        builder: (ctx, snap) {
          if (snap.connectionState == ConnectionState.waiting)
            return const Center(child: CircularProgressIndicator());
          final rounds = snap.data ?? [];
          if (rounds.isEmpty) return const Center(child: Text('No toast rounds found.'));
          
          return SingleChildScrollView(
            controller: _historyScrollController,
            scrollDirection: Axis.vertical,
            physics: _CoordinatedScrollPhysics(
              mainController: _mainScrollController,
            ),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('Toast-Consumer')),
                  DataColumn(label: Text('Salesman')),
                  DataColumn(label: Text('Time')),
                ],
                rows: rounds.reversed.map((round) {
                  final sales = (round['sales'] as List?) ?? [];
                  String formattedDate = '';
                  final dateTime = round['date_time'];
                  if (dateTime != null) {
                    final dateStr = dateTime.toString();
                    if (dateStr.isNotEmpty) {
                      final parts = dateStr.split(' ');
                      if (parts.length >= 2) {
                        final datePart = parts[0];
                        final timePart = parts[1].split(':').take(2).join(':');
                        formattedDate = '$datePart\n$timePart';
                      } else {
                        formattedDate = dateStr;
                      }
                    }
                  }
                  final summary = sales.map((s) {
                    final consumerField = s['consumer'];
                    final donatorField = s['donator'];
                    final productField = s['product'];
                    final user = consumerField is Map && consumerField['name'] != null ? consumerField['name'] : consumerField?.toString() ?? '';
                    final donator = donatorField is Map && donatorField['name'] != null ? donatorField['name'] : donatorField?.toString() ?? '';
                    final product = productField is Map && productField['name'] != null ? productField['name'] : productField?.toString() ?? '';
                    String ret = '';
                    if (donator != '') {
                      ret = '[$donator($user): $product]';
                    } else {
                      ret = '[$user: $product]';
                    }
                    return ret;
                  }).join(', ');
                  
                  // Extract salesman from the toast round
                  String salesman = '';
                  final salesmanField = round['salesman'];
                  if (salesmanField is Map && salesmanField['name'] != null) {
                    salesman = salesmanField['name'].toString();
                  } else if (salesmanField != null) {
                    salesman = salesmanField.toString();
                  }
                  
                  return DataRow(cells: [
                    DataCell(Text(summary)),
                    DataCell(Text(salesman)),
                    DataCell(Text(formattedDate)),
                  ]);
                }).toList(),
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
    // If we're at the top of the history table and trying to scroll up
    if (position.pixels <= 0 && offset > 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the history table
      }
    }
    // If we're at the bottom of the history table and trying to scroll down
    else if (position.pixels >= position.maxScrollExtent && offset < 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the history table
      }
    }
    return super.applyPhysicsToUserOffset(position, offset);
  }
}