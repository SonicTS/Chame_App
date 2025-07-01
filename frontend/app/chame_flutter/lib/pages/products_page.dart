import 'package:chame_flutter/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/widgets/simple_deletion_dialog.dart';
import 'package:provider/provider.dart';

class ProductsPage extends StatefulWidget {
  const ProductsPage({super.key});

  @override
  State<ProductsPage> createState() => _ProductsPageState();
}

class _ProductsPageState extends State<ProductsPage> {
  late Future<List<Map<String, dynamic>>> _productsFuture;
  String _productNameFilter = '';

  @override
  void initState() {
    super.initState();
    _productsFuture = PyBridge().getAllProducts();
  }

  void _reloadProducts() {
    setState(() {
      _productsFuture = PyBridge().getAllProducts();
    });
  }

  // Show simplified deletion dialog for products
  void _showProductDeletionDialog(BuildContext context, int productId, String productName) async {
    final result = await showSimpleDeletionDialog(
      context: context,
      entityType: 'product',
      entityId: productId,
      entityName: productName,
      deletedBy: 'flutter_admin',
    );
    
    if (result == true) {
      // Deletion was successful, reload the products
      _reloadProducts();
    }
  }

  // Helper to show dialog
  void _showDialog(BuildContext context, String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))],
      ),
    );
  }

  // Show restore dialog with deleted products
  void _showRestoreProductsDialog(BuildContext context) async {
    try {
      final deletedProducts = await PyBridge().getDeletedProducts();
      
      if (!context.mounted) return;
      
      if (deletedProducts.isEmpty) {
        _showDialog(context, 'No Deleted Products', 'There are no deleted products to restore.');
        return;
      }

      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Restore Deleted Products'),
          content: SizedBox(
            width: double.maxFinite,
            height: 400,
            child: ListView.builder(
              itemCount: deletedProducts.length,
              itemBuilder: (context, index) {
                final product = deletedProducts[index];
                return Card(
                  child: ListTile(
                    title: Text(product['name']?.toString() ?? 'Unknown'),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Category: ${product['category']?.toString() ?? 'N/A'}'),
                        Text('Price: ${product['price_per_unit']?.toString() ?? 'N/A'}'),
                        Text('Stock: ${product['stock_quantity']?.toString() ?? 'N/A'}'),
                        Text('Deleted: ${product['deleted_at']?.toString().split('T')[0] ?? 'N/A'}'),
                        Text('By: ${product['deleted_by']?.toString() ?? 'Unknown'}'),
                      ],
                    ),
                    trailing: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        _performProductRestore(
                          context,
                          product['product_id'] as int,
                          product['name']?.toString() ?? 'Unknown',
                        );
                      },
                      child: const Text('Restore'),
                    ),
                  ),
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (context.mounted) {
        _showDialog(context, 'Error', 'Failed to load deleted products: $e');
      }
    }
  }

  // Perform product restoration
  Future<void> _performProductRestore(BuildContext context, int productId, String productName) async {
    try {
      final error = await PyBridge().restoreProduct(productId: productId);
      
      if (error != null) {
        _showDialog(context, 'Error', error);
      } else {
        _showDialog(context, 'Success', 'Product "$productName" restored successfully!');
        _reloadProducts();
      }
    } catch (e) {
      _showDialog(context, 'Error', 'Failed to restore product: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Products')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _productsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          final products = snapshot.data ?? [];
          final filteredProducts = _productNameFilter.isEmpty
              ? products
              : products.where((p) => (p['name'] ?? '').toLowerCase().contains(_productNameFilter)).toList();

          return SafeArea(
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
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Expanded(
                              child: Text('Products', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                            ),
                            if (auth.role == "admin") ...[
                              ElevatedButton(
                                onPressed: () => _showRestoreProductsDialog(context),
                                style: ElevatedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  backgroundColor: Colors.orange,
                                  foregroundColor: Colors.white,
                                ),
                                child: const Text('Restore', style: TextStyle(fontSize: 12)),
                              ),
                              const SizedBox(width: 8),
                              ElevatedButton(
                                onPressed: () async {
                                  final result = await Navigator.pushNamed(context, '/add_product');
                                  if (result == true) {
                                    _reloadProducts();
                                  }
                                },
                                style: ElevatedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                ),
                                child: const Text('Add New', style: TextStyle(fontSize: 12)),
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          decoration: const InputDecoration(
                            labelText: 'Filter products by name',
                            prefixIcon: Icon(Icons.search),
                            isDense: true,
                          ),
                          onChanged: (v) => setState(() => _productNameFilter = v.trim().toLowerCase()),
                        ),
                        const SizedBox(height: 8),
                        // Scrollable DataTable
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: DataTable(
                            columns: const [
                              DataColumn(label: Text('Name')),
                              DataColumn(label: Text('Category')),
                              DataColumn(label: Text('Price')),
                              DataColumn(label: Text('Cost')),
                              DataColumn(label: Text('Profit')),
                              DataColumn(label: Text('Stock')),
                              DataColumn(label: Text('Toaster Space')),
                              DataColumn(label: Text('Actions')),
                            ],
                            rows: filteredProducts.map((product) {
                              final productId = product['product_id'] as int;
                              return DataRow(cells: [
                                DataCell(Text(product['name']?.toString() ?? '')),
                                DataCell(Text(product['category']?.toString() ?? '')),
                                DataCell(Text(product['price_per_unit']?.toString() ?? '')),
                                DataCell(Text(product['cost_per_unit']?.toString() ?? '')),
                                DataCell(Text(product['profit_per_unit']?.toString() ?? '')),
                                DataCell(Text(product['stock_quantity']?.toString() ?? '')),
                                DataCell(Text(product['toaster_space']?.toString() ?? '')),
                                DataCell(
                                  auth.role == 'admin'
                                      ? IconButton(
                                          icon: const Icon(Icons.delete, color: Colors.red),
                                          onPressed: () => _showProductDeletionDialog(
                                            context,
                                            productId,
                                            product['name']?.toString() ?? 'Unknown',
                                          ),
                                        )
                                      : const SizedBox.shrink(),
                                ),
                              ]);
                            }).toList(),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }

}
