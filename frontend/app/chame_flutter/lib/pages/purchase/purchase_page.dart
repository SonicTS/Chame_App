import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:provider/provider.dart';

import 'purchase_pricing.dart';
import 'widgets/user_selection_section.dart';
import 'package:chame_flutter/widgets/shared/user_dropdown_selector.dart';
import 'package:chame_flutter/widgets/shared/user_balance_card.dart';
import 'widgets/product_selection_widget.dart';
import 'widgets/action_buttons_widget.dart';
import 'widgets/shopping_cart_widget.dart';
import 'widgets/sales_config_widget.dart';
import 'widgets/sales_table_widget.dart';

class PurchasePage extends StatefulWidget {
  const PurchasePage({super.key});

  @override
  State<PurchasePage> createState() => _PurchasePageState();
}

class _PurchasePageState extends State<PurchasePage> {
  late Future<List<Map<String, dynamic>>> _usersFuture;
  late Future<List<Map<String, dynamic>>> _productsFuture;
  int? _selectedUserId;
  Map<String, dynamic>? _selectedUser;
  int? _selectedProductId;
  int _quantity = 1;
  bool _isSubmitting = false;
  String _salesConfig = 'all';
  bool _includeDonator = false;
  int? _donatorId;
  Map<String, dynamic>? _donator;
  
  // Shopping cart functionality
  List<Map<String, dynamic>> _shoppingCart = [];
  double _totalCost = 0.0;

  // Main scroll controller for coordinated scrolling
  final ScrollController _mainScrollController = ScrollController();

  // Pagination state
  int _currentPage = 1;
  int _pageSize = 100;
  int _totalPages = 1;
  int _totalSales = 0;
  bool _isLoadingSales = false;
  Map<String, dynamic>? _paginatedSalesData;

  @override
  void initState() {
    super.initState();
    _fetchAll();
  }

  void _fetchAll() {
    final auth = Provider.of<AuthService>(context, listen: false);
    setState(() {
      _usersFuture = PyBridge().getAllUsers().then(auth.filterVisibleUsers);
      _productsFuture = PyBridge().getAllRawProducts();
    });
    
    // Load paginated sales
    _loadPaginatedSales();
    
    // Update the selected user data to reflect current balance
    _updateSelectedUserData();
  }

  Future<void> _loadPaginatedSales() async {
    if (_isLoadingSales) return;
    
    setState(() {
      _isLoadingSales = true;
    });
    
    try {
      final auth = Provider.of<AuthService>(context, listen: false);
      // Fetch the full sales list and apply visibility filtering so we can
      // build a client-side paginated list that matches the filtered set.
      final allSales = await PyBridge().getAllSales();
      final visible = auth.filterVisibleRecords(allSales.cast<Map<String, dynamic>>());

      // Apply top-level salesConfig filter (category) before paginating
      final afterConfig = _salesConfig == 'all'
          ? visible
          : visible.where((s) => s['product']?['category'] == _salesConfig).toList();

      final totalVisible = afterConfig.length;
      final computedPages = (totalVisible + _pageSize - 1) ~/ _pageSize;
      final page = _currentPage.clamp(1, computedPages == 0 ? 1 : computedPages);
      final start = (page - 1) * _pageSize;
      final end = (start + _pageSize) > totalVisible ? totalVisible : (start + _pageSize);
      final pageSlice = start < end ? afterConfig.sublist(start, end) : <Map<String, dynamic>>[];

      setState(() {
        _paginatedSalesData = {
          'sales': pageSlice,
          'total_count': totalVisible,
          'page': page,
          'page_size': _pageSize,
          'total_pages': computedPages,
        };
        _totalSales = totalVisible;
        _totalPages = computedPages;
        _isLoadingSales = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingSales = false;
      });
      print('Error loading paginated sales: $e');
    }
  }

