import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:provider/provider.dart';

class ReturnPfandPage extends StatefulWidget {
  const ReturnPfandPage({super.key});

  @override
  State<ReturnPfandPage> createState() => _ReturnPfandPageState();
}

class _ReturnPfandPageState extends State<ReturnPfandPage> {
  late Future<List<Map<String, dynamic>>> _productsFuture;
  late Future<List<Map<String, dynamic>>> _usersFuture;
  late Future<List<Map<String, dynamic>>> _pfandHistory;

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
  _pfandHistory = PyBridge().getPfandHistory();
}

void _onUserSelected(int? userId) async {
  if (userId == null) return;

  final pfandData = await _pfandHistory;
  // Filter by selected user and counter > 0
  final userProducts = pfandData.where((p) => p['user_id'] == userId && (p['counter'] ?? 0) > 0).toList();

  setState(() {
    _selectedUser = userId;
    _allProducts = pfandData;
    _filteredProducts = userProducts;
    _removedProducts.clear();
    _controllers.clear();
    _productAmounts.clear();

    for (var p in userProducts) {
      final id = p['product_id'].toString();
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
      final id = product['product_id'].toString();
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

  void _onSubmit() async {
    final selectedProducts = _filteredProducts.map((product) {
      final id = product['product_id'].toString();
      final amountText = _controllers[id]?.text ?? '1';
      final amount = int.tryParse(amountText) ?? 1;
      return {'id': product['product_id'], 'amount': amount};
    }).toList();
    if (_selectedUser == null || selectedProducts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a user and at least one product')),
      );
      return;
    }

    try {
      final auth = Provider.of<AuthService>(context, listen: false);
      final salesmanId = auth.currentUserId;
      if (salesmanId == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Unable to identify current user')),
        );
        return;
      }
      
      await PyBridge().submitPfandReturn(_selectedUser!, selectedProducts, salesmanId);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Submit pressed!')),
      );
      // Refresh pfand history and update UI
      final pfandData = await PyBridge().getPfandHistory();
      // Filter by selected user and counter > 0
      final userProducts = pfandData.where((p) => p['user_id'] == _selectedUser! && (p['counter'] ?? 0) > 0).toList();
      setState(() {
        _allProducts = pfandData;
        _filteredProducts = userProducts;
        _removedProducts.clear();
        _controllers.clear();
        _productAmounts.clear();
        for (var p in userProducts) {
          final id = p['product_id'].toString();
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
      if (userProducts.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No Pfand items left for this user.')),
        );
      }
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
                if (userSnapshot.connectionState == ConnectionState.waiting) {
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
                              final id = product['product_id'].toString();
                              final amountController = _controllers[id]!;
                              if (_selectedUser != null && _filteredProducts.isEmpty) {
                                return const Padding(
                                  padding: EdgeInsets.only(top: 20),
                                  child: Text('No Pfand items found for this user.'),
                                );
                              }
                              return Card(
                                child: ListTile(
                                  title: Text(product['product']['name'] ?? ''),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('Pfand: ${product['product']['pfand']}'),
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
                                          const SizedBox(width: 8),
                                          Text('Borrowed: ${product['counter']}'),
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
                                    title: Text(product['product']['name'] ?? ''),
                                    subtitle: Text('Pfand: ${product['product']['pfand']}'),
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
