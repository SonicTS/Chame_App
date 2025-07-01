import 'package:flutter/material.dart';
import 'package:chame_flutter/data/py_bride.dart';

/// Show a simplified deletion dialog that automatically determines the best deletion method
/// Returns true if deletion was successful, false if cancelled, null if error
Future<bool?> showSimpleDeletionDialog({
  required BuildContext context,
  required String entityType,
  required int entityId,
  required String entityName,
  String deletedBy = "flutter_admin",
}) async {
  return showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (context) => SimpleDeletionDialog(
      entityType: entityType,
      entityId: entityId,
      entityName: entityName,
      deletedBy: deletedBy,
    ),
  );
}

class SimpleDeletionDialog extends StatefulWidget {
  final String entityType;
  final int entityId;
  final String entityName;
  final String deletedBy;

  const SimpleDeletionDialog({
    super.key,
    required this.entityType,
    required this.entityId,
    required this.entityName,
    required this.deletedBy,
  });

  @override
  State<SimpleDeletionDialog> createState() => _SimpleDeletionDialogState();
}

class _SimpleDeletionDialogState extends State<SimpleDeletionDialog> {
  final PyBridge _pyBridge = PyBridge();
  
  bool _isAnalyzing = true;
  bool _isDeleting = false;
  String? _errorMessage;
  
  // Analysis results
  String _deletionType = 'unknown';
  List<String> _warnings = [];
  List<Map<String, dynamic>> _dependencies = [];
  bool _canProceed = false;

  @override
  void initState() {
    super.initState();
    _analyzeImpact();
  }

  Future<void> _analyzeImpact() async {
    try {
      setState(() {
        _isAnalyzing = true;
        _errorMessage = null;
      });

      final analysis = await _pyBridge.analyzeDeletionImpact(
        entityType: widget.entityType,
        entityId: widget.entityId,
      );

      setState(() {
        _deletionType = analysis['deletion_type'] ?? 'unknown';
        _warnings = List<String>.from(analysis['warnings'] ?? []);
        _dependencies = List<Map<String, dynamic>>.from(analysis['dependencies'] ?? []);
        _canProceed = analysis['can_proceed'] ?? false;
        _isAnalyzing = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to analyze deletion impact: $e';
        _isAnalyzing = false;
        _canProceed = false;
      });
    }
  }

  Future<void> _executeDeletion() async {
    try {
      setState(() {
        _isDeleting = true;
        _errorMessage = null;
      });

      final result = await _pyBridge.executeDeletion(
        entityType: widget.entityType,
        entityId: widget.entityId,
        deletedBy: widget.deletedBy,
      );

      if (result['success'] == true) {
        // Show success message briefly
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['message'] ?? 'Deletion successful'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 2),
            ),
          );
          
          // Close dialog with success
          Navigator.of(context).pop(true);
        }
      } else {
        setState(() {
          _errorMessage = result['message'] ?? 'Deletion failed';
          _isDeleting = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to execute deletion: $e';
        _isDeleting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Delete ${widget.entityName}'),
      content: SizedBox(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_isAnalyzing) ...[
              const Row(
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 12),
                  Text('Analyzing deletion impact...'),
                ],
              ),
            ] else if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  border: Border.all(color: Colors.red.shade200),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.error, color: Colors.red.shade700, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: TextStyle(color: Colors.red.shade700),
                      ),
                    ),
                  ],
                ),
              ),
            ] else if (_canProceed) ...[
              // Show deletion type and impact
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _deletionType == 'hard' ? Colors.orange.shade50 : Colors.blue.shade50,
                  border: Border.all(
                    color: _deletionType == 'hard' ? Colors.orange.shade200 : Colors.blue.shade200,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          _deletionType == 'hard' ? Icons.delete_forever : Icons.visibility_off,
                          color: _deletionType == 'hard' ? Colors.orange.shade700 : Colors.blue.shade700,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _deletionType == 'hard' 
                              ? 'Will be permanently deleted'
                              : 'Will be soft deleted (can be restored)',
                            style: TextStyle(
                              color: _deletionType == 'hard' ? Colors.orange.shade700 : Colors.blue.shade700,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (_deletionType == 'hard') ...[
                      const SizedBox(height: 4),
                      Text(
                        'This action cannot be undone!',
                        style: TextStyle(
                          color: Colors.orange.shade600,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              
              // Show warnings
              if (_warnings.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Text(
                  'Impact:',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                ...(_warnings.map((warning) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.info_outline, size: 16, color: Colors.blue.shade600),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          warning,
                          style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                        ),
                      ),
                    ],
                  ),
                ))),
              ],
              
              // Show dependencies
              if (_dependencies.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Text(
                  'Dependencies:',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                Container(
                  constraints: const BoxConstraints(maxHeight: 120),
                  child: SingleChildScrollView(
                    child: Column(
                      children: _dependencies.map((dep) => Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.link, size: 16, color: Colors.grey.shade600),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                '${dep['description']} (${dep['count']} records)',
                                style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                              ),
                            ),
                          ],
                        ),
                      )).toList(),
                    ),
                  ),
                ),
              ],
            ] else ...[
              const Text('Cannot proceed with deletion due to errors.'),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isAnalyzing || _isDeleting ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        if (_errorMessage != null) ...[
          TextButton(
            onPressed: _isAnalyzing || _isDeleting ? null : _analyzeImpact,
            child: const Text('Retry'),
          ),
        ],
        if (_canProceed && _errorMessage == null) ...[
          ElevatedButton(
            onPressed: _isAnalyzing || _isDeleting ? null : _executeDeletion,
            style: ElevatedButton.styleFrom(
              backgroundColor: _deletionType == 'hard' ? Colors.red : Colors.orange,
              foregroundColor: Colors.white,
            ),
            child: _isDeleting
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : Text(_deletionType == 'hard' ? 'Delete Permanently' : 'Soft Delete'),
          ),
        ],
      ],
    );
  }
}
