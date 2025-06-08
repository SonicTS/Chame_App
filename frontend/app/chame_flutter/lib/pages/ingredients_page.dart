import 'package:chame_flutter/data/py_bride.dart';
import 'package:flutter/material.dart';

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
    return Scaffold(
      appBar: AppBar(title: const Text('Ingredients')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _ingredientsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: \\${snapshot.error}'));
          }
          final ingredients = snapshot.data ?? [];
          final filteredIngredients = _ingredientNameFilter.isEmpty
              ? ingredients
              : ingredients.where((i) => (i['name'] ?? '').toLowerCase().contains(_ingredientNameFilter)).toList();
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Ingredient', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
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
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('Name')),
                        DataColumn(label: Text('Price per package')),
                        DataColumn(label: Text('Ingredients in package')),
                        DataColumn(label: Text('Price per unit')),
                        DataColumn(label: Text('Stock')),
                        DataColumn(label: Text('Restock')),
                      ],
                      rows: filteredIngredients.map((ingredient) {
                        return DataRow(cells: [
                          DataCell(Text(ingredient['name']?.toString() ?? '')),
                          DataCell(Text(ingredient['price_per_package']?.toString() ?? '')),
                          DataCell(Text(ingredient['number_of_units']?.toString() ?? '')),
                          DataCell(Text(ingredient['price_per_unit']?.toString() ?? '')),
                          DataCell(Text(ingredient['stock_quantity']?.toString() ?? '')),
                          DataCell(_RestockButton(
                            ingredientId: ingredient['ingredient_id'] is int ? ingredient['ingredient_id'] : int.tryParse(ingredient['ingredient_id']?.toString() ?? '0') ?? 0,
                            onRestocked: _reloadIngredients,
                          )),
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

class _RestockButton extends StatelessWidget {
  final int ingredientId;
  final VoidCallback onRestocked;
  const _RestockButton({required this.ingredientId, required this.onRestocked});

  @override
  Widget build(BuildContext context) {
    final controller = TextEditingController();
    return Row(
      children: [
        SizedBox(
          width: 60,
          child: TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              hintText: 'Qty',
              isDense: true,
              contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 8),
            ),
          ),
        ),
        const SizedBox(width: 8),
        ElevatedButton(
          onPressed: () async {
            final qty = int.tryParse(controller.text);
            if (qty == null || qty <= 0) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Enter a valid quantity')),
              );
              return;
            }
            final error = await PyBridge().restockIngredient(
              ingredientId: ingredientId,
              quantity: qty,
            );
            if (error == null) {
              onRestocked();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Restocked ingredient $ingredientId with $qty units')),
              );
            } else {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Error: $error')),
              );
            }
          },
          child: const Text('Restock'),
        ),
      ],
    );
  }
}
