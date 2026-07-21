import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// Test double for the native PyBridge method channel
/// (`samples.flutter.dev/chame/python`).
///
/// This plays the same role for widget/unit tests that the backend's
/// temporary sqlite database (`tmp_path` + `reset_database()`) plays for the
/// Python test suite: a fully controlled, disposable stand-in for "the
/// backend" so the Flutter side can be tested without a real Python process.
///
/// Usage:
/// ```dart
/// final bridge = FakePyBridgeChannel()
///   ..onReturn('get_all_users', [{'user_id': 1, 'name': 'admin', 'role': 'admin'}]);
/// setUp(() => bridge.install());
/// tearDown(() => bridge.uninstall());
/// ```
class FakePyBridgeChannel {
  static const MethodChannel channel = MethodChannel('samples.flutter.dev/chame/python');

  final Map<String, dynamic Function(MethodCall call)> _handlers = {};

  /// Every method call received while installed, in order. Useful for
  /// asserting the app called the backend with the expected arguments.
  final List<MethodCall> calls = [];

  /// Registers a handler that computes the response for [method] from the
  /// incoming [MethodCall].
  void on(String method, dynamic Function(MethodCall call) handler) {
    _handlers[method] = handler;
  }

  /// Registers a fixed response for [method]. Lists/maps are JSON-encoded
  /// first, matching how the real bridge returns collection data as a JSON
  /// string.
  void onReturn(String method, dynamic value) {
    on(method, (_) => value is String ? value : jsonEncode(value));
  }

  /// Registers [method] to throw a [PlatformException], simulating a
  /// backend-reported error (e.g. wrong password, validation failure).
  void onError(String method, {String code = 'error', String? message}) {
    on(method, (_) => throw PlatformException(code: code, message: message));
  }

  void install() {
    calls.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call);
      final handler = _handlers[call.method];
      if (handler == null) {
        throw MissingPluginException('No fake handler registered for ${call.method}');
      }
      return handler(call);
    });
  }

  void uninstall() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  }
}
