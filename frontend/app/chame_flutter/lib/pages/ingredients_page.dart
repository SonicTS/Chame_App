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
  late Future<List<Map<String, dynamic>>> _stockHistoryFuture;
  String _ingredientNameFilter = '';
  String _stockHistoryFilter = '';
  int? _selectedIngredientId;
  final ScrollController _mainScrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _ingredientsFuture = PyBridge().getIngredients();
    _stockHistoryFuture = PyBridge().getStockHistory();
  }

  void _reloadIngredients() {
    setState(() {
      _ingredientsFuture = PyBridge().getIngredients();
      _stockHistoryFuture = PyBridge().getStockHistory();
    });
  }

  void _filterStockHistory() {
    setState(() {
      _stockHistoryFuture = PyBridge().getStockHistory(ingredientId: _selectedIngredientId);
    });
  }

  @override
  void dispose() {
    _mainScrollController.dispose();
    super.dispose();
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

  // Show stock update dialog
  void _showStockUpdateDialog(BuildContext context, int ingredientId, String ingredientName, String currentStock) {
    final TextEditingController stockController = TextEditingController(text: currentStock);
    final TextEditingController commentController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Update Stock: $ingredientName'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: stockController,
              decoration: const InputDecoration(
                labelText: 'New Stock Amount',
                hintText: 'Enter new stock quantity',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              onChanged: (value) {
                if (value.isNotEmpty) {
                  // Show comment field when user starts typing
                  commentController.text = commentController.text.isEmpty ? 'Stock updated via Flutter admin' : commentController.text;
                }
              },
            ),
            const SizedBox(height: 16),
            TextField(
              controller: commentController,
              decoration: const InputDecoration(
                labelText: 'Comment (optional)',
                hintText: 'Reason for stock update',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final newStock = int.tryParse(stockController.text);
              if (newStock == null || newStock < 0) {
                _showDialog(context, 'Error', 'Please enter a valid stock amount (0 or greater)');
                return;
              }
              
              Navigator.pop(ctx);
              _performStockUpdate(context, ingredientId, ingredientName, newStock, commentController.text);
            },
            child: const Text('Update'),
          ),
        ],
      ),
    );
  }

  // Perform stock update
  Future<void> _performStockUpdate(BuildContext context, int ingredientId, String ingredientName, int newStock, String comment) async {
    try {
      final error = await PyBridge().updateStock(
        ingredientId: ingredientId,
        amount: newStock,
        comment: comment.isEmpty ? 'Stock updated via Flutter admin' : comment,
      );
      
      if (error != null) {
        _showDialog(context, 'Error', 'Failed to update stock: $error');
      } else {
        _showDialog(context, 'Success', 'Stock for "$ingredientName" updated to $newStock successfully!');
        _reloadIngredients();
      }
    } catch (e) {
      _showDialog(context, 'Error', 'Failed to update stock: $e');
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
                controller: _mainScrollController,
                padding: const EdgeInsets.all(16.0),
                keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                physics: _CoordinatedScrollPhysics(
                  mainController: _mainScrollController,
                ),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Ingredients section
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
                        physics: _CoordinatedScrollPhysics(
                          mainController: _mainScrollController,
                        ),
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
                              DataCell(
                                auth.role == 'admin'
                                    ? GestureDetector(
                                        onTap: () => _showStockUpdateDialog(
                                          context,
                                          ingredientId,
                                          ingredient['name']?.toString() ?? 'Unknown',
                                          ingredient['stock_quantity']?.toString() ?? '0',
                                        ),
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            border: Border.all(color: Colors.grey.shade300),
                                            borderRadius: BorderRadius.circular(4),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Text(ingredient['stock_quantity']?.toString() ?? '0'),
                                              const SizedBox(width: 4),
                                              const Icon(Icons.edit, size: 12, color: Colors.grey),
                                            ],
                                          ),
                                        ),
                                      )
                                    : Text(ingredient['stock_quantity']?.toString() ?? '0'),
                              ),
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
                      
                      // Stock History section
                      const SizedBox(height: 32),
                      const Text('Stock History', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 16),
                      
                      // Stock History Filter
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              decoration: const InputDecoration(
                                labelText: 'Filter stock history by ingredient name',
                                prefixIcon: Icon(Icons.search),
                                isDense: true,
                              ),
                              onChanged: (v) => setState(() => _stockHistoryFilter = v.trim().toLowerCase()),
                            ),
                          ),
                          const SizedBox(width: 16),
                          ElevatedButton(
                            onPressed: () {
                              setState(() {
                                _selectedIngredientId = null;
                                _stockHistoryFilter = '';
                              });
                              _filterStockHistory();
                            },
                            child: const Text('Show All'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      
                      // Stock History Table
                      FutureBuilder<List<Map<String, dynamic>>>(
                        future: _stockHistoryFuture,
                        builder: (context, snapshot) {
                          if (snapshot.connectionState == ConnectionState.waiting) {
                            return const Center(child: CircularProgressIndicator());
                          }
                          if (snapshot.hasError) {
                            return Center(child: Text('Error loading stock history: ${snapshot.error}'));
                          }
                          
                          final stockHistory = snapshot.data ?? [];
                          final filteredStockHistory = _stockHistoryFilter.isEmpty
                              ? stockHistory
                              : stockHistory.where((history) {
                                  final ingredientName = history['ingredient_name']?.toString().toLowerCase() ?? '';
                                  return ingredientName.contains(_stockHistoryFilter);
                                }).toList();
                          
                          if (filteredStockHistory.isEmpty) {
                            return const Center(
                              child: Padding(
                                padding: EdgeInsets.all(16.0),
                                child: Text('No stock history found'),
                              ),
                            );
                          }
                          
                          return SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            physics: _CoordinatedScrollPhysics(
                              mainController: _mainScrollController,
                            ),
                            child: DataTable(
                              columns: const [
                                DataColumn(label: Text('Ingredient')),
                                DataColumn(label: Text('Amount Changed')),
                                DataColumn(label: Text('Date')),
                                DataColumn(label: Text('Comment')),
                                DataColumn(label: Text('Actions')),
                              ],
                              rows: filteredStockHistory.map((history) {
                                final ingredientId = history['ingredient_id'] as int?;
                                final ingredientName = history['ingredient_name']?.toString() ?? 'Unknown';
                                final amount = history['amount']?.toString() ?? '0';
                                final timestamp = history['timestamp']?.toString().split('T')[0] ?? 'N/A';
                                final comment = history['comment']?.toString() ?? 'No comment';
                                
                                return DataRow(cells: [
                                  DataCell(Text(ingredientName)),
                                  DataCell(
                                    Text(
                                      amount,
                                      style: TextStyle(
                                        color: (history['amount'] ?? 0) > 0 ? Colors.green : Colors.red,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  DataCell(Text(timestamp)),
                                  DataCell(
                                    SizedBox(
                                      width: 200,
                                      child: Text(
                                        comment,
                                        overflow: TextOverflow.ellipsis,
                                        maxLines: 2,
                                      ),
                                    ),
                                  ),
                                  DataCell(
                                    ingredientId != null
                                        ? IconButton(
                                            icon: const Icon(Icons.filter_list, color: Colors.blue),
                                            onPressed: () {
                                              setState(() {
                                                _selectedIngredientId = ingredientId;
                                              });
                                              _filterStockHistory();
                                            },
                                            tooltip: 'Filter by this ingredient',
                                          )
                                        : const SizedBox.shrink(),
                                  ),
                                ]);
                              }).toList(),
                            ),
                          );
                        },
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
    return super.applyPhysicsToUserOffset(position, offset);
  }

  @override
  Simulation? createBallisticSimulation(ScrollMetrics position, double velocity) {
    return super.createBallisticSimulation(position, velocity);
  }
}
