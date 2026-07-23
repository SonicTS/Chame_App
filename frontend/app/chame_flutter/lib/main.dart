import 'package:chame_flutter/pages/add_ingredients_page.dart';
import 'package:chame_flutter/pages/add_product_page.dart';
import 'package:chame_flutter/pages/add_user_page.dart';
import 'package:chame_flutter/pages/backup_management_page.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/services/auto_backup_service.dart';
import 'package:chame_flutter/widgets/shared/user_dropdown_selector.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:provider/provider.dart';
import 'package:flutter/services.dart';
import 'pages/ingredients_page.dart';
import 'pages/login/login_page.dart';
import 'pages/products_page.dart';
import 'pages/purchase/purchase_page.dart';
import 'pages/toast_round_page.dart';
import 'pages/users_page.dart';
import 'pages/bank_page.dart';
import 'data/py_bride.dart';
import 'pages/restock_ingredients_page.dart';
import 'pages/return_pfand.dart';
import 'pages/receipt_scan/receipt_scan_page.dart';
import 'pages/receipt_parsing_settings_page.dart';

// Global method channel for reverse bridge calls
const MethodChannel _reverseBridgeChannel = MethodChannel('samples.flutter.dev/chame/python');

// Setup reverse bridge listener for Python → Flutter calls
void _setupReverseBridge() {
  try {
  //print('🌉 Setting up method call handler for reverse bridge...');
    _reverseBridgeChannel.setMethodCallHandler(_handleReverseBridgeCall);
  //print('✅ Reverse bridge method call handler configured successfully');
  //print('   Channel: ${_reverseBridgeChannel.name}');
  //print('   Handler: _handleReverseBridgeCall');
  } catch (e) {
  //print('❌ Failed to setup reverse bridge: $e');
    rethrow;
  }
}

// Handle calls from Python through the bridge
Future<void> _handleReverseBridgeCall(MethodCall call) async {
  final String callTimestamp = DateTime.now().toIso8601String();
  
  try {
    print('📞 [FLUTTER-BRIDGE] Received reverse bridge call at $callTimestamp');
    print('   Method: ${call.method}');
    print('   Arguments type: ${call.arguments?.runtimeType}');
    
    switch (call.method) {
      case 'log_to_firebase':
        print('🔥 [FLUTTER-BRIDGE] Handling Firebase logging request...');
        await _handleFirebaseLog(call.arguments);
        print('✅ [FLUTTER-BRIDGE] Firebase logging request completed');
        break;
      case 'update_progress':
        print('📊 [FLUTTER-BRIDGE] Handling progress update...');
        await _handleProgressUpdate(call.arguments);
        print('✅ [FLUTTER-BRIDGE] Progress update completed');
        break;
      case 'show_notification':
        print('🔔 [FLUTTER-BRIDGE] Handling notification request...');
        await _handleShowNotification(call.arguments);
        print('✅ [FLUTTER-BRIDGE] Notification request completed');
        break;
      case 'test_bridge':
        print('🧪 [FLUTTER-BRIDGE] Bridge test request received');
        await _handleBridgeTest(call.arguments);
        print('✅ [FLUTTER-BRIDGE] Bridge test completed');
        break;
      default:
        print('❓ [FLUTTER-BRIDGE] Unknown reverse bridge method called: ${call.method}');
        print('   Available methods: log_to_firebase, update_progress, show_notification, test_bridge');
    }
    
    print('✅ [FLUTTER-BRIDGE] Reverse bridge call ${call.method} processed successfully');
    
  } catch (e, stackTrace) {
    print('💥 [FLUTTER-BRIDGE] Error handling reverse bridge call ${call.method}: $e');
    // print('📍 Stack trace: $stackTrace');
    // print('🔍 Call arguments: ${call.arguments}');
    
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
      //print('🆘 Logged reverse bridge error to Firebase');
    } catch (logError) {
      //print('☠️ Failed to log reverse bridge error: $logError');
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
    
    print('🚀 [FLUTTER-FIREBASE] Processing Firebase log request at $timestamp');
    print('   Level: $level');
    print('   Message: $message');
    print('   Metadata keys: ${metadata.keys.toList()}');
    
    // Log to Firebase Crashlytics (queues locally)
    try {
      FirebaseCrashlytics.instance.log('[$level] Python: $message');
      print('📝 [FLUTTER-FIREBASE] ✓ Log queued locally in Firebase Crashlytics');
    } catch (logError) {
      print('❌ [FLUTTER-FIREBASE] Failed to queue log: $logError');
      rethrow;
    }
    
    // Set custom keys for context
    try {
      print('� [FLUTTER-FIREBASE] Setting ${metadata.length} custom keys...');
      metadata.forEach((key, value) {
        final keyName = 'python_$key';
        final keyValue = value.toString();
        FirebaseCrashlytics.instance.setCustomKey(keyName, keyValue);
        print('   ✓ Set custom key: $keyName = $keyValue');
      });
      print('✅ [FLUTTER-FIREBASE] All custom keys set successfully');
    } catch (keyError) {
      print('❌ [FLUTTER-FIREBASE] Failed to set custom keys: $keyError');
      rethrow;
    }
    
    // Record as non-fatal error for better visibility (queues locally)
    try {
      print('📊 [FLUTTER-FIREBASE] Queuing non-fatal error report...');
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
      print('✅ [FLUTTER-FIREBASE] ✓ Non-fatal error report queued locally');
    } catch (recordError) {
      print('❌ [FLUTTER-FIREBASE] Failed to queue error report: $recordError');
      rethrow;
    }
    
    // Set breadcrumb for tracking
    try {
      print('🍞 [FLUTTER-FIREBASE] Setting breadcrumb data...');
      FirebaseCrashlytics.instance.setCustomKey('last_python_log', '[$level] $message');
      FirebaseCrashlytics.instance.setCustomKey('last_python_log_time', timestamp);
      print('✅ [FLUTTER-FIREBASE] Breadcrumb data set successfully');
    } catch (breadcrumbError) {
      print('❌ [FLUTTER-FIREBASE] Failed to set breadcrumb data: $breadcrumbError');
      rethrow;
    }
    
    print('🔥 [FLUTTER-FIREBASE] Firebase log processing completed (data queued locally)');
    print('   Summary: [$level] Python: $message');
    print('   ℹ️ Note: Data will be uploaded when app has network connectivity');
    if (metadata.isNotEmpty) {
      print('   📦 Metadata: $metadata');
    }
    
  } catch (e, stackTrace) {
    print('💥 [FLUTTER-FIREBASE] Critical error in _handleFirebaseLog: $e');
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
      print('🆘 [FLUTTER-FIREBASE] Successfully logged the logging error to Firebase');
    } catch (metaError) {
      print('☠️ [FLUTTER-FIREBASE] Failed to log the logging error: $metaError');
    }
  }
}