  void _goToNextPage() {
    if (_currentPage < _totalPages) {
      setState(() {
        _currentPage++;
      });
      _loadPaginatedSales();
    }
  }

  void _goToPreviousPage() {
    if (_currentPage > 1) {
      setState(() {
        _currentPage--;
      });
      _loadPaginatedSales();
    }
  }

  void _goToFirstPage() {
    if (_currentPage != 1) {
      setState(() {
        _currentPage = 1;
      });
      _loadPaginatedSales();
    }
  }

  void _goToLastPage() {
    if (_currentPage != _totalPages) {
      setState(() {
        _currentPage = _totalPages;
      });
      _loadPaginatedSales();
    }
  }

  Future<void> _updateSelectedUserData() async {
    if (_selectedUserId != null) {
      try {
        final users = await _usersFuture;
        final updatedUser = users.firstWhere(
          (user) => user['user_id'] == _selectedUserId,
          orElse: () => <String, dynamic>{},
        );
        
        if (updatedUser.isNotEmpty && mounted) {
          setState(() {
            _selectedUser = updatedUser;
          });
        }
      } catch (e) {
        // Handle error gracefully - user data will be updated when UI rebuilds
      }
    }
  }

  Future<void> _updateDonatorData() async {
    if (_donatorId != null) {
      try {
        final users = await _usersFuture;
        final updated = users.firstWhere(
          (u) => u['user_id'] == _donatorId,
          orElse: () => <String, dynamic>{},
        );
        if (updated.isNotEmpty && mounted) {
          setState(() {
            _donator = updated;
          });
        }
      } catch (e) {
        // ignore
      }
    }
  }

  void _addToCart(Map<String, dynamic> product, int quantity) {
    if (quantity < 1) return;
    
    setState(() {
      final existingIndex = _shoppingCart.indexWhere(
        (item) => item['product']['product_id'] == product['product_id']
      );
      
      if (existingIndex >= 0) {
        _shoppingCart[existingIndex]['quantity'] += quantity;
      } else {
        _shoppingCart.add({
          'product': product,
          'quantity': quantity,
        });
      }
      
      _updateTotalCost();
    });
  }

  void _removeFromCart(int index) {
    setState(() {
      _shoppingCart.removeAt(index);
      _updateTotalCost();
    });
  }

  void _updateCartQuantity(int index, int newQuantity) {
    if (newQuantity < 1) {
      _removeFromCart(index);
      return;
    }
    
    setState(() {
      _shoppingCart[index]['quantity'] = newQuantity;
      _updateTotalCost();
    });
  }

  void _updateTotalCost() {
    _totalCost = _shoppingCart.fold<double>(0.0, (sum, item) {
      final quantity = item['quantity'] as int;
      final product = item['product'] as Map<String, dynamic>;
      return sum + getCheckoutTotal(product, quantity);
    });
  }

  void _clearCart() {
    setState(() {
      _shoppingCart.clear();
      _totalCost = 0.0;
    });
  }

