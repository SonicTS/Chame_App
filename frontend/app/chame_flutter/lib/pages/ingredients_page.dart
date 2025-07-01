import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/widgets/simple_deletion_dialog.dart';
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

  // Show simplified deletion dialog for ingredients
  void _showIngredientDeletionDialog(BuildContext context, int ingredientId, String ingredientName) async {
    final result = await showSimpleDeletionDialog(
      context: context,
      entityType: 'ingredient',
      entityId: ingredientId,
      entityName: ingredientName,
      deletedBy: 'flutter_admin',
    );
    
    if (result == true) {
      // Deletion was successful, reload the ingredients
      _reloadIngredients();
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

  // Show restore dialog with deleted ingredients
  void _showRestoreIngredientsDialog(BuildContext context) async {
    try {
      final deletedIngredients = await PyBridge().getDeletedIngredients();
      
      if (!context.mounted) return;
      
      if (deletedIngredients.isEmpty) {
        _showDialog(context, 'No Deleted Ingredients', 'There are no deleted ingredients to restore.');
        return;
      }

      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Restore Deleted Ingredients'),
          content: SizedBox(
            width: double.maxFinite,
            height: 400,
            child: ListView.builder(
              itemCount: deletedIngredients.length,
              itemBuilder: (context, index) {
                final ingredient = deletedIngredients[index];
                return Card(
                  child: ListTile(
                    title: Text(ingredient['name']?.toString() ?? 'Unknown'),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Price: ${ingredient['price_per_unit']?.toString() ?? 'N/A'}'),
                        Text('Stock: ${ingredient['stock_quantity']?.toString() ?? 'N/A'}'),
                        Text('Deleted: ${ingredient['deleted_at']?.toString().split('T')[0] ?? 'N/A'}'),
                        Text('By: ${ingredient['deleted_by']?.toString() ?? 'Unknown'}'),
                      ],
                    ),
                    trailing: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        _performIngredientRestore(
                          context,
                          ingredient['ingredient_id'] as int,
                          ingredient['name']?.toString() ?? 'Unknown',
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
        _showDialog(context, 'Error', 'Failed to load deleted ingredients: $e');
      }
    }
  }

  // Perform ingredient restoration
  Future<void> _performIngredientRestore(BuildContext context, int ingredientId, String ingredientName) async {
    try {
      final error = await PyBridge().restoreIngredient(ingredientId: ingredientId);
      
      if (error != null) {
        _showDialog(context, 'Error', 'Failed to restore ingredient: $error');
      } else {
        _showDialog(context, 'Success', 'Ingredient "$ingredientName" restored successfully!');
        _reloadIngredients();
      }
    } catch (e) {
      _showDialog(context, 'Error', 'Failed to restore ingredient: $e');
    }
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
                          const Expanded(
                            child: Text('Ingredients', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                          ),
                          if (auth.role == 'admin')
                            Wrap(
                              spacing: 8,
                              children: [
                                ElevatedButton(
                                  onPressed: () => _showRestoreIngredientsDialog(context),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.orange,
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  ),
                                  child: const Text('Restore', style: TextStyle(color: Colors.white, fontSize: 12)),
                                ),
                                ElevatedButton(
                                  onPressed: () async {
                                    final result = await Navigator.pushNamed(context, '/add_ingredients');
                                    if (result == true) {
                                      _reloadIngredients();
                                    }
                                  },
                                  style: ElevatedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  ),
                                  child: const Text('Add New', style: TextStyle(fontSize: 12)),
                                ),
                              ],
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
                            DataColumn(label: Text('Actions')),
                          ],
                          rows: filteredIngredients.map((ingredient) {
                            final ingredientId = ingredient['ingredient_id'] as int;
                            return DataRow(cells: [
                              DataCell(Text(ingredient['name']?.toString() ?? '')),
                              DataCell(Text(ingredient['price_per_package']?.toString() ?? '')),
                              DataCell(Text(ingredient['number_of_units']?.toString() ?? '')),
                              DataCell(Text(ingredient['price_per_unit']?.toString() ?? '')),
                              DataCell(Text(ingredient['stock_quantity']?.toString() ?? '')),
                              DataCell(Text(ingredient['pfand']?.toString() ?? '')),
                              DataCell(
                                auth.role == 'admin'
                                    ? IconButton(
                                        icon: const Icon(Icons.delete, color: Colors.red),
                                        onPressed: () => _showIngredientDeletionDialog(
                                          context,
                                          ingredientId,
                                          ingredient['name']?.toString() ?? 'Unknown',
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
          );
        },
      ),
    );
  }

}
