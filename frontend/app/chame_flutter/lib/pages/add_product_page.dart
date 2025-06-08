import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:dropdown_search/dropdown_search.dart';
import 'package:collection/collection.dart';

class AddProductPage extends StatefulWidget {
  const AddProductPage({super.key});

  @override
  State<AddProductPage> createState() => _AddProductPageState();
}

class _AddProductPageState extends State<AddProductPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final List<_SelectedIngredient> _selectedIngredients = [];
  String _category = 'raw';
  int? _toasterSpace;
  bool _isSubmitting = false;
  List<Map<String, dynamic>> _ingredients = [];
  int? _ingredientId;
  double? _ingredientQty;
  double _currentCost = 0.0;

  @override
  void initState() {
    super.initState();
    _fetchIngredients();
  }

  Future<void> _fetchIngredients() async {
    final ingredients = await PyBridge().getIngredients();
    setState(() {
      _ingredients = ingredients;
      if (_ingredients.isNotEmpty) {
        _ingredientId = _ingredients.first['ingredient_id'];
      }
    });
  }

  void _addIngredient() {
    if (_ingredientId == null || _ingredientQty == null || _ingredientQty! < 0) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Error'),
          content: const Text('Please enter a valid quantity.'),
          actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))],
        ),
      );
      return;
    }
    if (_selectedIngredients.any((i) => i.ingredientId == _ingredientId)) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Error'),
          content: const Text('This ingredient is already added.'),
          actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))],
        ),
      );
      return;
    }
    final ingredient = _ingredients.firstWhere((i) => i['ingredient_id'] == _ingredientId);
    setState(() {
      _selectedIngredients.add(_SelectedIngredient(
        ingredientId: _ingredientId!,
        name: ingredient['name'] ?? '',
        quantity: _ingredientQty!,
        costPerUnit: (ingredient['price_per_unit'] as num?)?.toDouble() ?? 0.0,
      ));
      _currentCost = _calculateCurrentCost();
    });
  }

  void _removeIngredient(int ingredientId) {
    setState(() {
      _selectedIngredients.removeWhere((i) => i.ingredientId == ingredientId);
      _currentCost = _calculateCurrentCost();
    });
  }

  double _calculateCurrentCost() {
    double total = 0.0;
    for (final i in _selectedIngredients) {
      total += i.costPerUnit * i.quantity;
    }
    return total;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedIngredients.isEmpty) return;
    setState(() => _isSubmitting = true);
    final error = await PyBridge().addProduct(
      name: _nameController.text.trim(),
      category: _category,
      price: double.parse(_priceController.text),
      ingredientsIds: _selectedIngredients.map((e) => e.ingredientId).toList(),
      quantities: _selectedIngredients.map((e) => e.quantity.toDouble()).toList(),
      toasterSpace: _category == 'toast' ? (_toasterSpace ?? 1) : 1,
    );
    setState(() => _isSubmitting = false);
    if (error != null) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Error'),
          content: Text(error),
          actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))],
        ),
      );
    } else {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Success'),
          content: const Text('Product added successfully!'),
          actions: [TextButton(onPressed: () {
            Navigator.pop(ctx);
            Navigator.pop(context, true);
          }, child: const Text('OK'))],
        ),
      );
      _formKey.currentState!.reset();
      _nameController.clear();
      _priceController.clear();
      setState(() {
        _selectedIngredients.clear();
        _category = 'raw';
        _toasterSpace = null;
        _currentCost = 0.0;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Product')),
      body: _ingredients.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextFormField(
                      controller: _nameController,
                      decoration: const InputDecoration(labelText: 'Product Name'),
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        const Text('Category:'),
                        const SizedBox(width: 12),
                        DropdownButton<String>(
                          value: _category,
                          items: const [
                            DropdownMenuItem(value: 'raw', child: Text('Raw')),
                            DropdownMenuItem(value: 'toast', child: Text('Toast')),
                          ],
                          onChanged: (val) {
                            setState(() {
                              _category = val!;
                            });
                          },
                        ),
                        if (_category == 'toast') ...[
                          const SizedBox(width: 24),
                          SizedBox(
                            width: 120,
                            child: TextFormField(
                              decoration: const InputDecoration(labelText: 'Toaster Space'),
                              keyboardType: TextInputType.number,
                              onChanged: (v) => _toasterSpace = int.tryParse(v),
                              validator: (v) {
                                if (_category == 'toast') {
                                  final val = int.tryParse(v ?? '');
                                  if (val == null || val < 1) return 'Enter valid space';
                                }
                                return null;
                              },
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _priceController,
                      decoration: const InputDecoration(labelText: 'Price per Unit'),
                      keyboardType: TextInputType.numberWithOptions(decimal: true),
                      validator: (v) {
                        final val = double.tryParse(v ?? '');
                        if (val == null || val < 0) return 'Enter valid price';
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),
                    const Text('Select Ingredients', style: TextStyle(fontWeight: FontWeight.bold)),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          SizedBox(
                            width: 220,
                            child: DropdownSearch<Map<String, dynamic>>(
                              items: (String? filter, _) {
                                final filtered = filter == null || filter.isEmpty
                                    ? _ingredients
                                    : _ingredients.where((i) => (i['name'] ?? '').toLowerCase().contains(filter.toLowerCase())).toList();
                                return Future.value(filtered);
                              },
                              selectedItem: _ingredients.firstWhereOrNull((i) => i['ingredient_id'] == _ingredientId),
                              itemAsString: (i) => i['name'] ?? '',
                              compareFn: (a, b) => a['ingredient_id'] == b['ingredient_id'],
                              onChanged: (val) => setState(() => _ingredientId = val?['ingredient_id'] as int?),
                              popupProps: const PopupProps.menu(
                                showSearchBox: true,
                              ),
                              decoratorProps: const DropDownDecoratorProps(
                                decoration: InputDecoration(labelText: 'Ingredient'),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          SizedBox(
                            width: 80,
                            child: TextFormField(
                              decoration: const InputDecoration(labelText: 'Quantity'),
                              keyboardType: TextInputType.number,
                              onChanged: (v) => _ingredientQty = double.tryParse(v),
                            ),
                          ),
                          const SizedBox(width: 12),
                          ElevatedButton(
                            onPressed: _addIngredient,
                            child: const Text('Add Ingredient'),
                          ),
                          const SizedBox(width: 24),
                          Text('Current Cost: ${_currentCost.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text('Selected Ingredients', style: TextStyle(fontWeight: FontWeight.bold)),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: DataTable(
                        columns: const [
                          DataColumn(label: Text('Ingredient')),
                          DataColumn(label: Text('Quantity')),
                          DataColumn(label: Text('Action')),
                        ],
                        rows: _selectedIngredients.map((i) {
                          return DataRow(cells: [
                            DataCell(Text(i.name)),
                            DataCell(Text(i.quantity.toString())),
                            DataCell(IconButton(
                              icon: const Icon(Icons.delete),
                              onPressed: () => _removeIngredient(i.ingredientId),
                            )),
                          ]);
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Center(
                      child: ElevatedButton(
                        onPressed: _isSubmitting ? null : _submit,
                        child: _isSubmitting
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Text('Add Product'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}

class _SelectedIngredient {
  final int ingredientId;
  final String name;
  final double quantity;
  final double costPerUnit;
  _SelectedIngredient({
    required this.ingredientId,
    required this.name,
    required this.quantity,
    required this.costPerUnit,
  });
}
