import 'package:chame_flutter/pages/add_ingredients_page.dart';
import 'package:chame_flutter/pages/add_product_page.dart';
import 'package:chame_flutter/pages/backup_management_page.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:provider/provider.dart';
import 'package:flutter/services.dart';
import 'pages/ingredients_page.dart';
import 'pages/products_page.dart';
import 'pages/purchase_page.dart';
import 'pages/toast_round_page.dart';
import 'pages/users_page.dart';
import 'pages/bank_page.dart';
import 'data/py_bride.dart';
import 'pages/restock_ingredients_page.dart';
import 'pages/return_pfand.dart';

// Global method channel for reverse bridge calls
const MethodChannel _reverseBridgeChannel = MethodChannel('samples.flutter.dev/chame/python');

// Setup reverse bridge listener for Python → Flutter calls
void _setupReverseBridge() {
  try {
    print('🌉 Setting up method call handler for reverse bridge...');
    _reverseBridgeChannel.setMethodCallHandler(_handleReverseBridgeCall);
    print('✅ Reverse bridge method call handler configured successfully');
    print('   Channel: ${_reverseBridgeChannel.name}');
    print('   Handler: _handleReverseBridgeCall');
  } catch (e) {
    print('❌ Failed to setup reverse bridge: $e');
    rethrow;
  }
}

// Handle calls from Python through the bridge
Future<void> _handleReverseBridgeCall(MethodCall call) async {
  final String callTimestamp = DateTime.now().toIso8601String();
  
  try {
    print('📞 Received reverse bridge call at $callTimestamp');
    print('   Method: ${call.method}');
    print('   Arguments type: ${call.arguments?.runtimeType}');
    
    switch (call.method) {
      case 'log_to_firebase':
        print('🔥 Handling Firebase logging request...');
        await _handleFirebaseLog(call.arguments);
        print('✅ Firebase logging request completed');
        break;
      case 'update_progress':
        print('📊 Handling progress update...');
        await _handleProgressUpdate(call.arguments);
        print('✅ Progress update completed');
        break;
      case 'show_notification':
        print('🔔 Handling notification request...');
        await _handleShowNotification(call.arguments);
        print('✅ Notification request completed');
        break;
      default:
        print('❓ Unknown reverse bridge method called: ${call.method}');
        print('   Available methods: log_to_firebase, update_progress, show_notification');
    }
    
    print('✅ Reverse bridge call ${call.method} processed successfully');
    
  } catch (e, stackTrace) {
    print('💥 Error handling reverse bridge call ${call.method}: $e');
    print('📍 Stack trace: $stackTrace');
    print('🔍 Call arguments: ${call.arguments}');
    
    // Try to log this error to Firebase
    try {
      FirebaseCrashlytics.instance.recordError(
        'Reverse Bridge Call Error: ${call.method}',
        stackTrace,
        fatal: false,
        information: [
          'Method: ${call.method}',
          'Error: $e',
          'Timestamp: $callTimestamp',
          'Arguments: ${call.arguments}',
        ],
      );
      print('🆘 Logged reverse bridge error to Firebase');
    } catch (logError) {
      print('☠️ Failed to log reverse bridge error: $logError');
    }
  }
}