  Future<void> _submitMultiplePurchases() async {
    if (_selectedUserId == null || _shoppingCart.isEmpty) {
      _showDialog('Error', 'Please select a user and add items to cart.');
      return;
    }

    final auth = Provider.of<AuthService>(context, listen: false);
    final salesmanId = auth.currentUserId;
    if (salesmanId == null) {
      _showDialog('Error', 'Unable to identify current user');
      return;
    }

    // Determine the actual payer (donator when included) and keep it in
    // outer scope so it's available for the confirmation and summary below.
    final Map<String, dynamic>? payer = _includeDonator && _donator != null ? _donator : _selectedUser;
    if (_selectedUser != null) {
      final payerBalance = (payer?['balance'] as num?)?.toDouble() ?? 0.0;
      final payerAllowedDebt = (payer?['allowed_debt'] as num?)?.toDouble() ?? 0.0;
      if (payerBalance + payerAllowedDebt < _totalCost) {
        final name = _includeDonator ? (payer?['name'] ?? 'Donator') : (payer?['name'] ?? 'User');
        _showDialog('Error', 'Insufficient balance. $name balance: €${payerBalance.toStringAsFixed(2)}, allowed debt: €${payerAllowedDebt.toStringAsFixed(2)}, Total cost: €${_totalCost.toStringAsFixed(2)}');
        return;
      }
      // If purchase will put the payer into debt, confirm with the user
      if (payerBalance < _totalCost) {
        final debtAmount = (_totalCost - payerBalance);
        final confirmed = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('Confirm Debt'),
            content: Text('This purchase will put ${payer?['name'] ?? 'the user'} into debt by €${debtAmount.toStringAsFixed(2)}. Proceed?'),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
              TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Proceed')),
            ],
          ),
        );
        if (confirmed != true) return;
      }
    }

    setState(() => _isSubmitting = true);
    
    final itemList = _shoppingCart.map((item) => {
      'consumer_id': _selectedUserId!,
      if (_includeDonator && _donatorId != null) 'donator_id': _donatorId,
      'product_id': item['product']['product_id'] as int,
      'quantity': item['quantity'] as int,
    }).toList();

    final error = await PyBridge().makeMultiplePurchases(itemList: itemList, salesmanId: salesmanId);
    setState(() => _isSubmitting = false);
    
    if (error != null) {
      _showDialog('Error', error);
    } else {
      final oldBalance = (payer?['balance'] as num?)?.toDouble() ?? 0.0;
      final newBalance = oldBalance - _totalCost;
      
      _showDialog('Success', 
        'Purchase successful!\n'
        'Total: €${_totalCost.toStringAsFixed(2)}\n'
        'Previous balance: €${oldBalance.toStringAsFixed(2)}\n'
        'New balance: €${newBalance.toStringAsFixed(2)}'
      );
      
      _clearCart();
      // Reset form for next purchase
      setState(() {
        _selectedProductId = null;
        _quantity = 1;
      });
      // Refresh all data after successful purchase - most importantly user balance
      _fetchAll();
      // Also refresh donator data immediately so their balance card updates
      _updateDonatorData();
    }
  }

  Future<void> _submit() async {
    if (_selectedUserId == null || _selectedProductId == null || _quantity < 1) {
      _showDialog('Error', 'Please select user, product, and enter a valid quantity.');
      return;
    }
    
    final productsFuture = await _productsFuture;
    final product = productsFuture.firstWhere(
      (p) => p['product_id'] == _selectedProductId,
      orElse: () => <String, dynamic>{},
    );
    
    if (product.isEmpty) {
      _showDialog('Error', 'Product not found.');
      return;
    }
    
    _clearCart();
    _addToCart(product, _quantity);
    await _submitMultiplePurchases();
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
      appBar: AppBar(title: const Text('Purchase')),
      body: SafeArea(
        child: SingleChildScrollView(
          controller: _mainScrollController,
          padding: const EdgeInsets.all(16.0),
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Purchase Form', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
              const SizedBox(height: 16),
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
                      // Compute a preview pending deduction:
                      // - If cart has items, show cart total
                      // - Otherwise, if a product is selected, preview that product*quantity
                      double? pendingDeductionPreview;
                      if (_shoppingCart.isNotEmpty) {
                        pendingDeductionPreview = _totalCost;
                      } else if (_selectedProductId != null) {
                        final sel = products.firstWhere((p) => p['product_id'] == _selectedProductId, orElse: () => <String, dynamic>{});
                        if (sel.isNotEmpty) {
                          pendingDeductionPreview = getCheckoutTotal(sel, _quantity);
                        } else {
                          pendingDeductionPreview = null;
                        }
                      } else {
                        pendingDeductionPreview = null;
                      }

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          UserSelectionSection(
                            users: users,
                            selectedUserId: _selectedUserId,
                            selectedUser: _selectedUser,
                            pendingDeduction: pendingDeductionPreview,
                            showBalance: !_includeDonator,
                            onUserChanged: (val) => setState(() {
                              _selectedUserId = val?['user_id'] as int?;
                              _selectedUser = val;
                            }),
                          ),
                          const SizedBox(height: 8),
                          // Optional donator checkbox + selector
                          CheckboxListTile(
                            value: _includeDonator,
                            onChanged: (v) {
                              setState(() {
                                _includeDonator = v ?? false;
                                if (!_includeDonator) {
                                  _donatorId = null;
                                  _donator = null;
                                }
                              });
                            },
                            title: const Text('Include Donator (payer) for this purchase'),
                            controlAffinity: ListTileControlAffinity.leading,
                            contentPadding: EdgeInsets.zero,
                          ),
                          if (_includeDonator) ...[
                            const SizedBox(height: 8),
                            UserDropdownSelector(
                              users: users,
                              selectedUserId: _donatorId,
                              onChanged: (val) {
                                setState(() {
                                  _donatorId = val?['user_id'] as int?;
                                  _donator = val;
                                });
                                _updateDonatorData();
                              },
                              label: 'Select Donator',
                            ),
                            if (_donator != null) ...[
                              const SizedBox(height: 12),
                              // Preview the selected donator's balance and pending deduction
                              UserBalanceCard(
                                balance: (_donator!['balance'] as num?)?.toDouble() ?? 0.0,
                                pendingDeduction: pendingDeductionPreview,
                              ),
                            ],
                          ],
                          const SizedBox(height: 16),
                          ProductSelectionWidget(
                            products: products,
                            selectedProductId: _selectedProductId,
                            quantity: _quantity,
                            onProductChanged: (val) => setState(() => _selectedProductId = val?['product_id'] as int?),
                            onQuantityChanged: (val) => setState(() => _quantity = val),
                          ),
                          const SizedBox(height: 16),
                          ActionButtonsWidget(
                            isSubmitting: _isSubmitting,
                            canAddToCart: _selectedProductId != null && _quantity >= 1,
                            onAddToCart: () async {
                              final product = products.firstWhere(
                                (p) => p['product_id'] == _selectedProductId,
                                orElse: () => <String, dynamic>{},
                              );
                              if (product.isNotEmpty) {
                                _addToCart(product, _quantity);
                              }
                            },
                            onBuyNow: _submit,
                          ),
                          const SizedBox(height: 24),
                          ShoppingCartWidget(
                            shoppingCart: _shoppingCart,
                            totalCost: _totalCost,
                            isSubmitting: _isSubmitting,
                            onPurchaseAll: _submitMultiplePurchases,
                            onClearCart: _clearCart,
                            onRemoveItem: _removeFromCart,
                            onUpdateQuantity: _updateCartQuantity,
                          ),
                          const SizedBox(height: 24),
                          SalesConfigWidget(
                            salesConfig: _salesConfig,
                            onConfigChanged: (val) {
                              setState(() => _salesConfig = val);
                              // Rebuild client-side pagination for the new config
                              _currentPage = 1;
                              _loadPaginatedSales();
                            },
                          ),
                          const SizedBox(height: 12),
                          const Text('Sales', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                          const SizedBox(height: 12),
                          SizedBox(
                            height: 400, // Fixed height for the table with pagination
                            child: SalesTableWidget(
                              paginatedSalesData: _paginatedSalesData,
                              salesConfig: _salesConfig,
                              mainController: _mainScrollController,
                              isLoading: _isLoadingSales,
                              currentPage: _currentPage,
                              totalPages: _totalPages,
                              totalSales: _totalSales,
                              onNextPage: _goToNextPage,
                              onPreviousPage: _goToPreviousPage,
                              onFirstPage: _goToFirstPage,
                              onLastPage: _goToLastPage,
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
      ),
    );
  }
}
