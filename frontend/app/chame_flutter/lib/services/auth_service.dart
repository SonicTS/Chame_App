import 'package:chame_flutter/data/py_bride.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/services.dart';

class AuthService extends ChangeNotifier {
  final _storage = FlutterSecureStorage();
  String? _token;
  String? _role;
  bool _initialized = false;
  final Set<int> _knownGodUserIds = <int>{};

  bool get initialized => _initialized;
  bool get isLoggedIn => _token != null;
  String get role => _role ?? '';
  int? get currentUserId => _token != null ? int.tryParse(_token!) : null;
  bool get hasAdminRights => _role == 'admin' || _role == 'god';
  bool get canManageUsers => hasAdminRights || _role == 'wirt';
  bool get canSeeGodUser => _role == 'god';

  void _rememberGodUserIds(Iterable<Map<String, dynamic>> users) {
    for (final user in users) {
      if (user['role']?.toString() != 'god') {
        continue;
      }
      final userId = user['user_id'];
      if (userId is int) {
        _knownGodUserIds.add(userId);
      } else if (userId is num) {
        _knownGodUserIds.add(userId.toInt());
      }
    }
  }

  bool _mapContainsGodLink(Map<dynamic, dynamic> record) {
    if (record['role']?.toString() == 'god') {
      return true;
    }

    for (final key in ['user_id', 'consumer_id', 'donator_id', 'salesman_id']) {
      final value = record[key];
      if (value is int && _knownGodUserIds.contains(value)) {
        return true;
      }
      if (value is num && _knownGodUserIds.contains(value.toInt())) {
        return true;
      }
    }

    for (final value in record.values) {
      if (_containsGodLink(value)) {
        return true;
      }
    }

    return false;
  }

  bool _containsGodLink(dynamic value) {
    if (value is Map) {
      return _mapContainsGodLink(value);
    }
    if (value is Iterable) {
      for (final item in value) {
        if (_containsGodLink(item)) {
          return true;
        }
      }
    }
    return false;
  }

  List<Map<String, dynamic>> filterVisibleUsers(Iterable<Map<String, dynamic>> users) {
    _rememberGodUserIds(users);
    if (canSeeGodUser) {
      return users.map((user) => Map<String, dynamic>.from(user)).toList();
    }
    return users
        .where((user) => user['role']?.toString() != 'god')
        .map((user) => Map<String, dynamic>.from(user))
        .toList();
  }

  List<Map<String, dynamic>> filterVisibleRecords(Iterable<Map<String, dynamic>> records) {
    if (canSeeGodUser) {
      return records.map((record) => Map<String, dynamic>.from(record)).toList();
    }
    return records
        .where((record) => !_containsGodLink(record))
        .map((record) => Map<String, dynamic>.from(record))
        .toList();
  }

  AuthService() {
    _loadFromStorage();
  }

  Future<void> _loadFromStorage() async {
    _token = await _storage.read(key: 'user_id');
    _role  = await _storage.read(key: 'user_role');
    _initialized = true;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    try {
      final fetched = await PyBridge().login(username: username, password: password);
      if (fetched == null) return false; // Login failed

      if (fetched['user_id'] == null) {
        print('Login failed: user_id is null');
        return false;
      }
      if (fetched['role'] == null) {
        print('Login failed: role is null');
        return false;
      }
      _token = fetched['user_id'].toString();          // e.g. JWT
      _role  = fetched['role'];           // e.g. "admin" or "user"
      _rememberGodUserIds([fetched]);
      await _storage.write(key: 'user_id', value: _token);
      await _storage.write(key: 'user_role',    value: _role);
      notifyListeners();
      return true;
    } catch (e) {
      print('Exception during login: $e');
      if (e is PlatformException && e.message != null) {
        throw Exception(e.message);
      }
      notifyListeners();
      throw Exception('Login failed: $e');
    }
    
  }

  /// Changes the password of [targetUserId] (defaults to the currently
  /// logged-in user). The backend still requires [oldPassword] to match
  /// whatever account [targetUserId] refers to, so this doesn't grant any
  /// extra access beyond what changing your own password already did.
  Future<bool> changePassword(String oldPassword, String newPassword, {int? targetUserId}) async {
    final userId = targetUserId ?? currentUserId;
    if (userId == null) {
      print('Cannot change password: user is not logged in');
      return false; // User is not logged in
    }
    try {
      await PyBridge().changePassword(user_id: userId.toString(), oldPassword: oldPassword, newPassword: newPassword);
      return true;
    } catch (e) {
      print('Exception while changing password: $e');
      if (e is PlatformException && e.message != null) {
        throw Exception(e.message);
      }
      throw Exception('Failed to change password');
    }
  }

  /// Admin-only: resets [targetUserId]'s password directly, without needing
  /// their old password. Only actually succeeds if the currently logged-in
  /// user has admin rights -- the backend independently re-checks this too,
  /// this local check just avoids an unnecessary round-trip/nicer error.
  Future<bool> adminResetPassword(int targetUserId, String newPassword) async {
    if (!hasAdminRights) {
      print('Cannot reset password: current user is not an admin');
      return false;
    }
    try {
      await PyBridge().adminChangePassword(user_id: targetUserId.toString(), newPassword: newPassword);
      return true;
    } catch (e) {
      print('Exception while resetting password: $e');
      if (e is PlatformException && e.message != null) {
        throw Exception(e.message);
      }
      throw Exception('Failed to reset password');
    }
  }

  Future<void> logout() async {
    try {
      await PyBridge().logout();
    } catch (e) {
      print('Exception during logout: $e');
    }
    _token = null;
    _role  = null;
    await _storage.deleteAll();
    notifyListeners();
  }
}