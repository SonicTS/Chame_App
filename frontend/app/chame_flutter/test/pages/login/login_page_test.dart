// Widget tests for the login screen. Mirrors, at the Flutter layer, what
// the backend's login-related tests check: that the right users are
// offered for quick-login, that a sane fallback exists when none are found,
// and that submitting actually calls through to auth.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:chame_flutter/pages/login/login_page.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/widgets/shared/user_dropdown_selector.dart';

import '../../helpers/fake_py_bridge_channel.dart';
import '../../helpers/fake_secure_storage.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late FakePyBridgeChannel bridge;

  setUp(() {
    bridge = FakePyBridgeChannel()..install();
    installFakeSecureStorage();
  });

  tearDown(() {
    bridge.uninstall();
  });

  Widget buildLoginScreen() {
    return ChangeNotifierProvider<AuthService>(
      create: (_) => AuthService(),
      child: const MaterialApp(home: LoginScreen()),
    );
  }

  testWidgets('shows a quick-login dropdown for admin/wirt users and hides manual fields', (tester) async {
    bridge.onReturn('get_all_users', [
      {'user_id': 1, 'name': 'admin', 'role': 'admin'},
      {'user_id': 2, 'name': 'theresa', 'role': 'wirt'},
      {'user_id': 3, 'name': 'regular_joe', 'role': 'user'},
    ]);

    await tester.pumpWidget(buildLoginScreen());
    await tester.pumpAndSettle();

    expect(find.text('Select User:'), findsOneWidget);
    expect(find.byType(UserDropdownSelector), findsOneWidget);
    // Only the two admin/wirt users should have been offered.
    final selector = tester.widget<UserDropdownSelector>(find.byType(UserDropdownSelector));
    expect(selector.users.map((u) => u['name']), containsAll(['admin', 'theresa']));
    expect(selector.users.any((u) => u['name'] == 'regular_joe'), isFalse);

    // A user is auto-selected, so the manual username field should be hidden.
    expect(
      find.byWidgetPredicate((w) => w is TextField && w.decoration?.labelText == 'Username'),
      findsNothing,
    );
  });

  testWidgets('falls back to manual login when no admin/wirt users are found', (tester) async {
    bridge.onReturn('get_all_users', [
      {'user_id': 3, 'name': 'regular_joe', 'role': 'user'},
    ]);

    await tester.pumpWidget(buildLoginScreen());
    await tester.pumpAndSettle();

    expect(find.textContaining('No admin or wirt users found'), findsOneWidget);
    expect(
      find.byWidgetPredicate((w) => w is TextField && w.decoration?.labelText == 'Username'),
      findsOneWidget,
    );
  });

  testWidgets('"Use Manual Login Instead" switches away from the quick-login dropdown', (tester) async {
    bridge.onReturn('get_all_users', [
      {'user_id': 1, 'name': 'admin', 'role': 'admin'},
    ]);

    await tester.pumpWidget(buildLoginScreen());
    await tester.pumpAndSettle();

    expect(
      find.byWidgetPredicate((w) => w is TextField && w.decoration?.labelText == 'Username'),
      findsNothing,
    );

    await tester.tap(find.text('Use Manual Login Instead'));
    await tester.pumpAndSettle();

    expect(
      find.byWidgetPredicate((w) => w is TextField && w.decoration?.labelText == 'Username'),
      findsOneWidget,
    );
  });

  testWidgets('submitting manual credentials calls through to AuthService.login', (tester) async {
    bridge
      ..onReturn('get_all_users', <Map<String, dynamic>>[])
      ..onReturn('login', {'user_id': 9, 'role': 'admin'});

    await tester.pumpWidget(buildLoginScreen());
    await tester.pumpAndSettle();

    final usernameField = find.byWidgetPredicate((w) => w is TextField && w.decoration?.labelText == 'Username');
    await tester.enterText(usernameField, 'admin');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Log In'));
    await tester.pumpAndSettle();

    final loginCall = bridge.calls.firstWhere((c) => c.method == 'login');
    expect(loginCall.arguments['user'], 'admin');
    expect(find.text('Login failed'), findsNothing);
  });
}
