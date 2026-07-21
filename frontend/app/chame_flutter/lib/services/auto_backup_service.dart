import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../data/py_bride.dart';

/// User-adjustable configuration for the automatic backup service.
class AutoBackupSettings {
  final bool enabled;
  final int intervalDays;
  final int keepCount;

  const AutoBackupSettings({
    required this.enabled,
    required this.intervalDays,
    required this.keepCount,
  });

  static const defaults = AutoBackupSettings(
    enabled: false,
    intervalDays: 3,
    keepCount: 5,
  );

  AutoBackupSettings copyWith({
    bool? enabled,
    int? intervalDays,
    int? keepCount,
  }) {
    return AutoBackupSettings(
      enabled: enabled ?? this.enabled,
      intervalDays: intervalDays ?? this.intervalDays,
      keepCount: keepCount ?? this.keepCount,
    );
  }
}

/// Creates a rotating automatic database backup every [AutoBackupSettings.intervalDays]
/// days, keeping only the [AutoBackupSettings.keepCount] most recent automatic
/// backups (older ones are deleted).
///
/// There's no always-running background process on mobile, so this instead
/// checks "is a backup due?" opportunistically (e.g. once per app session,
/// see [maybeRunAutomaticBackup]) and creates one immediately if so. Settings
/// and the last-run timestamp are persisted in secure storage so the check
/// survives app restarts.
class AutoBackupService {
  static const _enabledKey = 'auto_backup_enabled';
  static const _intervalDaysKey = 'auto_backup_interval_days';
  static const _keepCountKey = 'auto_backup_keep_count';
  static const _lastRunKey = 'auto_backup_last_run';

  // Automatic backups are identifiable by this backup_type (see
  // services/database_backup.py's create_backup/list_backups): the backend
  // doesn't have a dedicated folder for it, so it's filed alongside manual
  // backups, but the type is preserved in the filename/metadata.
  static const backupType = 'automatic';

  final FlutterSecureStorage _storage;
  final PyBridge _pyBridge;

  AutoBackupService({
    FlutterSecureStorage? storage,
    PyBridge? pyBridge,
  })  : _storage = storage ?? const FlutterSecureStorage(),
        _pyBridge = pyBridge ?? PyBridge();

  Future<AutoBackupSettings> loadSettings() async {
    final enabledRaw = await _storage.read(key: _enabledKey);
    final intervalRaw = await _storage.read(key: _intervalDaysKey);
    final keepRaw = await _storage.read(key: _keepCountKey);

    return AutoBackupSettings(
      enabled: enabledRaw == 'true',
      intervalDays: int.tryParse(intervalRaw ?? '') ??
          AutoBackupSettings.defaults.intervalDays,
      keepCount:
          int.tryParse(keepRaw ?? '') ?? AutoBackupSettings.defaults.keepCount,
    );
  }

  Future<void> saveSettings(AutoBackupSettings settings) async {
    await _storage.write(key: _enabledKey, value: settings.enabled.toString());
    await _storage.write(
      key: _intervalDaysKey,
      value: settings.intervalDays.toString(),
    );
    await _storage.write(
      key: _keepCountKey,
      value: settings.keepCount.toString(),
    );
  }

  Future<DateTime?> _getLastRunTime() async {
    final raw = await _storage.read(key: _lastRunKey);
    if (raw == null) return null;
    return DateTime.tryParse(raw);
  }

  Future<void> _setLastRunTime(DateTime time) async {
    await _storage.write(key: _lastRunKey, value: time.toIso8601String());
  }

  /// Checks whether an automatic backup is due (enabled, and either never
  /// run before or the configured interval has elapsed since the last run),
  /// and if so creates one and prunes old automatic backups down to the
  /// configured retention count. Safe to call opportunistically (e.g. once
  /// per app session) -- it's a no-op when not due, and failures are
  /// swallowed since this shouldn't block normal app usage.
  Future<void> maybeRunAutomaticBackup() async {
    try {
      final settings = await loadSettings();
      if (!settings.enabled) return;

      final lastRun = await _getLastRunTime();
      final due = lastRun == null ||
          DateTime.now().difference(lastRun) >=
              Duration(days: settings.intervalDays);
      if (!due) return;

      await _pyBridge.createBackup(
        backupType: backupType,
        description: 'Automatic scheduled backup',
        createdBy: 'auto_backup_service',
      );
      await _setLastRunTime(DateTime.now());

      await _pruneOldAutomaticBackups(settings.keepCount);
    } catch (e) {
      // Automatic backups are best-effort; don't let a failure here
      // interrupt normal app usage. The user can still create/manage
      // backups manually from the Backup Management page.
      // ignore: avoid_print
      print('AutoBackupService: automatic backup failed: $e');
    }
  }

  Future<void> _pruneOldAutomaticBackups(int keepCount) async {
    final backups = await _pyBridge.listBackups();
    final automaticBackups = backups
        .where((b) => (b['filename'] as String? ?? '').contains('_${backupType}_'))
        .toList()
      ..sort((a, b) => (b['created_at'] as String? ?? '')
          .compareTo(a['created_at'] as String? ?? ''));

    if (automaticBackups.length <= keepCount) return;

    for (final backup in automaticBackups.skip(keepCount)) {
      final filename = backup['filename'] as String?;
      if (filename == null) continue;
      try {
        await _pyBridge.deleteBackup(backupFilename: filename);
      } catch (e) {
        // Keep pruning the rest even if one delete fails.
        // ignore: avoid_print
        print('AutoBackupService: failed to delete old backup $filename: $e');
      }
    }
  }
}
