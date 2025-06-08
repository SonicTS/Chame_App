import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';

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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Products')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _productsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: \\${snapshot.error}'));
          }
          final products = snapshot.data ?? [];
          final filteredProducts = _productNameFilter.isEmpty
              ? products
              : products.where((p) => (p['name'] ?? '').toLowerCase().contains(_productNameFilter)).toList();
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Products', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                    ElevatedButton(
                      onPressed: () async {
                        final result = await Navigator.pushNamed(context, '/add_product');
                        if (result == true) {
                          _reloadProducts();
                        }
                      },
                      child: const Text('Add a New Product'),
                    ),
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
                Expanded(
                  child: SingleChildScrollView(
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
                      ],
                      rows: filteredProducts.map((product) {
                        return DataRow(cells: [
                          DataCell(Text(product['name']?.toString() ?? '')),
                          DataCell(Text(product['category']?.toString() ?? '')),
                          DataCell(Text(product['price_per_unit']?.toString() ?? '')),
                          DataCell(Text(product['cost_per_unit']?.toString() ?? '')),
                          DataCell(Text(product['profit_per_unit']?.toString() ?? '')),
                          DataCell(Text(product['stock_quantity']?.toString() ?? '')),
                          DataCell(Text(product['toaster_space']?.toString() ?? '')),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
