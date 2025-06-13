import 'package:chame_flutter/data/py_bride.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/services.dart';

class AuthService extends ChangeNotifier {
  final _storage = FlutterSecureStorage();
  String? _token;
  String? _role;
  bool _initialized = false;

  bool get initialized => _initialized;
  bool get isLoggedIn => _token != null;
  String get role => _role ?? '';

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

  Future<bool> changePassword(String oldPassword, String newPassword) async {
    if (_token == null) {
      print('Cannot change password: user is not logged in');
      return false; // User is not logged in
    }
    try {
      await PyBridge().changePassword(user_id: _token!, oldPassword: oldPassword, newPassword: newPassword);
      return true;
    } catch (e) {
      print('Exception while changing password: $e');
      if (e is PlatformException && e.message != null) {
        throw Exception(e.message);
      }
      throw Exception('Failed to change password');
    }
  }

  Future<void> logout() async {
    _token = null;
    _role  = null;
    await _storage.deleteAll();
    notifyListeners();
  }
}