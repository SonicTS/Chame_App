import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/widgets/shared/user_dropdown_selector.dart';

/// Login screen. This is really just a [UserDropdownSelector] filtered down
/// to admin/wirt users for quick-login, with a manual username/password
/// fallback for anyone else (or if the user list fails to load).
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _userCtrl = TextEditingController(text: 'admin');
  final _passCtrl = TextEditingController();
  bool _loading = false, _error = false;
  List<Map<String, dynamic>> _availableUsers = [];
  int? _selectedUserId;
  bool _usersLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadAvailableUsers();
  }

  Future<void> _loadAvailableUsers() async {
    try {
      setState(() => _loading = true);
      
      // Use Future.microtask to avoid blocking UI
      await Future.microtask(() async {
        // Get all users from backend
        final users = await PyBridge().getAllUsers();
        
        // Filter to only admin and wirt users and allow duplicates by name
        final filteredUsers = users.where((user) => 
          user['role'] == 'admin' || user['role'] == 'wirt'
        ).toList();
        
        if (mounted) {
          setState(() {
            _availableUsers = filteredUsers;
            _usersLoaded = true;
            _loading = false;
            
            // Auto-select first user if available
            if (_availableUsers.isNotEmpty) {
              _selectedUserId = _availableUsers[0]['user_id'];
            }
          });
        }
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = true;
          _usersLoaded = true;
        });
      //print('Error loading users: $e');
        
        // Fallback: show error but allow typing username
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not load users. You can still try manual login.'),
            backgroundColor: Colors.orange,
          ),
        );
      }
    }
  }

  bool get _useManualLogin => _availableUsers.isEmpty || _selectedUserId == null;

  @override
  void dispose() {
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  void _submit() async {
    final manualUsername = _userCtrl.text.trim();
    if (_useManualLogin && manualUsername.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please enter a username')),
      );
      return;
    }

    if (_selectedUserId == null && _availableUsers.isNotEmpty && manualUsername.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select a user')),
      );
      return;
    }

    setState(() { _loading = true; _error = false; });
    final auth = Provider.of<AuthService>(context, listen: false);
    
    try {
      // Use Future.microtask to avoid blocking UI thread
      await Future.microtask(() async {
        String username;
        
        if (!_useManualLogin && _selectedUserId != null) {
          // Use selected user from dropdown
          final selectedUser = _availableUsers.firstWhere(
            (user) => user['user_id'] == _selectedUserId
          );
          username = selectedUser['name'];
        } else {
          username = manualUsername;
        }
        
        // Allow empty password
        final password = _passCtrl.text;
        
        final success = await auth.login(username, password);
        
        if (mounted) {
          setState(() { _loading = false; _error = !success; });
          
          if (!success) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Login failed for $username')),
            );
          }
        }
      });
    } catch (e) {
      if (mounted) {
        setState(() { _loading = false; _error = true; });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // User selection dropdown
                if (_usersLoaded && _availableUsers.isNotEmpty) ...[
                  const Text(
                    'Select User:',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 8),
                  UserDropdownSelector(
                    users: _availableUsers,
                    selectedUserId: _selectedUserId,
                    label: 'Choose a user...',
                    itemLabelBuilder: (user) => '${user['name']} (${user['role']})',
                    onChanged: (user) {
                      setState(() {
                        _selectedUserId = user?['user_id'];
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  TextButton.icon(
                    onPressed: () {
                      setState(() {
                        _selectedUserId = null;
                        if (_userCtrl.text.trim().isEmpty) {
                          _userCtrl.text = 'admin';
                        }
                      });
                    },
                    icon: const Icon(Icons.person_outline),
                    label: const Text('Use Manual Login Instead'),
                  ),
                  const SizedBox(height: 8),
                ] else if (_usersLoaded && _availableUsers.isEmpty) ...[
                  const Icon(Icons.warning, color: Colors.orange, size: 48),
                  const SizedBox(height: 16),
                  const Text(
                    'No admin or wirt users found.\nTry manual login with the default admin account.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.orange),
                  ),
                  const SizedBox(height: 16),
                ] else if (!_usersLoaded) ...[
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  const Text('Loading users...'),
                  const SizedBox(height: 16),
                ],

                if (_useManualLogin) ...[
                  TextField(
                    controller: _userCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Username',
                      hintText: 'Enter username',
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                
                // Password field
                TextField(
                  controller: _passCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Password (optional)',
                    hintText: 'Leave empty for default password',
                  ),
                  obscureText: true,
                ),
                const SizedBox(height: 20),
                
                // Error message
                if (_error) 
                  const Text(
                    'Login failed',
                    style: TextStyle(color: Colors.red),
                  ),
                
                // Login button
                ElevatedButton(
                  onPressed: (_loading || !_usersLoaded)
                    ? null 
                    : _submit,
                  child: _loading 
                    ? const CircularProgressIndicator() 
                    : const Text('Log In'),
                ),
                
                // Refresh button if user loading failed
                if (_usersLoaded && _availableUsers.isEmpty) ...[
                  const SizedBox(height: 16),
                  TextButton.icon(
                    onPressed: _loadAvailableUsers,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry Loading Users'),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
