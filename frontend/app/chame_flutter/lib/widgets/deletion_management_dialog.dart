import 'package:flutter/material.dart';
import '../data/py_bride.dart';

class DeletionManagementDialog extends StatefulWidget {
  final String entityType; // "user", "product", "ingredient"
  final int entityId;
  final String entityName;

  const DeletionManagementDialog({
    Key? key,
    required this.entityType,
    required this.entityId,
    required this.entityName,
  }) : super(key: key);

  @override
  _DeletionManagementDialogState createState() => _DeletionManagementDialogState();
}

class _DeletionManagementDialogState extends State<DeletionManagementDialog> {
  final PyBridge _pyBridge = PyBridge();
  bool _loading = true;
  bool _deleting = false;
  Map<String, dynamic>? _dependencies;
  String? _error;
  bool _forceDelete = false;

  @override
  void initState() {
    super.initState();
    _checkDependencies();
  }

  Future<void> _checkDependencies() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final deps = await _pyBridge.checkDeletionDependencies(
        entityType: widget.entityType,
        entityId: widget.entityId,
      );
      setState(() {
        _dependencies = deps;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to check dependencies: ${e.toString()}';
        _loading = false;
      });
    }
  }

  Future<void> _performDeletion() async {
    setState(() {
      _deleting = true;
      _error = null;
    });

    try {
      Map<String, dynamic> result;
      
      switch (widget.entityType) {
        case 'user':
          result = await _pyBridge.safeDeleteUser(
            userId: widget.entityId,
            force: _forceDelete,
          );
          break;
        case 'product':
          result = await _pyBridge.safeDeleteProduct(
            productId: widget.entityId,
            force: _forceDelete,
          );
          break;
        case 'ingredient':
          result = await _pyBridge.safeDeleteIngredient(
            ingredientId: widget.entityId,
            force: _forceDelete,
          );
          break;
        default:
          throw Exception('Unknown entity type: ${widget.entityType}');
      }

      if (result['success'] == true) {
        Navigator.of(context).pop(true); // Signal successful deletion
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Deleted successfully'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        throw Exception(result['message'] ?? 'Unknown error');
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to delete: ${e.toString()}';
        _deleting = false;
      });
    }
  }

  Widget _buildDependencyList(List<dynamic> items, String title, Color color) {
    if (items.isEmpty) return Container();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 8),
        ...items.map((item) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(
            children: [
              Icon(Icons.circle, size: 6, color: color),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${item['table']}: ${item['count']} records - ${item['action']}',
                  style: TextStyle(fontSize: 14),
                ),
              ),
            ],
          ),
        )).toList(),
        const SizedBox(height: 16),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Delete ${widget.entityType.toUpperCase()}: ${widget.entityName}'),
      content: SizedBox(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red[300]!),
                ),
                child: Text(
                  _error!,
                  style: TextStyle(color: Colors.red[800]),
                ),
              )
            else if (_dependencies != null) ...[
              // Blocking records
              _buildDependencyList(
                _dependencies!['blocking_records'] ?? [],
                '🚫 Blocking Dependencies',
                Colors.red,
              ),
              
              // Warnings
              _buildDependencyList(
                _dependencies!['warnings'] ?? [],
                '⚠️ Warnings',
                Colors.orange,
              ),
              
              // Safe to delete
              _buildDependencyList(
                _dependencies!['safe_to_delete'] ?? [],
                '✅ Will be deleted automatically',
                Colors.green,
              ),
              
              if (_dependencies!['can_delete'] != true) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.orange[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange[300]!),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Force Delete Option',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.orange[800],
                        ),
                      ),
                      const SizedBox(height: 8),
                      CheckboxListTile(
                        value: _forceDelete,
                        onChanged: (value) => setState(() => _forceDelete = value ?? false),
                        title: Text(
                          'Force delete (may break data integrity)',
                          style: TextStyle(fontSize: 14),
                        ),
                        subtitle: Text(
                          'This will delete the record and set nullable foreign keys to NULL',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                        controlAffinity: ListTileControlAffinity.leading,
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _deleting ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: (_deleting || (_dependencies?['can_delete'] != true && !_forceDelete)) 
              ? null 
              : _performDeletion,
          style: ElevatedButton.styleFrom(
            backgroundColor: _forceDelete ? Colors.red : Colors.orange,
            foregroundColor: Colors.white,
          ),
          child: _deleting
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(_forceDelete ? 'Force Delete' : 'Delete'),
        ),
      ],
    );
  }
}

// Helper function to show the deletion dialog
Future<bool?> showDeletionDialog({
  required BuildContext context,
  required String entityType,
  required int entityId,
  required String entityName,
}) {
  return showDialog<bool>(
    context: context,
    builder: (context) => DeletionManagementDialog(
      entityType: entityType,
      entityId: entityId,
      entityName: entityName,
    ),
  );
}