// Handle progress updates from Python
Future<void> _handleProgressUpdate(Map<dynamic, dynamic> arguments) async {
  final String timestamp = DateTime.now().toIso8601String();
  
  try {
    final double progress = (arguments['progress'] as num?)?.toDouble() ?? 0.0;
    final String message = arguments['message']?.toString() ?? '';
    
  //print('📊 Progress update received at $timestamp');
  //print('   Progress: ${(progress * 100).toStringAsFixed(1)}%');
  //print('   Message: $message');
    
    // You can emit this to a stream or update UI state here
  //print('✅ Progress update processed successfully');
    
  } catch (e) {
  //print('❌ Error processing progress update: $e');
  //print('🔍 Arguments: $arguments');
  }
}

// Handle notifications from Python
Future<void> _handleShowNotification(Map<dynamic, dynamic> arguments) async {
  final String timestamp = DateTime.now().toIso8601String();
  
  try {
    final String title = arguments['title']?.toString() ?? '';
    final String message = arguments['message']?.toString() ?? '';
    final String type = arguments['type']?.toString() ?? 'info';
    
  //print('🔔 Notification received at $timestamp');
  //print('   Type: $type');
  //print('   Title: $title');
  //print('   Message: $message');
    
    // You can show actual notifications here using flutter_local_notifications
  //print('✅ Notification processed successfully');
    
  } catch (e) {
  //print('❌ Error processing notification: $e');
  //print('🔍 Arguments: $arguments');
  }
}

