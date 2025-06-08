import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';

// Placeholder for the pybridge call. Replace with actual implementation later.
Future<String?> addIngredientViaPyBridge({
  required String name,
  required double price,
  required int numberIngredients,
  required int stock,
}) async {
  // TODO: Implement actual call to pybridge
  final error = await PyBridge().addIngredient(
    name: name,
    price: price,
    numberIngredients: numberIngredients,
    stock: stock,
  );
  return error; // return error message if any, null if success
}

class AddIngredientsPage extends StatefulWidget {
  const AddIngredientsPage({super.key});

  @override
  State<AddIngredientsPage> createState() => _AddIngredientsPageState();
}

class _AddIngredientsPageState extends State<AddIngredientsPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final _numberIngredientsController = TextEditingController();
  final _stockController = TextEditingController();
  double _pricePerUnit = 0.0;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _priceController.addListener(_updatePricePerUnit);
    _numberIngredientsController.addListener(_updatePricePerUnit);
  }

  void _updatePricePerUnit() {
    final price = double.tryParse(_priceController.text) ?? 0.0;
    final num = int.tryParse(_numberIngredientsController.text) ?? 0;
    setState(() {
      _pricePerUnit = (num > 0) ? price / num : 0.0;
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _priceController.dispose();
    _numberIngredientsController.dispose();
    _stockController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);
    final error = await addIngredientViaPyBridge(
      name: _nameController.text.trim(),
      price: double.parse(_priceController.text),
      numberIngredients: int.parse(_numberIngredientsController.text),
      stock: int.tryParse(_stockController.text) ?? 0,
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
          content: const Text('Ingredient added successfully!'),
          actions: [TextButton(onPressed: () {
            Navigator.pop(ctx);
            Navigator.pop(context, true); // Pop and signal reload
          }, child: const Text('OK'))],
        ),
      );
      _formKey.currentState!.reset();
      _nameController.clear();
      _priceController.clear();
      _numberIngredientsController.clear();
      _stockController.clear();
      setState(() => _pricePerUnit = 0.0);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Ingredient')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Center(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(labelText: 'Ingredient Name'),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _priceController,
                  decoration: const InputDecoration(labelText: 'Price per Package'),
                  keyboardType: TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    final val = double.tryParse(v ?? '');
                    if (val == null || val < 0) return 'Enter valid price';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _numberIngredientsController,
                  decoration: const InputDecoration(labelText: 'Ingredients in Package'),
                  keyboardType: TextInputType.number,
                  validator: (v) {
                    final val = int.tryParse(v ?? '');
                    if (val == null || val <= 0) return 'Enter valid number';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _stockController,
                  decoration: const InputDecoration(labelText: 'Stock'),
                  keyboardType: TextInputType.number,
                  validator: (v) {
                    if (v == null || v.isEmpty) return null;
                    final val = int.tryParse(v);
                    if (val == null || val < 0) return 'Enter valid stock';
                    return null;
                  },
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  child: _isSubmitting
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Add Ingredient'),
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Price per Unit:', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(width: 8),
                    Container(
                      margin: const EdgeInsets.only(top: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(_pricePerUnit.toStringAsFixed(2), style: const TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
