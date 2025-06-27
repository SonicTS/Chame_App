import 'package:flutter/material.dart';
import '../data/py_bride.dart';

class BackupManagementPage extends StatefulWidget {
  @override
  _BackupManagementPageState createState() => _BackupManagementPageState();
}

class _BackupManagementPageState extends State<BackupManagementPage> {
  final PyBridge _pyBridge = PyBridge();
  List<Map<String, dynamic>> _backups = [];
  bool _loading = false;
  bool _creating = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadBackups();
  }

  Future<void> _loadBackups() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final backups = await _pyBridge.listBackups();
      setState(() {
        _backups = backups;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load backups: ${e.toString()}';
        _loading = false;
      });
    }
  }

  Future<void> _createBackup() async {
    // Show description dialog
    String? description = await _showDescriptionDialog();
    if (description == null) return; // User cancelled

    setState(() {
      _creating = true;
      _error = null;
    });

    try {
      final result = await _pyBridge.createBackup(
        backupType: "manual",
        description: description,
        createdBy: "admin_user",
      );

      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backup created successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        await _loadBackups(); // Refresh the list
      } else {
        throw Exception(result['message'] ?? 'Unknown error');
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to create backup: ${e.toString()}';
      });
    } finally {
      setState(() {
        _creating = false;
      });
    }
  }

  Future<String?> _showDescriptionDialog() async {
    String description = '';
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Create Backup'),
        content: TextField(
          onChanged: (value) => description = value,
          decoration: InputDecoration(
            labelText: 'Description (optional)',
            hintText: 'e.g., Before major update',
          ),
          maxLines: 2,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, description),
            child: Text('Create'),
          ),
        ],
      ),
    );
  }

  Future<void> _restoreBackup(Map<String, dynamic> backup) async {
    // Show confirmation dialog
    final confirmed = await _showRestoreConfirmationDialog(backup);
    if (!confirmed) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final result = await _pyBridge.restoreBackup(
        backupPath: backup['path'],
        confirm: true,
      );

      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Database restored successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        await _loadBackups(); // Refresh the list
      } else {
        throw Exception(result['message'] ?? 'Unknown error');
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to restore backup: ${e.toString()}';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Future<bool> _showRestoreConfirmationDialog(Map<String, dynamic> backup) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Restore Backup'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Are you sure you want to restore this backup?',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text('⚠️ This will overwrite your current database!'),
            SizedBox(height: 16),
            Text('Backup Details:'),
            Text('• Created: ${backup['created_at'] ?? 'Unknown'}'),
            Text('• Type: ${backup['backup_type'] ?? 'Unknown'}'),
            if (backup['description']?.isNotEmpty == true)
              Text('• Description: ${backup['description']}'),
            Text('• Size: ${_formatFileSize(backup['size'] ?? 0)}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Restore', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    ) ?? false;
  }

  Future<void> _deleteBackup(Map<String, dynamic> backup) async {
    final confirmed = await _showDeleteConfirmationDialog(backup);
    if (!confirmed) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final result = await _pyBridge.deleteBackup(
        backupFilename: backup['filename'],
      );

      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backup deleted successfully!'),
            backgroundColor: Colors.orange,
          ),
        );
        await _loadBackups(); // Refresh the list
      } else {
        throw Exception(result['message'] ?? 'Unknown error');
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to delete backup: ${e.toString()}';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Future<bool> _showDeleteConfirmationDialog(Map<String, dynamic> backup) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete Backup'),
        content: Text('Are you sure you want to delete this backup? This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Delete', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    ) ?? false;
  }

  String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }

  String _formatDate(String? dateStr) {
    if (dateStr == null) return 'Unknown';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr; // Return as-is if parsing fails
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Database Backup Management'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Header with create backup button
          Container(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'Manage database backups',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                    ),
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: _creating ? null : _createBackup,
                  icon: _creating 
                      ? SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(Icons.backup),
                  label: Text(_creating ? 'Creating...' : 'Create Backup'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
          Divider(height: 1),
          
          // Error message
          if (_error != null)
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(16),
              color: Colors.red[50],
              child: Text(
                _error!,
                style: TextStyle(color: Colors.red[800]),
              ),
            ),
          
          // Backup list
          Expanded(
            child: _loading && _backups.isEmpty
                ? Center(child: CircularProgressIndicator())
                : _backups.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.backup, size: 64, color: Colors.grey),
                            SizedBox(height: 16),
                            Text(
                              'No backups found',
                              style: TextStyle(
                                fontSize: 18,
                                color: Colors.grey[600],
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Create your first backup to get started',
                              style: TextStyle(color: Colors.grey[500]),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: _backups.length,
                        itemBuilder: (context, index) {
                          final backup = _backups[index];
                          return Card(
                            margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: Colors.teal[100],
                                child: Icon(
                                  Icons.backup,
                                  color: Colors.teal[700],
                                ),
                              ),
                              title: Text(
                                backup['filename'] ?? 'Unknown',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  if (backup['description']?.isNotEmpty == true)
                                    Text(backup['description']),
                                  Text('Created: ${_formatDate(backup['created_at'])}'),
                                  Text('Type: ${backup['backup_type'] ?? 'Unknown'} • Size: ${_formatFileSize(backup['size'] ?? 0)}'),
                                ],
                              ),
                              isThreeLine: true,
                              trailing: PopupMenuButton<String>(
                                onSelected: (action) {
                                  switch (action) {
                                    case 'restore':
                                      _restoreBackup(backup);
                                      break;
                                    case 'delete':
                                      _deleteBackup(backup);
                                      break;
                                  }
                                },
                                itemBuilder: (context) => [
                                  PopupMenuItem(
                                    value: 'restore',
                                    child: Row(
                                      children: [
                                        Icon(Icons.restore, color: Colors.blue),
                                        SizedBox(width: 8),
                                        Text('Restore'),
                                      ],
                                    ),
                                  ),
                                  PopupMenuItem(
                                    value: 'delete',
                                    child: Row(
                                      children: [
                                        Icon(Icons.delete, color: Colors.red),
                                        SizedBox(width: 8),
                                        Text('Delete'),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loadBackups,
        child: Icon(Icons.refresh),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        tooltip: 'Refresh backup list',
      ),
    );
  }
}
