// lib/data/py_bridge.dart
import 'dart:convert';
import 'dart:ffi';
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

  Future<void> changePassword({
    required String user_id,
    required String oldPassword,
    required String newPassword,
  }) async {
    try {
      final result = await _chan.invokeMethod('change_password', {
        'user_id': int.parse(user_id),
        'old_password': oldPassword,
        'new_password': newPassword,
      });
    } catch (e, stack) {
      print('Error in changePassword: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<Map<String, dynamic>?> login({
    required String username,
    required String password,
  }) async {
    try {
      final result = await _chan.invokeMethod('login', {
        'user': username,
        'password': password,
      });
      if (result == null || result == 'null') return null;
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in login: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      if (e is PlatformException && e.message != null) {
        throw Exception(e.message);
      }
      throw Exception('Login failed: $e');
    }
  }



  Future<String?> addIngredient({
    required String name,
    required double price,
    required int numberIngredients,
    required double pfand,
    required int stock,
  }) async {
    print('Adding ingredient: name=$name, price=$price, numberIngredients=$numberIngredients, pfand=$pfand, stock=$stock');
    try {
      await _chan.invokeMethod('add_ingredient', {
        'name': name,
        'price_per_package': price,
        'number_ingredients': numberIngredients,
        'pfand': pfand,
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
    required String? password,
  }) async {
    try {
      await _chan.invokeMethod('add_user', {
        'name': name,
        'balance': balance,
        'role': role,
        'password': password,
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> changeUserRole({
    required int userId,
    required String newRole,
  }) async {
    try {
      await _chan.invokeMethod('change_user_role', {
        'user_id': userId,
        'new_role': newRole,
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

  Future<String?> makeMultiplePurchases({
    required List<Map<String, dynamic>> itemList,
  }) async {
    try {
      await _chan.invokeMethod('make_multiple_purchases', {
        'item_list': jsonEncode(itemList),
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<String?> addToastRound({
    required List<int> productIds,
    required List<int> consumer_selections,
    required List<int> donator_selections,
  }) async {
    try {
      await _chan.invokeMethod('add_toast_round', {
        'product_ids': productIds,
        'consumer_selections': consumer_selections,
        'donator_selections': donator_selections,
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

  Future<List<Map<String, dynamic>>> getAllRawProducts() async {
    try {
      final result = await _chan.invokeMethod('get_all_raw_products');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getAllRawProducts: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
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

  Future<String?> restockIngredients(List<Map<String, dynamic>> restocks) async {
    // restocks: [{ 'name': ..., 'restock': ... }, ...]
    try {
      await _chan.invokeMethod('restock_ingredients', {
        'restocks': jsonEncode(restocks),
      });
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  Future<void> submitPfandReturn(
    int userId,
    List<Map<String, dynamic>> products,
  ) async {
    try {
      await _chan.invokeMethod('submit_pfand_return', {
        'user_id': userId,
        'product_list': jsonEncode(products),
      });
    } catch (e) {
      print('Error in submitPfandReturn: \x1b[31m$e\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getPfandHistory() async {
    try {
      final result = await _chan.invokeMethod('get_pfand_history');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in getPfandHistory: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  // ========== BACKUP MANAGEMENT METHODS ==========

  Future<Map<String, dynamic>> createBackup({
    String backupType = "manual",
    String description = "",
    String createdBy = "flutter_admin",
  }) async {
    try {
      final result = await _chan.invokeMethod('create_backup', {
        'backup_type': backupType,
        'description': description,
        'created_by': createdBy,
      });
      if (result == null || result == 'null') {
        throw Exception('Failed to create backup: No response from backend');
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in createBackup: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> listBackups() async {
    try {
      final result = await _chan.invokeMethod('list_backups');
      if (result == null || result == 'null') {
        return <Map<String, dynamic>>[];
      }
      final List<dynamic> decoded = jsonDecode(result as String);
      return decoded.cast<Map<String, dynamic>>();
    } catch (e, stack) {
      print('Error in listBackups: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> restoreBackup({
    required String backupPath,
    required bool confirm,
  }) async {
    try {
      final result = await _chan.invokeMethod('restore_backup', {
        'backup_path': backupPath,
        'confirm': confirm,
      });
      if (result == null || result == 'null') {
        throw Exception('Failed to restore backup: No response from backend');
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in restoreBackup: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> deleteBackup({
    required String backupFilename,
  }) async {
    try {
      final result = await _chan.invokeMethod('delete_backup', {
        'backup_filename': backupFilename,
      });
      if (result == null || result == 'null') {
        throw Exception('Failed to delete backup: No response from backend');
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in deleteBackup: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  // ========== DELETION MANAGEMENT METHODS ==========

  Future<Map<String, dynamic>> checkDeletionDependencies({
    required String entityType,
    required int entityId,
  }) async {
    try {
      final result = await _chan.invokeMethod('check_deletion_dependencies', {
        'entity_type': entityType,
        'entity_id': entityId,
      });
      if (result == null || result == 'null') {
        throw Exception('Failed to check deletion dependencies: No response from backend');
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in checkDeletionDependencies: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  // ========== ENHANCED DELETION METHODS ==========

  Future<Map<String, dynamic>> enhancedDeleteUser({
    required int userId,
    String deletedByUser = "admin",
    bool hardDelete = false,
    Map<String, String>? cascadeChoices,
  }) async {
    try {
      final result = await _chan.invokeMethod('enhanced_delete_user', {
        'user_id': userId,
        'deleted_by_user': deletedByUser,
        'hard_delete': hardDelete,
        'cascade_choices': jsonEncode(cascadeChoices ?? {}),
      });
      if (result == null || result == 'null') {
        return {'success': false, 'message': 'No response from server'};
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in enhancedDeleteUser: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      return {'success': false, 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> enhancedDeleteProduct({
    required int productId,
    String deletedByUser = "admin",
    bool hardDelete = false,
    Map<String, String>? cascadeChoices,
  }) async {
    try {
      final result = await _chan.invokeMethod('enhanced_delete_product', {
        'product_id': productId,
        'deleted_by_user': deletedByUser,
        'hard_delete': hardDelete,
        'cascade_choices': jsonEncode(cascadeChoices ?? {}),
      });
      if (result == null || result == 'null') {
        return {'success': false, 'message': 'No response from server'};
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in enhancedDeleteProduct: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      return {'success': false, 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> enhancedDeleteIngredient({
    required int ingredientId,
    String deletedByUser = "admin",
    bool hardDelete = false,
    Map<String, String>? cascadeChoices,
  }) async {
    try {
      final result = await _chan.invokeMethod('enhanced_delete_ingredient', {
        'ingredient_id': ingredientId,
        'deleted_by_user': deletedByUser,
        'hard_delete': hardDelete,
        'cascade_choices': jsonEncode(cascadeChoices ?? {}),
      });
      if (result == null || result == 'null') {
        return {'success': false, 'message': 'No response from server'};
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in enhancedDeleteIngredient: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      return {'success': false, 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> getDeletionImpactAnalysis({
    required String entityType,
    required int entityId,
  }) async {
    try {
      final result = await _chan.invokeMethod('get_deletion_impact_analysis', {
        'entity_type': entityType,
        'entity_id': entityId,
      });
      if (result == null || result == 'null') {
        return {};
      }
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in getDeletionImpactAnalysis: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  // ========== RESTORE METHODS ==========

  Future<List<Map<String, dynamic>>> getDeletedProducts() async {
    try {
      final result = await _chan.invokeMethod('get_deleted_products');
      if (result == null || result == 'null') {
        throw Exception('Failed to get deleted products: No response from backend');
      }
      final List<dynamic> data = jsonDecode(result as String) as List<dynamic>;
      return data.map((item) => item as Map<String, dynamic>).toList();
    } catch (e, stack) {
      print('Error in getDeletedProducts: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getDeletedIngredients() async {
    try {
      final result = await _chan.invokeMethod('get_deleted_ingredients');
      if (result == null || result == 'null') {
        throw Exception('Failed to get deleted ingredients: No response from backend');
      }
      final List<dynamic> data = jsonDecode(result as String) as List<dynamic>;
      return data.map((item) => item as Map<String, dynamic>).toList();
    } catch (e, stack) {
      print('Error in getDeletedIngredients: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getDeletedUsers() async {
    try {
      final result = await _chan.invokeMethod('get_deleted_users');
      if (result == null || result == 'null') {
        throw Exception('Failed to get deleted users: No response from backend');
      }
      final List<dynamic> data = jsonDecode(result as String) as List<dynamic>;
      return data.map((item) => item as Map<String, dynamic>).toList();
    } catch (e, stack) {
      print('Error in getDeletedUsers: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<String?> restoreProduct({required int productId}) async {
    try {
      final result = await _chan.invokeMethod('restore_product', {
        'product_id': productId,
      });
      if (result == null || result == 'null') {
        return null;
      }
      return result as String;
    } catch (e, stack) {
      print('Error in restoreProduct: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      return 'Error restoring product: $e';
    }
  }

  Future<String?> restoreIngredient({required int ingredientId}) async {
    try {
      final result = await _chan.invokeMethod('restore_ingredient', {
        'ingredient_id': ingredientId,
      });
      if (result == null || result == 'null') {
        return null;
      }
      return result as String;
    } catch (e, stack) {
      print('Error in restoreIngredient: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      return 'Error restoring ingredient: $e';
    }
  }

  Future<String?> restoreUser({required int userId}) async {
    try {
      final result = await _chan.invokeMethod('restore_user', {
        'user_id': userId,
      });
      if (result == null || result == 'null') {
        return null;
      }
      return result as String;
    } catch (e, stack) {
      print('Error in restoreUser: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      return 'Error restoring user: $e';
    }
  }

  // ========== SAFE DELETION METHODS ==========
  
  Future<Map<String, dynamic>> safeDeleteUser({
    required int userId,
    bool force = false,
  }) async {
    return await enhancedDeleteUser(
      userId: userId,
      hardDelete: force,
    );
  }

  Future<Map<String, dynamic>> safeDeleteProduct({
    required int productId,
    bool force = false,
  }) async {
    return await enhancedDeleteProduct(
      productId: productId,
      hardDelete: force,
    );
  }

  Future<Map<String, dynamic>> safeDeleteIngredient({
    required int ingredientId,
    bool force = false,
  }) async {
    return await enhancedDeleteIngredient(
      ingredientId: ingredientId,
      hardDelete: force,
    );
  }

  // ========== NEW SIMPLIFIED DELETION SYSTEM ==========
  
  /// Analyze what would happen when deleting an entity
  /// Returns information about whether hard or soft deletion will be used
  Future<Map<String, dynamic>> analyzeDeletionImpact({
    required String entityType,
    required int entityId,
  }) async {
    try {
      final result = await _chan.invokeMethod('analyze_deletion_impact', {
        'entity_type': entityType,
        'entity_id': entityId,
      });
      
      if (result == null || result == 'null') {
        throw Exception('No response from backend');
      }
      
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in analyzeDeletionImpact: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }
  
  /// Execute deletion with simplified logic
  /// Automatically chooses hard vs soft deletion based on dependencies
  Future<Map<String, dynamic>> executeDeletion({
    required String entityType,
    required int entityId,
    String deletedBy = "flutter_admin",
  }) async {
    try {
      final result = await _chan.invokeMethod('execute_deletion', {
        'entity_type': entityType,
        'entity_id': entityId,
        'deleted_by': deletedBy,
      });
      
      if (result == null || result == 'null') {
        throw Exception('No response from backend');
      }
      
      return jsonDecode(result as String) as Map<String, dynamic>;
    } catch (e, stack) {
      print('Error in executeDeletion: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }

  Future<void> testFirebaseLogging() async {
    try {
      await _chan.invokeMethod('test_firebase_logging');
    } catch (e, stack) {
      print('Error in testFirebaseLogging: \x1b[31m$e\nStacktrace: $stack\x1b[0m');
      rethrow;
    }
  }
}
