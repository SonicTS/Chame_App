import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';

class ReturnPfandPage extends StatefulWidget {
  const ReturnPfandPage({super.key});

  @override
  State<ReturnPfandPage> createState() => _ReturnPfandPageState();
}

class _ReturnPfandPageState extends State<ReturnPfandPage> {
  late Future<List<Map<String, dynamic>>> _productsFuture;
  late Future<List<Map<String, dynamic>>> _usersFuture;

  List<Map<String, dynamic>> _allProducts = [];
  List<Map<String, dynamic>> _filteredProducts = [];
  List<Map<String, dynamic>> _removedProducts = [];

  int? _selectedUser;
  String _userFilter = '';
  Map<String, int> _productAmounts = {};
  final Map<String, TextEditingController> _controllers = {};
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _productsFuture = PyBridge().getAllProducts();
    _usersFuture = PyBridge().getAllUsers();

    _productsFuture.then((products) {
      setState(() {
        _allProducts = products;
        _filteredProducts = products.where((p) => (p['pfand'] ?? 0) > 0).toList();
        for (var p in _filteredProducts) {
          final id = p['id'].toString();
          _productAmounts[id] = 1;
          _controllers[id] = TextEditingController(text: '1');
          _controllers[id]!.addListener(() {
            final value = int.tryParse(_controllers[id]!.text);
            if (value != null && value > 0) {
              _productAmounts[id] = value;
            }
          });
        }
      });
    });
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    _scrollController.dispose();
    super.dispose();
  }

  void _removeProduct(Map<String, dynamic> product) {
    setState(() {
      _filteredProducts.remove(product);
      _removedProducts.add(product);
    });
  }

  void _revertProduct(Map<String, dynamic> product) {
    setState(() {
      _removedProducts.remove(product);
      _filteredProducts.add(product);
      // Re-initialize controller if it was removed before
      final id = product['id'].toString();
      if (!_controllers.containsKey(id)) {
        _controllers[id] = TextEditingController(text: '1');
        _controllers[id]!.addListener(() {
          final value = int.tryParse(_controllers[id]!.text);
          if (value != null && value > 0) {
            _productAmounts[id] = value;
          }
        });
        _productAmounts[id] = 1;
      }
    });
  }

  void _onUserFilterChanged(String value) {
    setState(() {
      _userFilter = value.toLowerCase();
    });
  }

  void _onUserSelected(int? userId) {
    setState(() {
      _selectedUser = userId;
    });
  }

  void _onSubmit() async {
    final selectedProducts = _filteredProducts.map((product) {
      final id = product['product_id'];
      final amountText = _controllers[id]?.text ?? '1';
      final amount = int.tryParse(amountText) ?? 1;
      return {'id': id, 'amount': amount};
    }).toList();
    if (_selectedUser == null || selectedProducts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a user and at least one product')),
      );
      return;
    }

    try {
      await PyBridge().submitPfandReturn(_selectedUser!, selectedProducts);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Submit pressed!')),
      );
      setState(() {
        // Optionally: reset the UI here or navigate away
      });
    } catch (e) {
      debugPrint('Error submitting Pfand return: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error submitting: $e')),
      );
      return;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Return Pfand')),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return FutureBuilder<List<Map<String, dynamic>>>(
              future: _usersFuture,
              builder: (context, userSnapshot) {
                if (userSnapshot.connectionState == ConnectionState.waiting || _allProducts.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (userSnapshot.hasError) {
                  return Center(child: Text('Error: ${userSnapshot.error}'));
                }

                final users = userSnapshot.data ?? [];
                final filteredUsers = _userFilter.isEmpty
                    ? users
                    : users.where((u) => (u['name'] ?? '').toLowerCase().contains(_userFilter)).toList();

                return Scrollbar(
                  controller: _scrollController,
                  thumbVisibility: true,
                  child: SingleChildScrollView(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16.0),
                    keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                    child: ConstrainedBox(
                      constraints: BoxConstraints(minHeight: constraints.maxHeight),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Select User:', style: TextStyle(fontWeight: FontWeight.bold)),
                          TextField(
                            decoration: const InputDecoration(labelText: 'Filter users'),
                            onChanged: _onUserFilterChanged,
                          ),
                          DropdownButton<int>(
                            isExpanded: true,
                            value: _selectedUser,
                            hint: const Text('Choose user'),
                            items: filteredUsers.map((user) {
                              return DropdownMenuItem<int>(
                                value: user['user_id'],
                                child: Text(user['name'] ?? ''),
                              );
                            }).toList(),
                            onChanged: _onUserSelected,
                          ),
                          const SizedBox(height: 24),
                          const Text('Products with Pfand:', style: TextStyle(fontWeight: FontWeight.bold)),
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: _filteredProducts.length,
                            itemBuilder: (context, idx) {
                              final product = _filteredProducts[idx];
                              final id = product['id'].toString();
                              final amountController = _controllers[id]!;

                              return Card(
                                child: ListTile(
                                  title: Text(product['name'] ?? ''),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('Pfand: ${product['pfand']}'),
                                      const SizedBox(height: 8),
                                      Row(
                                        children: [
                                          const Text('Amount:'),
                                          const SizedBox(width: 8),
                                          SizedBox(
                                            width: 60,
                                            child: TextField(
                                              controller: amountController,
                                              keyboardType: TextInputType.number,
                                              decoration: const InputDecoration(
                                                isDense: true,
                                                contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                  trailing: IconButton(
                                    icon: const Icon(Icons.remove_circle, color: Colors.red),
                                    onPressed: () => _removeProduct(product),
                                  ),
                                ),
                              );
                            },
                          ),
                          if (_removedProducts.isNotEmpty) ...[
                            const SizedBox(height: 16),
                            const Text('Removed Products (tap to revert):', style: TextStyle(fontWeight: FontWeight.bold)),
                            ListView.builder(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: _removedProducts.length,
                              itemBuilder: (context, idx) {
                                final product = _removedProducts[idx];
                                return Card(
                                  color: Colors.grey[200],
                                  child: ListTile(
                                    title: Text(product['name'] ?? ''),
                                    subtitle: Text('Pfand: ${product['pfand']}'),
                                    trailing: const Icon(Icons.undo, color: Colors.green),
                                    onTap: () => _revertProduct(product),
                                  ),
                                );
                              },
                            ),
                          ],
                          const SizedBox(height: 32),
                          Center(
                            child: ElevatedButton(
                              onPressed: _onSubmit,
                              child: const Text('Submit'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
