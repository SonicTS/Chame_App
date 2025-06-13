import 'package:chame_flutter/pages/add_ingredients_page.dart';
import 'package:chame_flutter/pages/add_product_page.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:provider/provider.dart';
import 'pages/ingredients_page.dart';
import 'pages/products_page.dart';
import 'pages/purchase_page.dart';
import 'pages/toast_round_page.dart';
import 'pages/users_page.dart';
import 'pages/bank_page.dart';
import 'data/py_bride.dart';
import 'pages/restock_ingredients_page.dart';


class AuthGate extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);

    if (!auth.initialized) {
      // still loading from secure storage
      return Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    // once initialized, choose Login or Home
    return auth.isLoggedIn ? HomePage() : LoginScreen();
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Ping Python backend at startup
  await Firebase.initializeApp();
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
  try {
    await PyBridge().ping();
    print('Python backend is ready.');
  } catch (e, stack) {
    print('Failed to ping Python backend: '
        '[31m$e\n$stack[0m');
  }
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthService(),
      child: ChameApp(),
    ),
  );
}

class ChameApp extends StatelessWidget {
  const ChameApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthService>(
      builder: (ctx, auth, _) {
        return MaterialApp(
          title: 'Chame',
          theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.teal),
          home: AuthGate(),
          routes: {
            '/ingredients': (_) => IngredientsPage(),
            '/products': (_) => ProductsPage(),
            '/purchase': (_) => PurchasePage(),
            '/toast_round': (_) => ToastRoundPage(),
            '/users': (_) => UsersPage(),
            '/bank': (_) => BankPage(),
            '/add_ingredients': (_) => AddIngredientsPage(),
            '/add_product': (_) => AddProductPage(),
            '/restock_ingredients': (_) => RestockIngredientsPage(),
            '/settings': (_) => SettingsPage(),
            // ...other routes
          },
        );
      }
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Chame App Home')),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/ingredients'),
                        child: const Text('Ingredients'),
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/products'),
                        child: const Text('Products'),
                      ),
                      if (auth.role == "admin") ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/bank'),
                        child: const Text('Bank'),
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/purchase'),
                        child: const Text('Purchase'),
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/toast_round'),
                        child: const Text('Toast Rounds'),
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/users'),
                        child: const Text('Users'),
                      ),
                      if (auth.role == "admin")
                        ElevatedButton(
                          onPressed: () => Navigator.pushNamed(context, '/restock_ingredients'),
                          child: const Text('Restock Ingredients'),
                        ),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/settings'),
                        child: const Text('Settings'),
                      ),
                      ElevatedButton(
                        onPressed: () {
                          auth.logout();
                        },
                        child: const Text('Logout'),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}



class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl  = TextEditingController();
  bool _loading = false, _error = false;

  void _submit() async {
    setState(() { _loading = true; _error = false; });
    final auth = Provider.of<AuthService>(context, listen: false);
    try {
      final success = await auth.login(_emailCtrl.text, _passCtrl.text);
      setState(() { _loading = false; _error = !success; });
      if (!success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Login failed for ${_emailCtrl.text}')),
        );
      }
    } catch (e) {
      setState(() { _loading = false; _error = true; });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
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
                TextField(controller: _emailCtrl, decoration: const InputDecoration(labelText: 'User')),
                TextField(controller: _passCtrl,  decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
                const SizedBox(height: 20),
                if (_error) const Text('Login failed', style: TextStyle(color: Colors.red)),
                ElevatedButton(
                  onPressed: _loading ? null : _submit,
                  child: _loading ? const CircularProgressIndicator() : const Text('Log In'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}


class SettingsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ElevatedButton(
                onPressed: () => showModalBottomSheet(
                context: context,
                isScrollControlled: true, // <-- Key for keyboard safety!
                builder: (ctx) => ChangePasswordSheet(),
                shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                ),
              ),
              child: const Text('Change Password'),
            ),
          ),
        ),
      ),
    );
  }
}


class ChangePasswordSheet extends StatefulWidget {
  @override
  State<ChangePasswordSheet> createState() => _ChangePasswordSheetState();
}

class _ChangePasswordSheetState extends State<ChangePasswordSheet> {
  final _oldPassCtrl = TextEditingController();
  final _newPassCtrl = TextEditingController();
  final _confirmPassCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  void _changePassword() async {
    setState(() { _loading = true; _error = null; });
    if (_newPassCtrl.text != _confirmPassCtrl.text) {
      setState(() { _loading = false; _error = 'Passwords do not match'; });
      return;
    }
    final auth = Provider.of<AuthService>(context, listen: false);
    try {
      final result = await auth.changePassword(_oldPassCtrl.text, _newPassCtrl.text);
      setState(() { _loading = false; });
      if (result == true) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Password changed successfully')));
      }
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      // This ensures the sheet goes above the keyboard!
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 24,
        right: 24,
        top: 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Change Password',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(
              controller: _oldPassCtrl,
              decoration: const InputDecoration(labelText: 'Current Password'),
              obscureText: true,
            ),
            TextField(
              controller: _newPassCtrl,
              decoration: const InputDecoration(labelText: 'New Password'),
              obscureText: true,
            ),
            TextField(
              controller: _confirmPassCtrl,
              decoration: const InputDecoration(labelText: 'Confirm New Password'),
              obscureText: true,
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: _loading ? null : () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _loading ? null : _changePassword,
                  child: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Change'),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}