// Handle Firebase logging from Python
Future<void> _handleFirebaseLog(Map<dynamic, dynamic> arguments) async {
  final String timestamp = DateTime.now().toIso8601String();
  
  try {
    final String level = arguments['level']?.toString() ?? 'INFO';
    final String message = arguments['message']?.toString() ?? '';
    final Map<String, dynamic> metadata = Map<String, dynamic>.from(arguments['metadata'] ?? {});
    
    print('🚀 Starting Firebase log operation at $timestamp');
    print('   Level: $level');
    print('   Message: $message');
    print('   Metadata keys: ${metadata.keys.toList()}');
    
    // Log to Firebase Crashlytics with detailed logging
    try {
      FirebaseCrashlytics.instance.log('[$level] Python: $message');
      print('✅ Successfully wrote to Firebase Crashlytics log');
    } catch (logError) {
      print('❌ Failed to write to Firebase Crashlytics log: $logError');
      rethrow;
    }
    
    // Set custom keys for context with logging
    try {
      print('📝 Setting ${metadata.length} custom keys...');
      metadata.forEach((key, value) {
        final keyName = 'python_$key';
        final keyValue = value.toString();
        FirebaseCrashlytics.instance.setCustomKey(keyName, keyValue);
        print('   ✓ Set custom key: $keyName = $keyValue');
      });
      print('✅ All custom keys set successfully');
    } catch (keyError) {
      print('❌ Failed to set custom keys: $keyError');
      rethrow;
    }
    
    // Record as non-fatal error for better visibility in Firebase Console
    try {
      print('📊 Recording non-fatal error to Firebase...');
      FirebaseCrashlytics.instance.recordError(
        'Python Log [$level]: $message',
        null,
        fatal: false,
        information: [
          'Level: $level',
          'Message: $message',
          'Timestamp: $timestamp',
          'Flutter_Log_Handler: _handleFirebaseLog',
          ...metadata.entries.map((e) => '${e.key}: ${e.value}'),
        ],
      );
      print('✅ Successfully recorded non-fatal error to Firebase');
    } catch (recordError) {
      print('❌ Failed to record error to Firebase: $recordError');
      rethrow;
    }
    
    // Set breadcrumb for tracking with logging
    try {
      print('🍞 Setting breadcrumb data...');
      FirebaseCrashlytics.instance.setCustomKey('last_python_log', '[$level] $message');
      FirebaseCrashlytics.instance.setCustomKey('last_python_log_time', timestamp);
      print('✅ Breadcrumb data set successfully');
    } catch (breadcrumbError) {
      print('❌ Failed to set breadcrumb data: $breadcrumbError');
      rethrow;
    }
    
    print('🔥 Firebase log operation completed successfully');
    print('   Final summary: [$level] Python: $message');
    if (metadata.isNotEmpty) {
      print('   📦 Metadata: $metadata');
    }
    
  } catch (e, stackTrace) {
    print('💥 Critical error in _handleFirebaseLog: $e');
    print('📍 Stack trace: $stackTrace');
    print('🔍 Arguments received: $arguments');
    
    // Try to log the error itself to Firebase
    try {
      FirebaseCrashlytics.instance.recordError(
        'Firebase Logging Handler Error: $e',
        stackTrace,
        fatal: false,
        information: [
          'Handler: _handleFirebaseLog',
          'Original_arguments: $arguments',
          'Timestamp: $timestamp',
          'Error_occurred_while: Processing Python Firebase log',
        ],
      );
      print('🆘 Successfully logged the logging error to Firebase');
    } catch (metaError) {
      print('☠️ Failed to log the logging error: $metaError');
    }
  }
}

// Handle progress updates from Python
Future<void> _handleProgressUpdate(Map<dynamic, dynamic> arguments) async {
  final String timestamp = DateTime.now().toIso8601String();
  
  try {
    final double progress = (arguments['progress'] as num?)?.toDouble() ?? 0.0;
    final String message = arguments['message']?.toString() ?? '';
    
    print('📊 Progress update received at $timestamp');
    print('   Progress: ${(progress * 100).toStringAsFixed(1)}%');
    print('   Message: $message');
    
    // You can emit this to a stream or update UI state here
    print('✅ Progress update processed successfully');
    
  } catch (e) {
    print('❌ Error processing progress update: $e');
    print('🔍 Arguments: $arguments');
  }
}

// Handle notifications from Python
Future<void> _handleShowNotification(Map<dynamic, dynamic> arguments) async {
  final String timestamp = DateTime.now().toIso8601String();
  
  try {
    final String title = arguments['title']?.toString() ?? '';
    final String message = arguments['message']?.toString() ?? '';
    final String type = arguments['type']?.toString() ?? 'info';
    
    print('🔔 Notification received at $timestamp');
    print('   Type: $type');
    print('   Title: $title');
    print('   Message: $message');
    
    // You can show actual notifications here using flutter_local_notifications
    print('✅ Notification processed successfully');
    
  } catch (e) {
    print('❌ Error processing notification: $e');
    print('🔍 Arguments: $arguments');
  }
}

// Initialize Python backend asynchronously to avoid blocking main thread
void _initializePythonBackend() {
  final String initTimestamp = DateTime.now().toIso8601String();
  print('🐍 Starting Python backend initialization at $initTimestamp');
  
  Future.microtask(() async {
    try {
      print('📡 Attempting to ping Python backend...');
      await PyBridge().ping();
      print('✅ Python backend ping successful!');
      
      // Test logging immediately with detailed logging
      try {
        print('📝 Writing success log to Firebase Crashlytics...');
        FirebaseCrashlytics.instance.log('Python backend connection successful');
        print('✅ Successfully wrote connection log to Firebase');
        
        print('📊 Recording success event to Firebase...');
        FirebaseCrashlytics.instance.recordError(
          'Python Backend Status: Connected',
          null,
          fatal: false,
          information: [
            'Backend ping successful',
            'Initialization_timestamp: $initTimestamp',
            'Connection_method: PyBridge().ping()',
            'Status: SUCCESS',
          ],
        );
        print('✅ Successfully recorded connection event to Firebase');
        
      } catch (logError) {
        print('❌ Failed to log success to Firebase: $logError');
      }
      
    } catch (e, stack) {
      print('❌ Failed to ping Python backend:');
      print('   Error: $e');
      print('   Stack: $stack');
      
      // Log the failure to Firebase with detailed logging
      try {
        print('🆘 Logging backend failure to Firebase...');
        FirebaseCrashlytics.instance.recordError(
          'Python Backend Connection Failed',
          StackTrace.current,
          fatal: false,
          information: [
            'Failed during app startup',
            'Initialization_timestamp: $initTimestamp',
            'Error_message: $e',
            'Stack_trace: $stack',
            'Connection_method: PyBridge().ping()',
            'Status: FAILED',
          ],
        );
        print('✅ Successfully logged backend failure to Firebase');
        
      } catch (logError) {
        print('💥 Critical: Failed to log backend failure to Firebase: $logError');
      }
    }
  });
}

