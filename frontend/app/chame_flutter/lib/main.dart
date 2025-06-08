import 'package:chame_flutter/pages/add_ingredients_page.dart';
import 'package:chame_flutter/pages/add_product_page.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'pages/ingredients_page.dart';
import 'pages/products_page.dart';
import 'pages/purchase_page.dart';
import 'pages/toast_round_page.dart';
import 'pages/users_page.dart';
import 'pages/bank_page.dart';
import 'data/py_bride.dart';

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
  runApp(const ChameApp());
}

class ChameApp extends StatelessWidget {
  const ChameApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Chame',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.teal),
      initialRoute: '/',
      routes: {
        '/': (_) => HomePage(),
        '/ingredients': (_) => IngredientsPage(),
        '/products': (_) => ProductsPage(),
        '/purchase': (_) => PurchasePage(),
        '/toast_round': (_) => ToastRoundPage(),
        '/users': (_) => UsersPage(),
        '/bank': (_) => BankPage(),
        '/add_ingredients': (_) => AddIngredientsPage(),
        '/add_product': (_) => AddProductPage(),
        // ...other routes
      },
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chame App Home')),
      body: Center(
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
            ElevatedButton(
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
          ],
        ),
      ),
    );
  }
}
