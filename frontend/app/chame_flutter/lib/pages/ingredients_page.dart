import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class IngredientsPage extends StatefulWidget {
  const IngredientsPage({super.key});

  @override
  State<IngredientsPage> createState() => _IngredientsPageState();
}

class _IngredientsPageState extends State<IngredientsPage> {
  late Future<List<Map<String, dynamic>>> _ingredientsFuture;
  String _ingredientNameFilter = '';

  @override
  void initState() {
    super.initState();
    _ingredientsFuture = PyBridge().getIngredients();
  }

  void _reloadIngredients() {
    setState(() {
      _ingredientsFuture = PyBridge().getIngredients();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Ingredients')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _ingredientsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          final ingredients = snapshot.data ?? [];
          final filteredIngredients = _ingredientNameFilter.isEmpty
              ? ingredients
              : ingredients.where((i) => (i['name'] ?? '').toLowerCase().contains(_ingredientNameFilter)).toList();

          return LayoutBuilder(
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
                          const Text('Ingredient', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                          if (auth.role == 'admin')
                            ElevatedButton(
                              onPressed: () async {
                                final result = await Navigator.pushNamed(context, '/add_ingredients');
                                if (result == true) {
                                  _reloadIngredients();
                                }
                              },
                              child: const Text('Add a New Ingredient'),
                            ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        decoration: const InputDecoration(
                          labelText: 'Filter ingredients by name',
                          prefixIcon: Icon(Icons.search),
                          isDense: true,
                        ),
                        onChanged: (v) => setState(() => _ingredientNameFilter = v.trim().toLowerCase()),
                      ),
                      const SizedBox(height: 8),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: DataTable(
                          columns: const [
                            DataColumn(label: Text('Name')),
                            DataColumn(label: Text('Price per package')),
                            DataColumn(label: Text('Ingredients in package')),
                            DataColumn(label: Text('Price per unit')),
                            DataColumn(label: Text('Stock')),
                            DataColumn(label: Text('Pfand')),
                          ],
                          rows: filteredIngredients.map((ingredient) {
                            return DataRow(cells: [
                              DataCell(Text(ingredient['name']?.toString() ?? '')),
                              DataCell(Text(ingredient['price_per_package']?.toString() ?? '')),
                              DataCell(Text(ingredient['number_of_units']?.toString() ?? '')),
                              DataCell(Text(ingredient['price_per_unit']?.toString() ?? '')),
                              DataCell(Text(ingredient['stock_quantity']?.toString() ?? '')),
                              DataCell(Text(ingredient['pfand']?.toString() ?? '')),
                            ]);
                          }).toList(),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

}
