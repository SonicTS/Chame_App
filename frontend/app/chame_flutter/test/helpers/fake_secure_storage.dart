import 'package:flutter_secure_storage/test/test_flutter_secure_storage_platform.dart';
import 'package:flutter_secure_storage_platform_interface/flutter_secure_storage_platform_interface.dart';

/// Installs an in-memory [FlutterSecureStoragePlatform] so `AuthService`
/// (and anything else backed by `FlutterSecureStorage`) works in tests
/// without a real platform channel.
///
/// Returns the backing map, so tests can seed it (e.g. pre-populate
/// `user_id`/`user_role` to simulate an already-logged-in app) or inspect it
/// after the fact.
Map<String, String> installFakeSecureStorage([Map<String, String>? initial]) {
  final data = initial ?? <String, String>{};
  FlutterSecureStoragePlatform.instance = TestFlutterSecureStoragePlatform(data);
  return data;
}