// Initialize Python backend asynchronously to avoid blocking main thread
void _initializePythonBackend() {
  final String initTimestamp = DateTime.now().toIso8601String();
//print('🐍 Starting Python backend initialization at $initTimestamp');
  
  Future.microtask(() async {
    try {
    //print('📡 Attempting to ping Python backend...');
      await PyBridge().ping();
    //print('✅ Python backend ping successful!');
      
      // Test logging immediately with detailed logging
      try {
      //print('📝 Writing success log to Firebase Crashlytics...');
        FirebaseCrashlytics.instance.log('Python backend connection successful');
      //print('✅ Successfully wrote connection log to Firebase');
        
      //print('📊 Recording success event to Firebase...');
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
      //print('✅ Successfully recorded connection event to Firebase');
        
      } catch (logError) {
      //print('❌ Failed to log success to Firebase: $logError');
      }
      
    } catch (e, stack) {
    print('❌ Failed to ping Python backend:');
    print('   Error: $e');
    print('   Stack: $stack');
      
      // Log the failure to Firebase with detailed logging
      try {
      //print('🆘 Logging backend failure to Firebase...');
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
      //print('✅ Successfully logged backend failure to Firebase');
        
      } catch (logError) {
      print('💥 Critical: Failed to log backend failure to Firebase: $logError');
      }
    }
  });
}

void main() async {
  final String appStartTimestamp = DateTime.now().toIso8601String();
//print('🚀 App startup initiated at $appStartTimestamp');
  
  WidgetsFlutterBinding.ensureInitialized();
//print('✅ Flutter widgets binding initialized');
  
  // Initialize Firebase with detailed logging
  try {
  //print('🔥 Initializing Firebase...');
    await Firebase.initializeApp();
  //print('✅ Firebase initialized successfully');
    
  //print('📊 Setting up Firebase error handling...');
    FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;
  //print('✅ Firebase error handling configured');
    
  } catch (firebaseError, stackTrace) {
  //print('💥 Critical: Firebase initialization failed!');
  //print('   Error: $firebaseError');
  //print('   Stack: $stackTrace');
    // Continue anyway, but log to console
  }
  
  // Setup reverse bridge for Python logging with logging
  try {
  //print('🌉 Setting up reverse bridge for Python logging...');
    _setupReverseBridge();
  //print('✅ Reverse bridge setup completed');
  } catch (bridgeError) {
  //print('❌ Failed to setup reverse bridge: $bridgeError');
  }
  
  // Test Firebase logging immediately with detailed logging
  try {
  //print('🧪 Testing Firebase logging functionality...');
    
    FirebaseCrashlytics.instance.log('App starting - Firebase logging test');
  //print('✅ Firebase log test completed');
    
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
  //print('✅ Firebase recordError test completed');
    
  } catch (testError) {
  //print('❌ Firebase logging test failed: $testError');
  }
  
  // Initialize Python backend asynchronously to avoid ANR
//print('🐍 Scheduling Python backend initialization...');
  _initializePythonBackend();
  
//print('🎯 Starting Flutter app...');
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthService(),
      child: ChameApp(),
    ),
  );
