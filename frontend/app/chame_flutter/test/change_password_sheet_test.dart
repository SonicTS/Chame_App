// Widget tests for ChangePasswordSheet, covering the "add a user selector,
// default it to the current user" feature.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:chame_flutter/main.dart';
import 'package:chame_flutter/services/auth_service.dart';
import 'package:chame_flutter/widgets/shared/user_dropdown_selector.dart';

import 'helpers/fake_py_bridge_channel.dart';
import 'helpers/fake_secure_storage.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late FakePyBridgeChannel bridge;
  late AuthService auth;

  setUp(() async {
    bridge = FakePyBridgeChannel()..install();
    installFakeSecureStorage();

    bridge.onReturn('login', {'user_id': 1, 'role': 'admin'});
    auth = AuthService();
    while (!auth.initialized) {
      await Future<void>.delayed(Duration.zero);
    }
    await auth.login('admin', 'secret');
  });

  tearDown(() {
    bridge.uninstall();
  });

  Widget buildSheet() {
    return ChangeNotifierProvider<AuthService>.value(
      value: auth,
      child: const MaterialApp(
        home: Scaffold(body: ChangePasswordSheet()),
      ),
    );
  }

  testWidgets('defaults the user selector to the currently logged-in user', (tester) async {
    bridge.onReturn('get_all_users', [
      {'user_id': 1, 'name': 'admin', 'role': 'admin'},
      {'user_id': 2, 'name': 'wirt_bob', 'role': 'wirt'},
    ]);

    await tester.pumpWidget(buildSheet());
    await tester.pumpAndSettle();

    final selector = tester.widget<UserDropdownSelector>(find.byType(UserDropdownSelector));
    expect(selector.selectedUserId, 1);
  });

  testWidgets('changing your own password still requires the old password', (tester) async {
    // Admins must never submit their current password; they must use
    // admin_change_password even when changing their own password.
    bridge
      ..onReturn('get_all_users', [
        {'user_id': 1, 'name': 'admin', 'role': 'admin'},
        {'user_id': 2, 'name': 'wirt_bob', 'role': 'wirt'},
      ])
      ..onReturn('admin_change_password', null);

    await tester.pumpWidget(buildSheet());
    await tester.pumpAndSettle();

    // Admin should not see the "Current Password" field for any action
    expect(find.widgetWithText(TextField, 'Current Password'), findsNothing);

    await tester.enterText(find.widgetWithText(TextField, 'New Password'), 'new-pass');
    await tester.enterText(find.widgetWithText(TextField, 'Confirm New Password'), 'new-pass');

    await tester.tap(find.widgetWithText(ElevatedButton, 'Change'));
    await tester.pumpAndSettle();

    final call = bridge.calls.firstWhere((c) => c.method == 'admin_change_password');
    expect(call.arguments['user_id'], 1);
    expect(call.arguments.containsKey('old_password'), isFalse);
    expect(call.arguments['new_password'], 'new-pass');
    expect(bridge.calls.any((c) => c.method == 'change_password'), isFalse);
  });

  testWidgets('admin resetting another user\'s password does not ask for the old password', (tester) async {
    bridge
      ..onReturn('get_all_users', [
        {'user_id': 1, 'name': 'admin', 'role': 'admin'},
        {'user_id': 2, 'name': 'wirt_bob', 'role': 'wirt'},
      ])
      ..onReturn('admin_change_password', null);

    await tester.pumpWidget(buildSheet());
    await tester.pumpAndSettle();

    // Select the other user directly through the widget's callback: driving
    // the third-party dropdown's popup route isn't worth the brittleness
    // here, the wiring from selection -> _selectedUserId is what matters.
    final selector = tester.widget<UserDropdownSelector>(find.byType(UserDropdownSelector));
    selector.onChanged({'user_id': 2, 'name': 'wirt_bob', 'role': 'wirt'});
    await tester.pumpAndSettle();

    // No "Current Password" field should be shown for an admin resetting
    // someone else's password.
    expect(find.widgetWithText(TextField, 'Current Password'), findsNothing);

    await tester.enterText(find.widgetWithText(TextField, 'New Password'), 'new-pass');
    await tester.enterText(find.widgetWithText(TextField, 'Confirm New Password'), 'new-pass');

    await tester.tap(find.widgetWithText(ElevatedButton, 'Change'));
    await tester.pumpAndSettle();

    final call = bridge.calls.firstWhere((c) => c.method == 'admin_change_password');
    expect(call.arguments['user_id'], 2);
    expect(call.arguments.containsKey('old_password'), isFalse);
    expect(call.arguments['new_password'], 'new-pass');
    expect(bridge.calls.any((c) => c.method == 'change_password'), isFalse);
  });


  testWidgets('shows an error and does not submit when passwords do not match', (tester) async {
    bridge.onReturn('get_all_users', [
      {'user_id': 1, 'name': 'admin', 'role': 'admin'},
    ]);

    await tester.pumpWidget(buildSheet());
    await tester.pumpAndSettle();

    // Admins don't see the current-password field; just fill new/confirm
    await tester.enterText(find.widgetWithText(TextField, 'New Password'), 'new-pass');
    await tester.enterText(find.widgetWithText(TextField, 'Confirm New Password'), 'something-else');

    await tester.tap(find.widgetWithText(ElevatedButton, 'Change'));
    await tester.pumpAndSettle();

    expect(find.text('Passwords do not match'), findsOneWidget);
    expect(bridge.calls.any((c) => c.method == 'change_password'), isFalse);
    expect(bridge.calls.any((c) => c.method == 'admin_change_password'), isFalse);
  });
}
