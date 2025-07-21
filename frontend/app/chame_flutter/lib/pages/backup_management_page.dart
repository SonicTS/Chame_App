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
        contentPadding: EdgeInsets.fromLTRB(16, 20, 16, 0),
        content: Container(
          width: MediaQuery.of(context).size.width * 0.95,
          constraints: BoxConstraints(
            maxWidth: 400, // Maximum width for larger screens
          ),
          child: TextField(
            onChanged: (value) => description = value,
            decoration: InputDecoration(
              labelText: 'Description (optional)',
              hintText: 'e.g., Before major update',
            ),
            maxLines: 2,
          ),
        ),
        actions: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('Cancel'),
                ),
              ),
              SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context, description),
                  child: Text('Create'),
                ),
              ),
            ],
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
        contentPadding: EdgeInsets.fromLTRB(16, 20, 16, 0),
        content: Container(
          width: MediaQuery.of(context).size.width * 0.95,
          constraints: BoxConstraints(
            maxWidth: 400, // Maximum width for larger screens
          ),
          child: SingleChildScrollView(
            child: Column(
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
          ),
        ),
        actions: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: Text('Cancel'),
                ),
              ),
              SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context, true),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                  child: Text('Restore', style: TextStyle(color: Colors.white)),
                ),
              ),
            ],
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

  Future<void> _downloadFromServer() async {
    final result = await _showServerBackupSelectionDialog();
    if (result == null) return;

    try {
      setState(() => _loading = true);
      
      final downloadResult = await _pyBridge.downloadBackupFromServer(
        serverConfig: result['serverConfig'],
        remoteFilename: result['selectedFile'],
      );

      if (downloadResult['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backup downloaded successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        await _loadBackups(); // Refresh the list
      } else {
        throw Exception(downloadResult['message'] ?? 'Download failed');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<Map<String, dynamic>?> _showServerBackupSelectionDialog() async {
    final formKey = GlobalKey<FormState>();
    String serverUrl = 'http://minecraftwgwg.hopto.org:5050';
    List<dynamic> availableFiles = [];
    bool isLoading = false;
    String? selectedFile;
    String? errorMessage;

    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Text('Download Backup from Server'),
          contentPadding: EdgeInsets.fromLTRB(16, 20, 16, 0),
          content: Container(
            width: MediaQuery.of(context).size.width * 0.95,
            constraints: BoxConstraints(
              maxHeight: MediaQuery.of(context).size.height * 0.7,
              maxWidth: 500, // Maximum width for larger screens
            ),
            child: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Info about server download
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.purple[50],
                        border: Border.all(color: Colors.purple[300]!),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              Icon(Icons.cloud_download, color: Colors.purple[700], size: 20),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Download Backup from Server',
                                  style: TextStyle(
                                    fontSize: 14, 
                                    fontWeight: FontWeight.w500,
                                    color: Colors.purple[800]
                                  ),
                                ),
                              ),
                            ],
                          ),
                          SizedBox(height: 8),
                          Text(
                            'Select a .db backup file from your server to download.',
                            style: TextStyle(fontSize: 12, color: Colors.purple[700]),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 16),
                    
                    TextFormField(
                      initialValue: serverUrl,
                      decoration: InputDecoration(
                        labelText: 'Server URL',
                        hintText: 'http://yourserver.com:port',
                        prefixIcon: Icon(Icons.link),
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value?.isEmpty == true) return 'URL is required';
                        if (!value!.startsWith('http')) return 'URL must start with http:// or https://';
                        return null;
                      },
                      onChanged: (value) => serverUrl = value,
                    ),
                    SizedBox(height: 12),
                    
                    // Load files button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: isLoading ? null : () async {
                          if (formKey.currentState?.validate() == true) {
                            setState(() {
                              isLoading = true;
                              errorMessage = null;
                            });
                            
                            try {
                              final config = {
                                'method': 'http',
                                'url': '$serverUrl/list',
                              };
                              
                              final result = await _pyBridge.listServerBackups(serverConfig: config);
                              
                              if (result['success'] == true) {
                                // Filter to only show .db files
                                final allFiles = result['files'] as List<dynamic>? ?? [];
                                final dbFiles = allFiles.where((file) {
                                  final fileName = file['filename'] as String? ?? '';
                                  return fileName.toLowerCase().endsWith('.db');
                                }).toList();
                                
                                setState(() {
                                  availableFiles = dbFiles;
                                  selectedFile = null;
                                  if (dbFiles.isEmpty) {
                                    errorMessage = 'No .db backup files found on server';
                                  }
                                });
                              } else {
                                setState(() {
                                  errorMessage = result['message'] as String? ?? 'Failed to load files';
                                });
                              }
                            } catch (e) {
                              setState(() {
                                errorMessage = 'Error: ${e.toString()}';
                              });
                            } finally {
                              setState(() {
                                isLoading = false;
                              });
                            }
                          }
                        },
                        icon: isLoading 
                            ? SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                            : Icon(Icons.refresh),
                        label: Text(isLoading ? 'Loading...' : 'Load Available Files'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                    SizedBox(height: 12),
                    
                    // Error message
                    if (errorMessage != null)
                      Container(
                        width: double.infinity,
                        padding: EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.red[50],
                          border: Border.all(color: Colors.red[300]!),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          errorMessage!,
                          style: TextStyle(color: Colors.red[800], fontSize: 12),
                        ),
                      ),
                    
                    // File selection dropdown
                    if (availableFiles.isNotEmpty) ...[
                      SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        decoration: InputDecoration(
                          labelText: 'Select Backup File (.db)',
                          prefixIcon: Icon(Icons.file_present),
                          border: OutlineInputBorder(),
                        ),
                        value: selectedFile,
                        items: availableFiles.map((file) {
                          final fileName = file['filename'] as String? ?? 'Unknown';
                          final fileSize = file['size'] as int? ?? 0;
                          final modified = file['modified'] as String? ?? '';
                          
                          return DropdownMenuItem<String>(
                            value: fileName,
                            child: Tooltip(
                              message: 'Size: ${_formatFileSize(fileSize)} • Modified: ${_formatServerDate(modified)}',
                              child: Text(
                                fileName,
                                style: TextStyle(
                                  fontWeight: FontWeight.w500,
                                  fontSize: 14,
                                ),
                                overflow: TextOverflow.ellipsis,
                                maxLines: 1,
                              ),
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            selectedFile = value;
                          });
                        },
                        validator: (value) {
                          if (value == null || value.isEmpty) return 'Please select a file';
                          return null;
                        },
                        isExpanded: true,
                      ),
                      
                      // Show selected file details
                      if (selectedFile != null) ...[
                        SizedBox(height: 12),
                        Container(
                          width: double.infinity,
                          padding: EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.blue[50],
                            border: Border.all(color: Colors.blue[300]!),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Selected File Details:',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue[800],
                                  fontSize: 12,
                                ),
                              ),
                              SizedBox(height: 4),
                              ...availableFiles.where((file) => file['filename'] == selectedFile).map((file) {
                                final fileSize = file['size'] as int? ?? 0;
                                final modified = file['modified'] as String? ?? '';
                                return Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '• Size: ${_formatFileSize(fileSize)}',
                                      style: TextStyle(fontSize: 11, color: Colors.blue[700]),
                                    ),
                                    Text(
                                      '• Modified: ${_formatServerDate(modified)}',
                                      style: TextStyle(fontSize: 11, color: Colors.blue[700]),
                                    ),
                                  ],
                                );
                              }).toList(),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ],
                ),
              ),
            ),
          ),
          actions: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Expanded(
                  child: TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text('Cancel'),
                  ),
                ),
                SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: (selectedFile != null) ? () {
                      if (formKey.currentState?.validate() == true) {
                        Navigator.pop(context, {
                          'serverConfig': {
                            'method': 'http',
                            'url': '$serverUrl/download',
                          },
                          'selectedFile': selectedFile,
                        });
                      }
                    } : null,
                    child: Text('Download'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _importFromShare() async {
    try {
      setState(() => _loading = true);
      
      // Pick file from Android file picker
      final filePath = await _pyBridge.pickFileForImport();
      if (filePath == null) {
        setState(() => _loading = false);
        return; // User cancelled
      }
      
      // Import the selected file
      final importResult = await _pyBridge.importBackupFromShare(
        sharedFilePath: filePath,
      );

      if (importResult['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backup imported successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        await _loadBackups(); // Refresh the list
      } else {
        throw Exception(importResult['message'] ?? 'Import failed');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Import failed: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _exportToServer(Map<String, dynamic> backup) async {
    final result = await _showServerUploadDialog(backup);
    if (result == null) return;

    try {
      setState(() => _loading = true);
      
      final uploadResult = await _pyBridge.uploadBackupToServer(
        backupFilename: backup['filename'],
        serverConfig: result['serverConfig'],
      );

      if (uploadResult['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backup uploaded to server successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        throw Exception(uploadResult['message'] ?? 'Upload failed');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Upload failed: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<Map<String, dynamic>?> _showServerUploadDialog(Map<String, dynamic> backup) async {
    final formKey = GlobalKey<FormState>();
    String serverUrl = 'http://minecraftwgwg.hopto.org:5050';
    String remoteFilename = backup['filename'] ?? 'backup.db';

    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Upload Backup to Server'),
        contentPadding: EdgeInsets.fromLTRB(16, 20, 16, 0),
        content: Container(
          width: MediaQuery.of(context).size.width * 0.95,
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(context).size.height * 0.7,
            maxWidth: 500, // Maximum width for larger screens
          ),
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Info about server upload
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green[50],
                      border: Border.all(color: Colors.green[300]!),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            Icon(Icons.cloud_upload, color: Colors.green[700], size: 20),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Upload Backup to Server',
                                style: TextStyle(
                                  fontSize: 14, 
                                  fontWeight: FontWeight.w500,
                                  color: Colors.green[800]
                                ),
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Upload this backup file to your server for remote storage.',
                          style: TextStyle(fontSize: 12, color: Colors.green[700]),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(height: 16),
                  
                  // Backup info
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Backup to Upload:', style: TextStyle(fontWeight: FontWeight.bold)),
                        SizedBox(height: 4),
                        Text('• File: ${backup['filename']}'),
                        Text('• Size: ${_formatFileSize(backup['size'] ?? 0)}'),
                        Text('• Created: ${_formatDate(backup['created_at'])}'),
                        if (backup['description']?.isNotEmpty == true)
                          Text('• Description: ${backup['description']}'),
                      ],
                    ),
                  ),
                  SizedBox(height: 16),
                  
                  TextFormField(
                    initialValue: serverUrl,
                    decoration: InputDecoration(
                      labelText: 'Server URL',
                      hintText: 'http://yourserver.com:port',
                      prefixIcon: Icon(Icons.link),
                      border: OutlineInputBorder(),
                    ),
                    validator: (value) {
                      if (value?.isEmpty == true) return 'URL is required';
                      if (!value!.startsWith('http')) return 'URL must start with http:// or https://';
                      return null;
                    },
                    onChanged: (value) => serverUrl = value,
                  ),
                  SizedBox(height: 12),
                  
                  TextFormField(
                    initialValue: remoteFilename,
                    decoration: InputDecoration(
                      labelText: 'Remote Filename',
                      hintText: 'backup.db',
                      prefixIcon: Icon(Icons.file_present),
                      border: OutlineInputBorder(),
                    ),
                    validator: (value) {
                      if (value?.isEmpty == true) return 'Filename is required';
                      if (!value!.toLowerCase().endsWith('.db')) return 'Filename must end with .db';
                      return null;
                    },
                    onChanged: (value) => remoteFilename = value,
                  ),
                ],
              ),
            ),
          ),
        ),
        actions: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('Cancel'),
                ),
              ),
              SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    if (formKey.currentState?.validate() == true) {
                      Navigator.pop(context, {
                        'serverConfig': {
                          'method': 'http',
                          'url': '$serverUrl/upload',
                        },
                        'remoteFilename': remoteFilename,
                      });
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                  ),
                  child: Text('Upload'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _exportViaShare(Map<String, dynamic> backup) async {
    try {
      setState(() => _loading = true);
      
      await _pyBridge.shareFile(
        filePath: backup['path'],
        title: 'Share Backup: ${backup['filename']}',
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Backup shared successfully!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Share failed: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  String _formatServerDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr; // Return as-is if parsing fails
    }
  }

  Future<bool> _showDeleteConfirmationDialog(Map<String, dynamic> backup) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete Backup'),
        contentPadding: EdgeInsets.fromLTRB(16, 20, 16, 0),
        content: Container(
          width: MediaQuery.of(context).size.width * 0.95,
          constraints: BoxConstraints(
            maxWidth: 400, // Maximum width for larger screens
          ),
          child: Text('Are you sure you want to delete this backup? This action cannot be undone.'),
        ),
        actions: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: Text('Cancel'),
                ),
              ),
              SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context, true),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                  child: Text('Delete', style: TextStyle(color: Colors.white)),
                ),
              ),
            ],
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
            child: Column(
              children: [
                Row(
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
                  ],
                ),
                SizedBox(height: 12),
                // First row - Create and Download
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
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
                    ),
                    SizedBox(width: 8),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _loading ? null : _downloadFromServer,
                        icon: Icon(Icons.cloud_download),
                        label: Text('Download from Server'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.purple,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 8),
                // Second row - Import only (full width)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _loading ? null : _importFromShare,
                    icon: Icon(Icons.file_upload),
                    label: Text('Import from Device'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                    ),
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
                                    case 'export_server':
                                      _exportToServer(backup);
                                      break;
                                    case 'export_share':
                                      _exportViaShare(backup);
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
                                  PopupMenuDivider(),
                                  PopupMenuItem(
                                    value: 'export_server',
                                    child: Row(
                                      children: [
                                        Icon(Icons.cloud_upload, color: Colors.green),
                                        SizedBox(width: 8),
                                        Text('Export to Server'),
                                      ],
                                    ),
                                  ),
                                  PopupMenuItem(
                                    value: 'export_share',
                                    child: Row(
                                      children: [
                                        Icon(Icons.share, color: Colors.orange),
                                        SizedBox(width: 8),
                                        Text('Share via Android'),
                                      ],
                                    ),
                                  ),
                                  PopupMenuDivider(),
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
