// lib/data/py_bridge.dart
import 'dart:convert';
import 'package:flutter/services.dart';

class PyBridge {
  static const _chan = MethodChannel('samples.flutter.dev/chame/python');

  Future<void> ping() async => _chan.invokeMethod('ping');

  Future<List<Map<String, dynamic>>> getIngredients() async {
    try {
      final result = await _chan.invokeMethod('get_all_ingredients');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      // result is a JSON string
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getIngredients: '
          '\x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<String?> addIngredient({
    required String name,
    required double price,
    required int numberIngredients,
    required int stock,
  }) async {
    print('Adding ingredient: name=$name, price=$price, numberIngredients=$numberIngredients, stock=$stock');
    try {
      await _chan.invokeMethod('add_ingredient', {
        'name': name,
        'price_per_package': price,
        'number_ingredients': numberIngredients,
        'stock_quantity': stock,
      });
      print('Ingredient added successfully');
      return null; // Success, no error
    } catch (e) {
      // Return error message as string
      return e.toString();
    }
  }

  Future<String?> addUser({
    required String name,
    required double balance,
    required String role,
  }) async {
    try {
      await _chan.invokeMethod('add_user', {
        'name': name,
        'balance': balance,
        'role': role,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> withdraw({
    required int userId,
    required double amount,
  }) async {
    try {
      await _chan.invokeMethod('withdraw', {
        'user_id': userId,
        'amount': amount,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> deposit({
    required int userId,
    required double amount,
  }) async {
    try {
      await _chan.invokeMethod('deposit', {
        'user_id': userId,
        'amount': amount,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> addProduct({
    required String name,
    required String category,
    required double price,
    required List<int> ingredientsIds,
    required List<double> quantities,
    required int toasterSpace,
  }) async {
    try {
      await _chan.invokeMethod('add_product', {
        'name': name,
        'category': category,
        'price': price,
        'ingredients_ids': ingredientsIds,
        'quantities': quantities,
        'toaster_space': toasterSpace,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> restockIngredient({
    required int ingredientId,
    required int quantity,
  }) async {
    try {
      await _chan.invokeMethod('restock_ingredient', {
        'ingredient_id': ingredientId,
        'quantity': quantity,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> makePurchase({
    required int userId,
    required int productId,
    required int quantity,
  }) async {
    try {
      await _chan.invokeMethod('make_purchase', {
        'user_id': userId,
        'product_id': productId,
        'quantity': quantity,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> addToastRound({
    required List<int> productIds,
    required List<int> userSelections,
  }) async {
    try {
      await _chan.invokeMethod('add_toast_round', {
        'product_ids': productIds,
        'user_selections': userSelections,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> bankWithdraw({
    required double amount,
    required String description,
  }) async {
    try {
      await _chan.invokeMethod('bank_withdraw', {
        'amount': amount,
        'description': description,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<List<Map<String, dynamic>>> getAllUsers() async {
    try {
      final result = await _chan.invokeMethod('get_all_users');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getAllUsers: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getAllProducts() async {
    try {
      final result = await _chan.invokeMethod('get_all_products');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getAllProducts: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getAllSales() async {
    try {
      final result = await _chan.invokeMethod('get_all_sales');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getAllSales: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getAllToastProducts() async {
    try {
      final result = await _chan.invokeMethod('get_all_toast_products');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getAllToastProducts: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getAllToastRounds() async {
    try {
      final result = await _chan.invokeMethod('get_all_toast_rounds');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getAllToastRounds: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getFilteredTransaction({
    String userId = 'all',
    String txType = 'all',
  }) async {
    try {
      final result = await _chan.invokeMethod('get_filtered_transaction', {
        'user_id': userId,
        'tx_type': txType,
      });
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getFilteredTransaction: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<Map<String, dynamic>?> getBank() async {
    try {
      final result = await _chan.invokeMethod('get_bank');
      if (result == null || result == 'null') return null;
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in getBank: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getBankTransaction() async {
    try {
      final result = await _chan.invokeMethod('get_bank_transaction');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getBankTransaction: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }
}
