import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';

import 'add_ingredients_page.dart';

class RestockIngredientsPage extends StatefulWidget {
  const RestockIngredientsPage({super.key});

  @override
  State<RestockIngredientsPage> createState() => _RestockIngredientsPageState();
}

class _RestockIngredientsPageState extends State<RestockIngredientsPage> {
  List<Map<String, dynamic>> ingredients = [];
  Set<String> removedIngredientNames = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchIngredients();
  }

  Future<void> _fetchIngredients() async {
    setState(() => _loading = true);
    final fetched = await PyBridge().getIngredients();
    setState(() {
      ingredients = fetched.map((i) => {
        'ingredient_id': i['ingredient_id'], // internal use only
        'name': i['name'],
        'restock': '',
        'removed': removedIngredientNames.contains(i['name']),
      }).toList();
      _loading = false;
    });
  }

  List<Map<String, dynamic>> get visibleIngredients =>
      ingredients.where((i) => !i['removed']).toList();
  List<Map<String, dynamic>> get removedIngredients =>
      ingredients.where((i) => i['removed']).toList();

  void _onRestockChanged(int realIndex, String val) {
    setState(() {
      ingredients[realIndex]['restock'] = val;
    });
  }

  void _onPriceChanged(int realIndex, String val) {
    setState(() {
      ingredients[realIndex]['price'] = val;
    });
  }


  void removeIngredient(int index) {
    setState(() {
      removedIngredientNames.add(ingredients[index]['name']);
      ingredients[index]['removed'] = true;
    });
  }

  void restoreIngredient(int index) {
    setState(() {
      removedIngredientNames.remove(ingredients[index]['name']);
      ingredients[index]['removed'] = false;
    });
  }

  Future<void> addNewIngredient() async {
    final beforeRemoved = Set<String>.from(removedIngredientNames);
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AddIngredientsPage(sourceRoute: '/restock_ingredients'),
      ),
    );
    // After returning, re-fetch ingredients and restore removed state
    setState(() {
      removedIngredientNames = beforeRemoved;
    });
    await _fetchIngredients();
  }

  bool get canSubmitRestock {
    if (visibleIngredients.isEmpty) return false;
    for (final i in visibleIngredients) {
      final val = i['restock'];
      if (val == null || val.toString().isEmpty) return false;
      final numVal = int.tryParse(val.toString());
      if (numVal == null || numVal <= 0) return false;
    }
    return true;
  }

  Future<void> submitRestock() async {
    // Only send id and restock to backend
    final restockData = visibleIngredients.map((i) => {
      'id': i['ingredient_id'],
      'restock': int.tryParse(i['restock'].toString()) ?? 0,
      'price': i['price'] != null ? double.tryParse(i['price'].toString()) : null,
    }).toList();
    try {
      final error = await PyBridge().restockIngredients(restockData);
      if (error == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Restock submitted!')),
        );
        setState(() {
          for (var i in ingredients) {
            i['restock'] = '';
          }
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to submit restock: $error')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to submit restock: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Restock Ingredients')),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : LayoutBuilder(
                builder: (context, constraints) {
                  return SingleChildScrollView(
                    padding: const EdgeInsets.all(16.0),
                    keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                    child: ConstrainedBox(
                      constraints: BoxConstraints(minHeight: constraints.maxHeight),
                      child: Column(
                        children: [
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: visibleIngredients.length,
                            itemBuilder: (context, idx) {
                              final ingredient = visibleIngredients[idx];
                              final realIndex = ingredients.indexOf(ingredient);
                              return ListTile(
                                title: Text(ingredient['name']),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    SizedBox(
                                      width: 80,
                                      child: TextField(
                                        decoration: const InputDecoration(
                                          labelText: 'Restock',
                                        ),
                                        keyboardType: TextInputType.number,
                                        onChanged: (val) => _onRestockChanged(realIndex, val),
                                      ),
                                    ),
                                    SizedBox(
                                      width: 80,
                                      child: TextField(
                                        decoration: const InputDecoration(
                                          labelText: 'Price',
                                        ),
                                        keyboardType: TextInputType.number,
                                        onChanged: (val) => _onPriceChanged(realIndex, val),
                                      ),
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.close),
                                      onPressed: () => removeIngredient(realIndex),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                          if (removedIngredients.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 8.0),
                              child: Wrap(
                                spacing: 8,
                                children: [
                                  const Text('Restore:'),
                                  ...removedIngredients.map((ingredient) {
                                    final realIndex = ingredients.indexOf(ingredient);
                                    return ActionChip(
                                      label: Text(ingredient['name']),
                                      onPressed: () => restoreIngredient(realIndex),
                                    );
                                  }).toList(),
                                ],
                              ),
                            ),
                          Padding(
                            padding: const EdgeInsets.only(top: 16.0, bottom: 8.0),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                              children: [
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.add),
                                  label: const Text('Add New Ingredient'),
                                  onPressed: addNewIngredient,
                                ),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.check),
                                  label: const Text('Submit Restock'),
                                  onPressed: canSubmitRestock ? submitRestock : null,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
      ),
    );
  }

}
