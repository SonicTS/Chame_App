import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:provider/provider.dart';

class AddUserPage extends StatefulWidget {
  const AddUserPage({super.key});

  @override
  State<AddUserPage> createState() => _AddUserPageState();
}

class _AddUserPageState extends State<AddUserPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _balanceController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  String _role = 'user';
  bool _isSubmitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _balanceController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _addUser() async {
    if (!_formKey.currentState!.validate()) return;

    if (_role == 'wirt' && (_passwordController.text.isEmpty || _passwordController.text.length < 4)) {
      _showDialog('Error', 'Wirt password must be at least 4 characters long!');
      return;
    }
    if (_role == 'admin' && (_passwordController.text.isEmpty || _passwordController.text.length < 8)) {
      _showDialog('Error', 'Admin password must be at least 8 characters long!');
      return;
    }
    if ((_role == 'wirt' || _role == 'admin') && _passwordController.text != _confirmPasswordController.text) {
      _showDialog('Error', 'Passwords do not match!');
      return;
    }

    setState(() => _isSubmitting = true);
    
    try {
      final error = await PyBridge().addUser(
        name: _nameController.text.trim(),
        balance: double.parse(_balanceController.text),
        role: _role,
        password: _role == 'wirt' || _role == 'admin' ? _passwordController.text : null,
      );
      
      setState(() => _isSubmitting = false);
      
      if (error != null) {
        _showDialog('Error', error);
      } else {
        _showDialog('Success', 'User added successfully!', onOkPressed: () {
          Navigator.of(context).pop(); // Close success dialog
          Navigator.of(context).pop(); // Go back to users page
        });
        _clearForm();
      }
    } catch (e) {
      setState(() => _isSubmitting = false);
      _showDialog('Error', 'Failed to add user: $e');
    }
  }

  void _clearForm() {
    _nameController.clear();
    _balanceController.clear();
    _passwordController.clear();
    _confirmPasswordController.clear();
    setState(() => _role = 'user');
  }

  void _showDialog(String title, String content, {VoidCallback? onOkPressed}) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
            onPressed: onOkPressed ?? () => Navigator.pop(ctx),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    
    // Check if user has permission to add users
    if (auth.role != 'admin' && auth.role != 'wirt') {
      return Scaffold(
        appBar: AppBar(title: const Text('Add User')),
        body: const Center(
          child: Text(
            'Access Denied\nOnly Admin and Wirt users can add new users.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 18),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Add New User'),
        backgroundColor: Colors.blue.shade600,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Card(
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'User Information',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 20),
                        
                        // Name field
                        TextFormField(
                          controller: _nameController,
                          decoration: const InputDecoration(
                            labelText: 'User Name *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.person),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'Name is required';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        
                        // Balance field
                        TextFormField(
                          controller: _balanceController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(
                            labelText: 'Initial Balance *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.euro),
                            suffixText: '€',
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'Balance is required';
                            }
                            final balance = double.tryParse(value);
                            if (balance == null) {
                              return 'Please enter a valid number';
                            }
                            if (balance < 0) {
                              return 'Balance cannot be negative';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        
                        // Role dropdown
                        DropdownButtonFormField<String>(
                          value: _role,
                          decoration: const InputDecoration(
                            labelText: 'Role *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.security),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'user', child: Text('User')),
                            DropdownMenuItem(value: 'wirt', child: Text('Wirt')),
                            DropdownMenuItem(value: 'admin', child: Text('Admin')),
                          ],
                          onChanged: (val) => setState(() => _role = val!),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Role is required';
                            }
                            return null;
                          },
                        ),
                        
                        // Password fields (only show for admin/wirt roles)
                        if (_role == 'wirt' || _role == 'admin') ...[
                          const SizedBox(height: 16),
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.orange.shade50,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.orange.shade200),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.info, color: Colors.orange.shade700),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    _role == 'admin' 
                                        ? 'Admin password must be at least 8 characters long'
                                        : 'Wirt password must be at least 4 characters long',
                                    style: TextStyle(color: Colors.orange.shade700),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _passwordController,
                            obscureText: true,
                            decoration: const InputDecoration(
                              labelText: 'Password *',
                              border: OutlineInputBorder(),
                              prefixIcon: Icon(Icons.lock),
                            ),
                            validator: (value) {
                              if (_role == 'wirt' || _role == 'admin') {
                                if (value == null || value.isEmpty) {
                                  return 'Password is required for ${_role} role';
                                }
                                if (_role == 'admin' && value.length < 8) {
                                  return 'Admin password must be at least 8 characters';
                                }
                                if (_role == 'wirt' && value.length < 4) {
                                  return 'Wirt password must be at least 4 characters';
                                }
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _confirmPasswordController,
                            obscureText: true,
                            decoration: const InputDecoration(
                              labelText: 'Confirm Password *',
                              border: OutlineInputBorder(),
                              prefixIcon: Icon(Icons.lock_outline),
                            ),
                            validator: (value) {
                              if (_role == 'wirt' || _role == 'admin') {
                                if (value == null || value.isEmpty) {
                                  return 'Please confirm your password';
                                }
                                if (value != _passwordController.text) {
                                  return 'Passwords do not match';
                                }
                              }
                              return null;
                            },
                          ),
                        ],
                        
                        const SizedBox(height: 24),
                        
                        // Action buttons
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            TextButton(
                              onPressed: _isSubmitting ? null : () => Navigator.of(context).pop(),
                              child: const Text('Cancel'),
                            ),
                            const SizedBox(width: 12),
                            ElevatedButton(
                              onPressed: _isSubmitting ? null : _addUser,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                              ),
                              child: _isSubmitting
                                  ? const SizedBox(
                                      width: 20,
                                      height: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                      ),
                                    )
                                  : const Text('Add User'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Information card
                Card(
                  color: Colors.blue.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.info, color: Colors.blue.shade700),
                            const SizedBox(width: 8),
                            Text(
                              'User Role Information',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.blue.shade700,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text('• User: Has an account with money and can purchase products'),
                        const Text('• Wirt: Can sell products and return user money and collect it'),
                        const Text('• Admin: Can create ingredients, products, new users, restock ingredients and delete stuff'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
