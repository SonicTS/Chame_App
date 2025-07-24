import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';
import 'package:provider/provider.dart';

class PurchasePage extends StatefulWidget {
  const PurchasePage({super.key});

  @override
  State<PurchasePage> createState() => _PurchasePageState();
}

// User Selection Widget
class _UserSelectionWidget extends StatelessWidget {
  final List<Map<String, dynamic>> users;
  final int? selectedUserId;
  final Map<String, dynamic>? selectedUser;
  final Function(Map<String, dynamic>?) onUserChanged;

  const _UserSelectionWidget({
    required this.users,
    required this.selectedUserId,
    required this.selectedUser,
    required this.onUserChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownSearch<Map<String, dynamic>>(
          items: (String? filter, _) {
            final filtered = filter == null || filter.isEmpty
                ? users
                : users.where((u) => (u['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
            return Future.value(filtered);
          },
          selectedItem: users.firstWhereOrNull((u) => u['user_id'] == selectedUserId),
          itemAsString: (u) => u['name'] ?? '',
          compareFn: (a, b) => a['user_id'] == b['user_id'],
          onChanged: onUserChanged,
          popupProps: const PopupProps.menu(
            showSearchBox: true,
          ),
          decoratorProps: const DropDownDecoratorProps(
            decoration: InputDecoration(labelText: 'Select User'),
          ),
        ),
        if (selectedUser != null) ...[
          const SizedBox(height: 12),
          _UserBalanceCard(balance: (selectedUser!['balance'] as num?)?.toDouble() ?? 0.0),
        ],
      ],
    );
  }
}

// User Balance Card Widget
class _UserBalanceCard extends StatelessWidget {
  final double balance;
  final double? pendingDeduction;
  final bool isProcessing;

  const _UserBalanceCard({
    required this.balance,
    this.pendingDeduction,
    this.isProcessing = false,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBalance = pendingDeduction != null 
        ? balance - pendingDeduction! 
        : balance;
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isProcessing 
            ? [Colors.orange.shade50, Colors.orange.shade100]
            : [Colors.blue.shade50, Colors.blue.shade100],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isProcessing 
            ? Colors.orange.shade300 
            : Colors.blue.shade300, 
          width: 2
        ),
        boxShadow: [
          BoxShadow(
            color: (isProcessing 
              ? Colors.orange.shade200 
              : Colors.blue.shade200).withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isProcessing 
                ? Colors.orange.shade600 
                : Colors.blue.shade600,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              isProcessing 
                ? Icons.hourglass_empty 
                : Icons.account_balance_wallet, 
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isProcessing ? 'Processing...' : 'Current Balance',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Row(
                  children: [
                    Text(
                      '€${effectiveBalance.toStringAsFixed(2)}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 24,
                        color: effectiveBalance > 0 ? Colors.green : Colors.red,
                      ),
                    ),
                    if (pendingDeduction != null && !isProcessing) ...[
                      const SizedBox(width: 8),
                      Text(
                        '(-€${pendingDeduction!.toStringAsFixed(2)})',
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.red,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          if (isProcessing)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            Icon(
              effectiveBalance > 0 ? Icons.check_circle : Icons.warning,
              color: effectiveBalance > 0 ? Colors.green : Colors.orange,
              size: 20,
            ),
        ],
      ),
    );
  }
}

// Product Selection Widget
class _ProductSelectionWidget extends StatelessWidget {
  final List<Map<String, dynamic>> products;
  final int? selectedProductId;
  final int quantity;
  final Function(Map<String, dynamic>?) onProductChanged;
  final Function(int) onQuantityChanged;

  const _ProductSelectionWidget({
    required this.products,
    required this.selectedProductId,
    required this.quantity,
    required this.onProductChanged,
    required this.onQuantityChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownSearch<Map<String, dynamic>>(
          items: (String? filter, _) {
            final filtered = filter == null || filter.isEmpty
                ? products
                : products.where((p) => (p['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
            return Future.value(filtered);
          },
          selectedItem: products.firstWhereOrNull((p) => p['product_id'] == selectedProductId),
          itemAsString: (p) => p['name'] ?? '',
          compareFn: (a, b) => a['product_id'] == b['product_id'],
          onChanged: onProductChanged,
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
            initialValue: quantity.toString(),
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Quantity'),
            onChanged: (v) => onQuantityChanged(int.tryParse(v) ?? 1),
          ),
        ),
      ],
    );
  }
}

// Action Buttons Widget
class _ActionButtonsWidget extends StatelessWidget {
  final bool isSubmitting;
  final bool canAddToCart;
  final VoidCallback? onAddToCart;
  final VoidCallback? onBuyNow;

  const _ActionButtonsWidget({
    required this.isSubmitting,
    required this.canAddToCart,
    this.onAddToCart,
    this.onBuyNow,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 400) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ElevatedButton(
                onPressed: canAddToCart ? onAddToCart : null,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: const Text('Add to Cart'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: isSubmitting ? null : onBuyNow,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: isSubmitting
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Buy Now'),
              ),
            ],
          );
        } else {
          return Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: canAddToCart ? onAddToCart : null,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: const Text('Add to Cart'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: isSubmitting ? null : onBuyNow,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: isSubmitting
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Buy Now'),
                ),
              ),
            ],
          );
        }
      },
    );
  }
}

