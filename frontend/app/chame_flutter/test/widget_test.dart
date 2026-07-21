// App-level smoke tests: boots the real widget tree (ChameApp -> AuthGate)
// with a faked backend/storage and checks it lands on the expected screen.
// This is the Flutter analogue of the backend's
// `test_default_admin_bootstrap.py`: verifying the app's initial state is
// sane on a "fresh install" as well as once logged in.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:chame_flutter/main.dart';
import 'package:chame_flutter/services/auth_service.dart';

import 'helpers/fake_py_bridge_channel.dart';
import 'helpers/fake_secure_storage.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late FakePyBridgeChannel bridge;

  setUp(() {
    bridge = FakePyBridgeChannel()..install();
  });

  tearDown(() {
    bridge.uninstall();
  });

  testWidgets('shows the login screen on a fresh install', (tester) async {
    installFakeSecureStorage();
    bridge.onReturn('get_all_users', <Map<String, dynamic>>[]);

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthService>(
        create: (_) => AuthService(),
        child: const ChameApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Login'), findsOneWidget);
    expect(find.text('Chame App Home'), findsNothing);
  });

  testWidgets('shows the home page once a user is logged in', (tester) async {
    installFakeSecureStorage();
    bridge.onReturn('login', {'user_id': 1, 'role': 'admin'});

    // `testWidgets` runs its callback inside a FakeAsync zone, where a bare
    // `Future.delayed` never fires because the fake clock only advances via
    // `tester.pump(...)`. `runAsync` steps out to the real zone so this
    // AuthService setup (and its real secure-storage Future) can actually
    // complete before we build the widget tree.
    final auth = await tester.runAsync(() async {
      final auth = AuthService();
      while (!auth.initialized) {
        await Future<void>.delayed(Duration.zero);
      }
      await auth.login('admin', 'secret');
      return auth;
    });

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthService>.value(
        value: auth!,
        child: const ChameApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Chame App Home'), findsOneWidget);
    expect(find.text('Purchase'), findsOneWidget);
  });
}