void main() async {
  final String appStartTimestamp = DateTime.now().toIso8601String();
  print('🚀 App startup initiated at $appStartTimestamp');
  
  WidgetsFlutterBinding.ensureInitialized();
  print('✅ Flutter widgets binding initialized');
  
  // Initialize Firebase with detailed logging
  try {
    print('🔥 Initializing Firebase...');
    await Firebase.initializeApp();
    print('✅ Firebase initialized successfully');
    
    print('📊 Setting up Firebase error handling...');
    FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
    print('✅ Firebase error handling configured');
    
  } catch (firebaseError, stackTrace) {
    print('💥 Critical: Firebase initialization failed!');
    print('   Error: $firebaseError');
    print('   Stack: $stackTrace');
    // Continue anyway, but log to console
  }
  
  // Setup reverse bridge for Python logging with logging
  try {
    print('🌉 Setting up reverse bridge for Python logging...');
    _setupReverseBridge();
    print('✅ Reverse bridge setup completed');
  } catch (bridgeError) {
    print('❌ Failed to setup reverse bridge: $bridgeError');
  }
  
  // Test Firebase logging immediately with detailed logging
  try {
    print('🧪 Testing Firebase logging functionality...');
    
    FirebaseCrashlytics.instance.log('App starting - Firebase logging test');
    print('✅ Firebase log test completed');
    
    FirebaseCrashlytics.instance.recordError(
      'Test Firebase Integration',
      null,
      fatal: false,
      information: [
        'App startup test',
        'Firebase integration check',
        'Startup_timestamp: $appStartTimestamp',
        'Test_type: Initial_connectivity',
      ],
    );
    print('✅ Firebase recordError test completed');
    
  } catch (testError) {
    print('❌ Firebase logging test failed: $testError');
  }
  
  // Initialize Python backend asynchronously to avoid ANR
  print('🐍 Scheduling Python backend initialization...');
  _initializePythonBackend();
  
  print('🎯 Starting Flutter app...');
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthService(),
      child: ChameApp(),
    ),
  );
  print('✅ Flutter app started successfully');
}

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
            '/backup_management': (_) => BackupManagementPage(),
            '/return_pfand': (_) => ReturnPfandPage(),
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
                        onPressed: () => Navigator.pushNamed(context, '/return_pfand'),
                        child: const Text('Return Pfand'),
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
        print('Error loading users: $e');
        
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

  String _getUserDisplayName(Map<String, dynamic> user) {
    return '${user['name']} (${user['role']})';
  }

  void _submit() async {
    if (_selectedUserId == null && _availableUsers.isNotEmpty) {
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
        
        if (_selectedUserId != null) {
          // Use selected user from dropdown
          final selectedUser = _availableUsers.firstWhere(
            (user) => user['user_id'] == _selectedUserId
          );
          username = selectedUser['name'];
        } else {
          // Fallback: manual username entry (shouldn't happen with current UI)
          username = 'admin'; // Default fallback
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
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        value: _selectedUserId,
                        isExpanded: true,
                        hint: const Text('Choose a user...'),
                        items: _availableUsers.map((user) {
                          return DropdownMenuItem<int>(
                            value: user['user_id'],
                            child: Text(_getUserDisplayName(user)),
                          );
                        }).toList(),
                        onChanged: (int? newValue) {
                          setState(() {
                            _selectedUserId = newValue;
                          });
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ] else if (_usersLoaded && _availableUsers.isEmpty) ...[
                  const Icon(Icons.warning, color: Colors.orange, size: 48),
                  const SizedBox(height: 16),
                  const Text(
                    'No admin or wirt users found.\nPlease contact an administrator.',
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
                  onPressed: (_loading || (!_usersLoaded || _availableUsers.isEmpty)) 
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

class SettingsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);
    
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Change Password button
              ElevatedButton(
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
              
              // Backup Management button (admin only)
              if (auth.role == "admin") ...[
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () => Navigator.pushNamed(context, '/backup_management'),
                  icon: const Icon(Icons.backup),
                  label: const Text('Database Backup Management'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    foregroundColor: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Create, restore, and manage database backups',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ],
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
      // Use Future.microtask to avoid blocking UI thread
      await Future.microtask(() async {
        final result = await auth.changePassword(_oldPassCtrl.text, _newPassCtrl.text);
        
        if (mounted) {
          setState(() { _loading = false; });
          if (result == true) {
            Navigator.pop(context);
            ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Password changed successfully')));
          }
        }
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString().replaceFirst('Exception: ', '');
        });
      }
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