// Shopping Cart Item Widget
class _CartItemWidget extends StatelessWidget {
  final Map<String, dynamic> item;
  final int index;
  final Function(int) onRemove;
  final Function(int, int) onQuantityChanged;

  const _CartItemWidget({
    required this.item,
    required this.index,
    required this.onRemove,
    required this.onQuantityChanged,
  });

  @override
  Widget build(BuildContext context) {
    final product = item['product'] as Map<String, dynamic>;
    final quantity = item['quantity'] as int;
    final price = (product['price_per_unit'] as num?)?.toDouble() ?? 0.0;
    final total = price * quantity;

    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  product['name'] ?? '',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete, color: Colors.red),
                onPressed: () => onRemove(index),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '€${price.toStringAsFixed(2)} each',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _QuantityControls(
                quantity: quantity,
                onChanged: (newQuantity) => onQuantityChanged(index, newQuantity),
              ),
              Text(
                '€${total.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Colors.green,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// Quantity Controls Widget
class _QuantityControls extends StatelessWidget {
  final int quantity;
  final Function(int) onChanged;

  const _QuantityControls({
    required this.quantity,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: const Icon(Icons.remove, size: 18),
            onPressed: () => onChanged(quantity - 1),
            padding: const EdgeInsets.all(8),
            constraints: const BoxConstraints(),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Text(
              '$quantity',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.add, size: 18),
            onPressed: () => onChanged(quantity + 1),
            padding: const EdgeInsets.all(8),
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }
}

// Shopping Cart Widget
class _ShoppingCartWidget extends StatelessWidget {
  final List<Map<String, dynamic>> shoppingCart;
  final double totalCost;
  final bool isSubmitting;
  final VoidCallback onPurchaseAll;
  final VoidCallback onClearCart;
  final Function(int) onRemoveItem;
  final Function(int, int) onUpdateQuantity;

  const _ShoppingCartWidget({
    required this.shoppingCart,
    required this.totalCost,
    required this.isSubmitting,
    required this.onPurchaseAll,
    required this.onClearCart,
    required this.onRemoveItem,
    required this.onUpdateQuantity,
  });

  @override
  Widget build(BuildContext context) {
    if (shoppingCart.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Shopping Cart', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            children: [
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: shoppingCart.length,
                separatorBuilder: (context, index) => const Divider(height: 1),
                itemBuilder: (context, index) => _CartItemWidget(
                  item: shoppingCart[index],
                  index: index,
                  onRemove: onRemoveItem,
                  onQuantityChanged: onUpdateQuantity,
                ),
              ),
              const Divider(),
              _CartTotalWidget(
                totalCost: totalCost,
                isSubmitting: isSubmitting,
                onPurchaseAll: onPurchaseAll,
                onClearCart: onClearCart,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// Cart Total Widget
class _CartTotalWidget extends StatelessWidget {
  final double totalCost;
  final bool isSubmitting;
  final VoidCallback onPurchaseAll;
  final VoidCallback onClearCart;

  const _CartTotalWidget({
    required this.totalCost,
    required this.isSubmitting,
    required this.onPurchaseAll,
    required this.onClearCart,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Total:',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
              Text(
                '€${totalCost.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: Colors.green,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Column(
            children: [
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: isSubmitting ? null : onPurchaseAll,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: isSubmitting
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Purchase All', style: TextStyle(fontSize: 16)),
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onClearCart,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: const Text('Clear Cart', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// Sales Configuration Widget
class _SalesConfigWidget extends StatelessWidget {
  final String salesConfig;
  final Function(String) onConfigChanged;

  const _SalesConfigWidget({
    required this.salesConfig,
    required this.onConfigChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Text('Configure Sales Table:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(width: 12),
        Expanded(
          child: DropdownButton<String>(
            value: salesConfig,
            isExpanded: true,
            items: const [
              DropdownMenuItem(value: 'all', child: Text('All')),
              DropdownMenuItem(value: 'raw', child: Text('Raw')),
              DropdownMenuItem(value: 'toast', child: Text('Toast')),
            ],
            onChanged: (val) => onConfigChanged(val!),
          ),
        ),
      ],
    );
  }
}

// Sales Table Widget
class _SalesTableWidget extends StatefulWidget {
  final Map<String, dynamic>? paginatedSalesData;
  final String salesConfig;
  final ScrollController mainController;
  final bool isLoading;
  final int currentPage;
  final int totalPages;
  final int totalSales;
  final VoidCallback onNextPage;
  final VoidCallback onPreviousPage;
  final VoidCallback onFirstPage;
  final VoidCallback onLastPage;

  const _SalesTableWidget({
    required this.paginatedSalesData,
    required this.salesConfig,
    required this.mainController,
    required this.isLoading,
    required this.currentPage,
    required this.totalPages,
    required this.totalSales,
    required this.onNextPage,
    required this.onPreviousPage,
    required this.onFirstPage,
    required this.onLastPage,
  });

  @override
  State<_SalesTableWidget> createState() => _SalesTableWidgetState();
}

class _SalesTableWidgetState extends State<_SalesTableWidget> {
  final ScrollController _horizontalScrollController = ScrollController();
  final ScrollController _verticalScrollController = ScrollController();

  @override
  void dispose() {
    _horizontalScrollController.dispose();
    _verticalScrollController.dispose();
    super.dispose();
  }

  String _formatTimestamp(dynamic ts) {
    if (ts == null) return '';
    if (ts is DateTime) return ts.toString();
    if (ts is String) return ts;
    return ts.toString();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    final salesData = widget.paginatedSalesData;
    if (salesData == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20.0),
          child: Text('No sales data available.'),
        ),
      );
    }
    
    final allSales = (salesData['sales'] as List<dynamic>?)
        ?.cast<Map<String, dynamic>>() ?? [];
    
    final filteredSales = widget.salesConfig == 'all'
        ? allSales
        : allSales.where((s) => s['product']?['category'] == widget.salesConfig).toList();
    
    if (filteredSales.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20.0),
          child: Text('No sales found for the selected category.'),
        ),
      );
    }
    
    return Column(
      children: [
        // Pagination info and controls
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(8),
              topRight: Radius.circular(8),
            ),
          ),
          child: Column(
            children: [
              // Sales count info
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Flexible(
                    child: Text(
                      'Showing ${filteredSales.length} of ${widget.totalSales} sales',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Pagination controls
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Page ${widget.currentPage} of ${widget.totalPages}',
                    style: const TextStyle(fontSize: 14),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.first_page),
                    onPressed: widget.currentPage > 1 ? widget.onFirstPage : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                    padding: const EdgeInsets.all(2),
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: widget.currentPage > 1 ? widget.onPreviousPage : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                    padding: const EdgeInsets.all(2),
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: widget.currentPage < widget.totalPages ? widget.onNextPage : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                    padding: const EdgeInsets.all(2),
                  ),
                  IconButton(
                    icon: const Icon(Icons.last_page),
                    onPressed: widget.currentPage < widget.totalPages ? widget.onLastPage : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                    padding: const EdgeInsets.all(2),
                  ),
                ],
              ),
            ],
          ),
        ),
        // Sales table
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey.shade300),
              borderRadius: const BorderRadius.only(
                bottomLeft: Radius.circular(8),
                bottomRight: Radius.circular(8),
              ),
            ),
            child: Scrollbar(
              controller: _horizontalScrollController,
              thumbVisibility: true,
              child: SingleChildScrollView(
                controller: _horizontalScrollController,
                scrollDirection: Axis.horizontal,
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minWidth: MediaQuery.of(context).size.width - 32,
                  ),
                  child: Scrollbar(
                    controller: _verticalScrollController,
                    thumbVisibility: true,
                    child: SingleChildScrollView(
                      controller: _verticalScrollController,
                      scrollDirection: Axis.vertical,
                      physics: _CoordinatedScrollPhysics(
                        mainController: widget.mainController,
                      ),
                      child: _buildDataTable(filteredSales),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDataTable(List<Map<String, dynamic>> sales) {
    return DataTable(
      columnSpacing: 12,
      horizontalMargin: 12,
      dataRowMinHeight: 48,
      headingRowHeight: 48,
      columns: const [
        DataColumn(label: Text('ID', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Consumer', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Donator', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Salesman', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Product', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Qty', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Price', style: TextStyle(fontWeight: FontWeight.bold))),
        DataColumn(label: Text('Date', style: TextStyle(fontWeight: FontWeight.bold))),
      ],
      rows: sales.map((sale) => _buildDataRow(sale)).toList(),
    );
  }

  DataRow _buildDataRow(Map<String, dynamic> sale) {
    String consumer = '';
    String donator = '';
    String salesman = '';
    String product = '';
    
    try {
      final consumerField = sale['consumer'];
      final donatorField = sale['donator'];
      final salesmanField = sale['salesman'];
      final productField = sale['product'];
      
      consumer = consumerField is Map && consumerField['name'] != null
          ? consumerField['name'].toString()
          : consumerField?.toString() ?? '';
      donator = donatorField == null
          ? ''
          : (donatorField is Map && donatorField['name'] != null
              ? donatorField['name'].toString()
              : donatorField.toString());
      salesman = salesmanField is Map && salesmanField['name'] != null
          ? salesmanField['name'].toString()
          : salesmanField?.toString() ?? '';
      product = productField is Map && productField['name'] != null
          ? productField['name'].toString()
          : productField?.toString() ?? '';
    } catch (e) {
      consumer = sale['consumer']?.toString() ?? '';
      donator = sale['donator']?.toString() ?? '';
      salesman = sale['salesman']?.toString() ?? '';
      product = sale['product']?.toString() ?? '';
    }
    
    String formattedDate = '';
    try {
      final timestamp = sale['timestamp'];
      if (timestamp != null) {
        final dateStr = _formatTimestamp(timestamp);
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
    } catch (e) {
      formattedDate = _formatTimestamp(sale['timestamp']);
    }
    
    return DataRow(
      key: ValueKey(sale['sale_id']),
      cells: [
        DataCell(Text(sale['sale_id']?.toString() ?? '', style: const TextStyle(fontSize: 12))),
        DataCell(SizedBox(width: 80, child: Text(consumer, style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis, maxLines: 2))),
        DataCell(SizedBox(width: 80, child: Text(donator, style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis, maxLines: 2))),
        DataCell(SizedBox(width: 80, child: Text(salesman, style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis, maxLines: 2))),
        DataCell(SizedBox(width: 100, child: Text(product, style: const TextStyle(fontSize: 12), overflow: TextOverflow.ellipsis, maxLines: 2))),
        DataCell(Text(sale['quantity']?.toString() ?? '', style: const TextStyle(fontSize: 12))),
        DataCell(Text('€${sale['total_price']?.toString() ?? ''}', style: const TextStyle(fontSize: 12))),
        DataCell(SizedBox(width: 80, child: Text(formattedDate, style: const TextStyle(fontSize: 10), maxLines: 2, overflow: TextOverflow.ellipsis))),
      ],
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
    // If we're at the top of the sales table and trying to scroll up
    if (position.pixels <= 0 && offset > 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the sales table
      }
    }
    // If we're at the bottom of the sales table and trying to scroll down
    else if (position.pixels >= position.maxScrollExtent && offset < 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the sales table
      }
    }
    return super.applyPhysicsToUserOffset(position, offset);
  }
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
    setState(() {
      _usersFuture = PyBridge().getAllUsers();
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
      final salesData = await PyBridge().getSalesPaginated(
        page: _currentPage, 
        pageSize: _pageSize
      );
      
      setState(() {
        _paginatedSalesData = salesData;
        _totalSales = salesData['total_count'] ?? 0;
        _totalPages = salesData['total_pages'] ?? 1;
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
      final price = (item['product']['price_per_unit'] as num?)?.toDouble() ?? 0.0;
      final quantity = item['quantity'] as int;
      return sum + (price * quantity);
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

    if (_selectedUser != null) {
      final userBalance = (_selectedUser!['balance'] as num?)?.toDouble() ?? 0.0;
      if (userBalance < _totalCost) {
        _showDialog('Error', 'Insufficient balance. User balance: €${userBalance.toStringAsFixed(2)}, Total cost: €${_totalCost.toStringAsFixed(2)}');
        return;
      }
    }

    setState(() => _isSubmitting = true);
    
    final itemList = _shoppingCart.map((item) => {
      'consumer_id': _selectedUserId!,
      'product_id': item['product']['product_id'] as int,
      'quantity': item['quantity'] as int,
    }).toList();

    final error = await PyBridge().makeMultiplePurchases(itemList: itemList, salesmanId: salesmanId);
    setState(() => _isSubmitting = false);
    
    if (error != null) {
      _showDialog('Error', error);
    } else {
      final oldBalance = (_selectedUser?['balance'] as num?)?.toDouble() ?? 0.0;
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
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _UserSelectionWidget(
                            users: users,
                            selectedUserId: _selectedUserId,
                            selectedUser: _selectedUser,
                            onUserChanged: (val) => setState(() {
                              _selectedUserId = val?['user_id'] as int?;
                              _selectedUser = val;
                            }),
                          ),
                          const SizedBox(height: 16),
                          _ProductSelectionWidget(
                            products: products,
                            selectedProductId: _selectedProductId,
                            quantity: _quantity,
                            onProductChanged: (val) => setState(() => _selectedProductId = val?['product_id'] as int?),
                            onQuantityChanged: (val) => setState(() => _quantity = val),
                          ),
                          const SizedBox(height: 16),
                          _ActionButtonsWidget(
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
                          _ShoppingCartWidget(
                            shoppingCart: _shoppingCart,
                            totalCost: _totalCost,
                            isSubmitting: _isSubmitting,
                            onPurchaseAll: _submitMultiplePurchases,
                            onClearCart: _clearCart,
                            onRemoveItem: _removeFromCart,
                            onUpdateQuantity: _updateCartQuantity,
                          ),
                          const SizedBox(height: 24),
                          _SalesConfigWidget(
                            salesConfig: _salesConfig,
                            onConfigChanged: (val) {
                              setState(() => _salesConfig = val);
                              // No need to reload data since filtering is done client-side
                            },
                          ),
                          const SizedBox(height: 12),
                          const Text('Sales', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                          const SizedBox(height: 12),
                          SizedBox(
                            height: 400, // Fixed height for the table with pagination
                            child: _SalesTableWidget(
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
