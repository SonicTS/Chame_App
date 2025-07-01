import 'package:flutter/material.dart';
import '../data/py_bride.dart';

class EnhancedDeletionDialog extends StatefulWidget {
  final String entityType; // "user", "product", "ingredient"
  final int entityId;
  final String entityName;

  const EnhancedDeletionDialog({
    Key? key,
    required this.entityType,
    required this.entityId,
    required this.entityName,
  }) : super(key: key);

  @override
  _EnhancedDeletionDialogState createState() => _EnhancedDeletionDialogState();
}

class _EnhancedDeletionDialogState extends State<EnhancedDeletionDialog> {
  final PyBridge _pyBridge = PyBridge();
  bool _loading = true;
  bool _deleting = false;
  Map<String, dynamic>? _impactAnalysis;
  String? _error;
  bool _hardDelete = false;

  @override
  void initState() {
    super.initState();
    _loadImpactAnalysis();
  }

  Future<void> _loadImpactAnalysis() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final analysis = await _pyBridge.getDeletionImpactAnalysis(
        entityType: widget.entityType,
        entityId: widget.entityId,
      );
      setState(() {
        _impactAnalysis = analysis;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load impact analysis: ${e.toString()}';
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
          result = await _pyBridge.enhancedDeleteUser(
            userId: widget.entityId,
            hardDelete: _hardDelete,
          );
          break;
        case 'product':
          result = await _pyBridge.enhancedDeleteProduct(
            productId: widget.entityId,
            hardDelete: _hardDelete,
          );
          break;
        case 'ingredient':
          result = await _pyBridge.enhancedDeleteIngredient(
            ingredientId: widget.entityId,
            hardDelete: _hardDelete,
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
            backgroundColor: _hardDelete ? Colors.red : Colors.orange,
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

  Widget _buildImpactSection(List<dynamic> items, String title, Color color, IconData icon) {
    if (items.isEmpty) return Container();
    
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: color,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...items.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.arrow_right, size: 16, color: color),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item['description'] ?? item['effect'] ?? '${item['type']}: ${item['count']} items',
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                        ),
                        if (item['name'] != null)
                          Text(
                            item['name'],
                            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            )).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildDeletionTypeSwitch() {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Deletion Type',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
                color: Colors.grey[800],
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Radio<bool>(
                  value: false,
                  groupValue: _hardDelete,
                  onChanged: (value) => setState(() => _hardDelete = value ?? false),
                  activeColor: Colors.orange,
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Soft Delete (Recommended)',
                        style: TextStyle(
                          fontWeight: FontWeight.w500,
                          color: Colors.orange[800],
                        ),
                      ),
                      Text(
                        'Marks as deleted but preserves all data and relationships',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            Row(
              children: [
                Radio<bool>(
                  value: true,
                  groupValue: _hardDelete,
                  onChanged: (value) => setState(() => _hardDelete = value ?? false),
                  activeColor: Colors.red,
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Hard Delete (Permanent)',
                        style: TextStyle(
                          fontWeight: FontWeight.w500,
                          color: Colors.red[800],
                        ),
                      ),
                      Text(
                        'Permanently removes data and may break relationships',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Delete ${widget.entityType.toUpperCase()}: ${widget.entityName}'),
      content: SizedBox(
        width: double.maxFinite,
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(
          children: [
            if (_loading)
              const Expanded(child: Center(child: CircularProgressIndicator()))
            else if (_error != null)
              Expanded(
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.red[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red[300]!),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.error, color: Colors.red[800], size: 48),
                        const SizedBox(height: 16),
                        Text(
                          _error!,
                          style: TextStyle(color: Colors.red[800]),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: _loadImpactAnalysis,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else if (_impactAnalysis != null) ...[
              _buildDeletionTypeSwitch(),
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      // Current deletion type impact
                      if (_hardDelete) ...[
                        if (_impactAnalysis!['hard_deletion'] != null) ...[
                          Text(
                            _impactAnalysis!['hard_deletion']['description'] ?? '',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.red[700],
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          const SizedBox(height: 16),
                          _buildImpactSection(
                            _impactAnalysis!['hard_deletion']['impact']['will_be_deleted'] ?? [],
                            'Will be Permanently Deleted',
                            Colors.red,
                            Icons.delete_forever,
                          ),
                          _buildImpactSection(
                            _impactAnalysis!['hard_deletion']['impact']['will_be_orphaned'] ?? [],
                            'Will Lose References',
                            Colors.orange,
                            Icons.link_off,
                          ),
                        ],
                      ] else ...[
                        if (_impactAnalysis!['soft_deletion'] != null) ...[
                          Text(
                            _impactAnalysis!['soft_deletion']['description'] ?? '',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.orange[700],
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          const SizedBox(height: 16),
                          _buildImpactSection(
                            _impactAnalysis!['soft_deletion']['impact']['will_be_disabled'] ?? [],
                            'Will be Disabled',
                            Colors.orange,
                            Icons.visibility_off,
                          ),
                          _buildImpactSection(
                            _impactAnalysis!['soft_deletion']['impact']['historical_data_preserved'] ?? [],
                            'Historical Data Preserved',
                            Colors.green,
                            Icons.archive,
                          ),
                        ],
                      ],
                      
                      // Common cascade effects
                      if (_impactAnalysis!['soft_deletion'] != null) 
                        _buildImpactSection(
                          _impactAnalysis!['soft_deletion']['impact']['cascade_effects'] ?? [],
                          'Additional Effects',
                          Colors.blue,
                          Icons.waves,
                        ),
                    ],
                  ),
                ),
              ),
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
          onPressed: _deleting ? null : _performDeletion,
          style: ElevatedButton.styleFrom(
            backgroundColor: _hardDelete ? Colors.red : Colors.orange,
            foregroundColor: Colors.white,
          ),
          child: _deleting
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : Text(_hardDelete ? 'Hard Delete' : 'Soft Delete'),
        ),
      ],
    );
  }
}

// Helper function to show the enhanced deletion dialog
Future<bool?> showEnhancedDeletionDialog({
  required BuildContext context,
  required String entityType,
  required int entityId,
  required String entityName,
}) {
  return showDialog<bool>(
    context: context,
    builder: (context) => EnhancedDeletionDialog(
      entityType: entityType,
      entityId: entityId,
      entityName: entityName,
    ),
  );
}