//print('✅ Flutter app started successfully');
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
    return auth.isLoggedIn ? HomePage() : const LoginScreen();
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
            '/add_user': (_) => AddUserPage(),
            '/restock_ingredients': (_) => RestockIngredientsPage(),
            '/receipt_scan': (_) => const ReceiptScanPage(),
            '/receipt_parsing_settings': (_) => const ReceiptParsingSettingsPage(),
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

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    // Opportunistic check: creates a rotating automatic backup if one is
    // due (per the interval/retention configured on the Backup Management
    // page). No-op if disabled or not due yet; failures are swallowed so
    // they never block normal app usage.
    final auth = Provider.of<AuthService>(context, listen: false);
    if (auth.hasAdminRights) {
      AutoBackupService().maybeRunAutomaticBackup();
    }
  }

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
                      if (auth.hasAdminRights) ElevatedButton(
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
                      if (auth.hasAdminRights)
                        ElevatedButton(
                          onPressed: () => Navigator.pushNamed(context, '/restock_ingredients'),
                          child: const Text('Restock Ingredients'),
                        ),
                      if (auth.hasAdminRights)
                        ElevatedButton(
                          onPressed: () => Navigator.pushNamed(context, '/receipt_scan'),
                          child: const Text('Scan Receipt'),
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
                  builder: (ctx) => const ChangePasswordSheet(),
                  shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                  ),
                ),
                child: const Text('Change Password'),
              ),
              
              // Backup Management button (admin only)
              if (auth.hasAdminRights) ...[
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
              
              // Firebase Bridge Test button
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => _testFirebaseBridge(context),
                icon: const Icon(Icons.bug_report),
                label: const Text('Test Firebase Bridge'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Test Firebase logging bridge between Python and Flutter',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ChangePasswordSheet extends StatefulWidget {
  const ChangePasswordSheet({super.key});

  @override
  State<ChangePasswordSheet> createState() => _ChangePasswordSheetState();
}

class _ChangePasswordSheetState extends State<ChangePasswordSheet> {
  final _oldPassCtrl = TextEditingController();
  final _newPassCtrl = TextEditingController();
  final _confirmPassCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  late Future<List<Map<String, dynamic>>> _usersFuture;
  int? _selectedUserId;

  @override
  void initState() {
    super.initState();
    final auth = Provider.of<AuthService>(context, listen: false);
    _selectedUserId = auth.currentUserId;
    _usersFuture = PyBridge().getAllUsers().then(auth.filterVisibleUsers);
  }

  void _changePassword() async {
    setState(() { _loading = true; _error = null; });
    if (_newPassCtrl.text != _confirmPassCtrl.text) {
      setState(() { _loading = false; _error = 'Passwords do not match'; });
      return;
    }
    final auth = Provider.of<AuthService>(context, listen: false);
    final targetUserId = _selectedUserId;
    final isAdmin = auth.hasAdminRights;
    try {
      // Use Future.microtask to avoid blocking UI thread
      await Future.microtask(() async {
        final result = isAdmin
            ? await auth.adminResetPassword(targetUserId ?? auth.currentUserId!, _newPassCtrl.text)
            : await auth.changePassword(
                _oldPassCtrl.text,
                _newPassCtrl.text,
                targetUserId: targetUserId,
              );

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
    final auth = Provider.of<AuthService>(context, listen: false);
    final isAdmin = auth.hasAdminRights;
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
            if (isAdmin)
              FutureBuilder<List<Map<String, dynamic>>>(
                future: _usersFuture,
                builder: (context, snap) {
                  if (snap.connectionState == ConnectionState.waiting) {
                    return const Padding(
                      padding: EdgeInsets.only(bottom: 16),
                      child: LinearProgressIndicator(),
                    );
                  }
                  final users = snap.data ?? const <Map<String, dynamic>>[];
                  if (users.isEmpty) return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: UserDropdownSelector(
                      users: users,
                      selectedUserId: _selectedUserId,
                      label: 'User',
                      onChanged: (user) => setState(() {
                        _selectedUserId = user?['user_id'] as int?;
                      }),
                    ),
                  );
                },
              )
            else
              // Non-admins only change their own password — use a hidden
              // placeholder to keep existing logic that reads _selectedUserId.
              SizedBox(height: 0),
            if (isAdmin)
              const Padding(
                padding: EdgeInsets.only(bottom: 8),
                child: Text(
                    'As an admin, you can reset any user\'s password without '
                    'knowing their current one. Admins must not submit their current password.',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              )
            else
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

// Handle bridge test from Python
Future<void> _handleBridgeTest(Map<dynamic, dynamic>? arguments) async {
  final String timestamp = DateTime.now().toIso8601String();
  
  try {
    final String testType = arguments?['test_type']?.toString() ?? 'general';
    final String testMessage = arguments?['message']?.toString() ?? 'Bridge test';
    
    print('🧪 [FLUTTER-BRIDGE] Bridge test received at $timestamp');
    print('   Test Type: $testType');
    print('   Test Message: $testMessage');
    
    // Log to Firebase to test the full pipeline
    try {
      FirebaseCrashlytics.instance.log('🧪 Bridge Test: $testMessage');
      FirebaseCrashlytics.instance.recordError(
        'Bridge Test - $testType',
        null,
        fatal: false,
        information: [
          'Test_type: $testType',
          'Test_message: $testMessage', 
          'Timestamp: $timestamp',
          'Source: Flutter_bridge_test',
        ],
      );
      print('✅ [FLUTTER-BRIDGE] Bridge test logged to Firebase successfully');
    } catch (logError) {
      print('❌ [FLUTTER-BRIDGE] Bridge test Firebase logging failed: $logError');
    }
    
  } catch (e) {
    print('❌ [FLUTTER-BRIDGE] Error processing bridge test: $e');
  }
}

// Test Firebase bridge functionality
Future<void> _testFirebaseBridge(BuildContext context) async {
  print('🧪 [FLUTTER-TEST] Starting Firebase bridge test...');
  
  try {
    // Test 1: Direct Flutter Firebase logging with different methods
    print('📝 [FLUTTER-TEST] Testing direct Flutter Firebase logging...');
    print('ℹ️ [FLUTTER-TEST] Note: These calls only QUEUE data locally, they don\'t send immediately');
    
    // Method 1: Simple log
    FirebaseCrashlytics.instance.log('🧪 Direct Flutter Firebase test - Simple Log');
    print('📝 [FLUTTER-TEST] ✓ Simple log queued locally');
    
    // Method 2: Record error with more visibility
    FirebaseCrashlytics.instance.recordError(
      'Flutter Firebase Bridge Test - HIGH PRIORITY',
      StackTrace.current,
      fatal: false,
      information: [
        'Test_type: Direct_Flutter_logging',
        'Timestamp: ${DateTime.now().toIso8601String()}',
        'Source: Settings_page_test',
        'Priority: HIGH',
        'Visibility: ENHANCED',
      ],
    );
    print('📊 [FLUTTER-TEST] ✓ Non-fatal error queued locally');
    
    // Method 3: Set user identifier for easier tracking
    await FirebaseCrashlytics.instance.setUserIdentifier('flutter_test_user');
    print('👤 [FLUTTER-TEST] ✓ User identifier set');
    
    // Method 4: Set custom keys for filtering
    await FirebaseCrashlytics.instance.setCustomKey('test_session', DateTime.now().millisecondsSinceEpoch.toString());
    await FirebaseCrashlytics.instance.setCustomKey('test_type', 'firebase_bridge_test');
    await FirebaseCrashlytics.instance.setCustomKey('app_version', 'debug_test');
    print('🔑 [FLUTTER-TEST] ✓ Custom keys set');
    
    // Method 5: Create a more visible error
    FirebaseCrashlytics.instance.recordError(
      'FIREBASE LOGGING TEST - PLEASE CHECK CONSOLE',
      null,
      fatal: false,
      information: [
        'This is a test log to verify Firebase integration',
        'Check Firebase Console > Crashlytics > Non-fatal issues',
        'Project: chamekasse',
        'App: com.chame.kasse',
        'Test_timestamp: ${DateTime.now().toIso8601String()}',
        'If you see this in Firebase Console, logging is working!',
      ],
    );
    print('🎯 [FLUTTER-TEST] ✓ High-visibility test error queued locally');
    
    print('✅ [FLUTTER-TEST] All Firebase logs queued locally (not yet sent to server)');
    
    // Test 2: Attempt to force send to Firebase
    bool forceSendSuccess = false;
    try {
      print('📤 [FLUTTER-TEST] Attempting to force send queued reports...');
      await FirebaseCrashlytics.instance.sendUnsentReports();
      forceSendSuccess = true;
      print('✅ [FLUTTER-TEST] Force send command executed (but actual upload depends on network)');
    } catch (e) {
      print('❌ [FLUTTER-TEST] Force send not available or failed: $e');
    }
    
    // Test 3: Python bridge test
    print('🐍 [FLUTTER-TEST] Testing Python Firebase bridge...');
    bool pythonBridgeSuccess = false;
    try {
      await PyBridge().testFirebaseLogging();
      pythonBridgeSuccess = true;
      print('✅ [FLUTTER-TEST] Python Firebase bridge communication successful');
    } catch (e) {
      print('❌ [FLUTTER-TEST] Python Firebase bridge test failed: $e');
    }
    
    // Show realistic success message
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('🧪 Firebase bridge test completed!'),
              const SizedBox(height: 4),
              const Text('📝 Logs QUEUED locally (not yet sent)'),
              const SizedBox(height: 4),
              Text('📤 Force send: ${forceSendSuccess ? "✅ Attempted" : "❌ Failed"}'),
              const SizedBox(height: 4),
              Text('🐍 Python bridge: ${pythonBridgeSuccess ? "✅ Working" : "❌ Failed"}'),
              const SizedBox(height: 4),
              const Text('📍 Project: chamekasse'),
              const SizedBox(height: 4),
              const Text('⏱️ Upload happens when app has network + background time'),
              const SizedBox(height: 4),
              const Text('📊 Check Firebase Console after network reconnect'),
            ],
          ),
          backgroundColor: pythonBridgeSuccess ? Colors.green : Colors.orange,
          duration: const Duration(seconds: 10),
          action: SnackBarAction(
            label: 'Console',
            textColor: Colors.white,
            onPressed: () {
              print('🌐 Firebase Console: https://console.firebase.google.com/project/chamekasse/crashlytics');
            },
          ),
        ),
      );
    }
    
  } catch (e) {
    print('❌ [FLUTTER-TEST] Firebase bridge test failed: $e');
    
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Firebase bridge test failed: $e'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 5),
        ),
      );
    }
  }
}
