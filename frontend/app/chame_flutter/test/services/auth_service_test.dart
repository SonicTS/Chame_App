// Tests for AuthService: login/logout/change-password flows plus the
// "god user" visibility filtering. These mirror the backend's
// `test_role_change.py` / `test_admin_api_visibility.py`: instead of a real
// temp sqlite database, the native PyBridge channel and secure storage are
// faked, and instead of `services.admin_api`, `AuthService` is exercised
// directly.
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:chame_flutter/services/auth_service.dart';

import '../helpers/fake_py_bridge_channel.dart';
import '../helpers/fake_secure_storage.dart';

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

  // AuthService kicks off an async, unawaited read from secure storage in
  // its constructor. Waiting for `initialized` here avoids a race where that
  // read (which sees the empty fake storage) resolves *after* a test's own
  // login()/logout() call and clobbers the state it just set.
  Future<AuthService> freshAuthService() async {
    final auth = AuthService();
    while (!auth.initialized) {
      await Future<void>.delayed(Duration.zero);
    }
    return auth;
  }

  group('login', () {
    test('succeeds and stores user id/role when the backend accepts the credentials', () async {
      bridge.onReturn('login', {'user_id': 7, 'role': 'admin'});

      final auth = await freshAuthService();
      final success = await auth.login('admin', 'secret');

      expect(success, isTrue);
      expect(auth.isLoggedIn, isTrue);
      expect(auth.currentUserId, 7);
      expect(auth.role, 'admin');
    });

    test('returns false when the backend reports invalid credentials', () async {
      bridge.onReturn('login', null);

      final auth = await freshAuthService();
      final success = await auth.login('admin', 'wrong-password');

      expect(success, isFalse);
      expect(auth.isLoggedIn, isFalse);
    });

    test('throws with the backend message when the platform channel reports an error', () async {
      bridge.onError('login', message: 'Backend unavailable');

      final auth = await freshAuthService();
      expect(
        () => auth.login('admin', 'secret'),
        throwsA(isA<Exception>().having((e) => e.toString(), 'message', contains('Backend unavailable'))),
      );
    });
  });

  group('logout', () {
    test('clears the logged-in state', () async {
      bridge
        ..onReturn('login', {'user_id': 1, 'role': 'admin'})
        ..onReturn('logout', null);

      final auth = await freshAuthService();
      await auth.login('admin', 'secret');
      expect(auth.isLoggedIn, isTrue);

      await auth.logout();

      expect(auth.isLoggedIn, isFalse);
      expect(auth.currentUserId, isNull);
      expect(auth.role, '');
    });
  });

  group('changePassword', () {
    test('defaults to changing the currently logged-in user', () async {
      bridge
        ..onReturn('login', {'user_id': 3, 'role': 'wirt'})
        ..onReturn('change_password', null);

      final auth = await freshAuthService();
      await auth.login('wirt', 'secret');

      final result = await auth.changePassword('old-pass', 'new-pass');

      expect(result, isTrue);
      final call = bridge.calls.firstWhere((c) => c.method == 'change_password');
      expect(call.arguments['user_id'], 3);
      expect(call.arguments['old_password'], 'old-pass');
      expect(call.arguments['new_password'], 'new-pass');
    });

    test('targets an explicit user id when provided', () async {
      bridge
        ..onReturn('login', {'user_id': 3, 'role': 'admin'})
        ..onReturn('change_password', null);

      final auth = await freshAuthService();
      await auth.login('admin', 'secret');

      await auth.changePassword('old-pass', 'new-pass', targetUserId: 42);

      final call = bridge.calls.firstWhere((c) => c.method == 'change_password');
      expect(call.arguments['user_id'], 42);
    });

    test('fails when nobody is logged in and no target user is given', () async {
      final auth = await freshAuthService();
      final result = await auth.changePassword('old-pass', 'new-pass');
      expect(result, isFalse);
    });
  });

  group('god user visibility', () {
    final usersWithGod = [
      {'user_id': 1, 'name': 'admin', 'role': 'admin'},
      {'user_id': 2, 'name': 'god', 'role': 'god'},
    ];

    test('hides the god user from non-god viewers', () async {
      bridge.onReturn('login', {'user_id': 1, 'role': 'admin'});
      final auth = await freshAuthService();
      await auth.login('admin', 'secret');

      final visible = auth.filterVisibleUsers(usersWithGod);

      expect(visible.any((u) => u['role'] == 'god'), isFalse);
      expect(visible.map((u) => u['user_id']), [1]);
    });

    test('shows the god user to a god viewer', () async {
      bridge.onReturn('login', {'user_id': 2, 'role': 'god'});
      final auth = await freshAuthService();
      await auth.login('god', 'secret');

      final visible = auth.filterVisibleUsers(usersWithGod);

      expect(visible.any((u) => u['role'] == 'god'), isTrue);
    });

    test('hides records linked to a known god user id from non-god viewers', () async {
      bridge.onReturn('login', {'user_id': 1, 'role': 'admin'});
      final auth = await freshAuthService();
      await auth.login('admin', 'secret');

      // Remember which ids are "god" by first filtering a user list that
      // includes the god user (mirrors how the purchase/sales pages first
      // load users, then filter transaction-like records).
      auth.filterVisibleUsers(usersWithGod);

      final records = [
        {'transaction_id': 100, 'user_id': 1},
        {'transaction_id': 101, 'user_id': 2}, // linked to the god user
      ];

      final visible = auth.filterVisibleRecords(records);

      expect(visible.map((r) => r['transaction_id']), [100]);
    });
  });
}
