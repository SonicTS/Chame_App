import 'package:chame_flutter/data/py_bride.dart';
import 'package:flutter/material.dart';

class FlexibleDeletionDialog extends StatefulWidget {
  final String entityType;
  final int entityId;
  final String entityName;

  const FlexibleDeletionDialog({
    super.key,
    required this.entityType,
    required this.entityId,
    required this.entityName,
  });

  @override
  State<FlexibleDeletionDialog> createState() => _FlexibleDeletionDialogState();
}

class _FlexibleDeletionDialogState extends State<FlexibleDeletionDialog> {
  Map<String, dynamic>? _impactAnalysis;
  Map<String, String> _userChoices = {};
  bool _isLoading = true;
  bool _hardDelete = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadImpactAnalysis();
  }

  Future<void> _loadImpactAnalysis() async {
    try {
      final analysis = await PyBridge().getDeletionImpactAnalysis(
        entityType: widget.entityType,
        entityId: widget.entityId,
      );

      setState(() {
        _impactAnalysis = analysis;
        _isLoading = false;
        
        // Initialize user choices with default actions
        if (analysis['dependencies'] != null) {
          for (var dep in analysis['dependencies']) {
            _userChoices[dep['relationship_name']] = dep['default_action'];
          }
        }
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<Map<String, dynamic>> _performEntitySpecificDeletion() async {
    switch (widget.entityType.toLowerCase()) {
      case 'user':
        return await PyBridge().enhancedDeleteUser(
          userId: widget.entityId,
          hardDelete: _hardDelete,
          cascadeChoices: _userChoices,
        );
      case 'product':
        return await PyBridge().enhancedDeleteProduct(
          productId: widget.entityId,
          hardDelete: _hardDelete,
          cascadeChoices: _userChoices,
        );
      case 'ingredient':
        return await PyBridge().enhancedDeleteIngredient(
          ingredientId: widget.entityId,
          hardDelete: _hardDelete,
          cascadeChoices: _userChoices,
        );
      default:
        throw Exception('Unknown entity type: ${widget.entityType}');
    }
  }

  Future<void> _performDeletion() async {
    try {
      // Show loading dialog
      if (mounted) {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => const AlertDialog(
            content: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 20),
                Text('Deleting...'),
              ],
            ),
          ),
        );
      }

      final result = await _performEntitySpecificDeletion();

      if (mounted) {
        Navigator.pop(context); // Close loading dialog
        Navigator.pop(context, true); // Close deletion dialog with success
        
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('Success'),
            content: Text(result['message'] ?? 'Deletion completed successfully'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('OK'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        try {
          Navigator.pop(context); // Close loading dialog
        } catch (_) {}
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('Error'),
            content: Text('Failed to delete: $e'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('OK'),
              ),
            ],
          ),
        );
      }
    }
  }

  void _onCascadeChoiceChanged(String relationshipName, String newChoice) {
    setState(() {
      _userChoices[relationshipName] = newChoice;
    });
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isSmallDevice = screenWidth < 600;
    
    return AlertDialog(
      title: Text('Delete ${widget.entityType}: ${widget.entityName}'),
      content: SizedBox(
        width: isSmallDevice ? screenWidth * 0.9 : double.maxFinite,
        height: MediaQuery.of(context).size.height * (isSmallDevice ? 0.75 : 0.7),
        child: _buildDialogContent(isSmallDevice),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: (_impactAnalysis?['can_proceed'] == true) ? _performDeletion : null,
          style: ElevatedButton.styleFrom(
            backgroundColor: _hardDelete ? Colors.red : Colors.orange,
          ),
          child: Text(_hardDelete ? 'Permanently Delete' : 'Soft Delete'),
        ),
      ],
    );
  }

  Widget _buildDialogContent(bool isSmallDevice) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (_error != null) {
      return Center(child: Text('Error: $_error'));
    }
    
    if (_impactAnalysis == null) {
      return const Center(child: Text('No data available'));
    }
    
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _DeletionTypeSelector(
            isSmallDevice: isSmallDevice,
            hardDelete: _hardDelete,
            onChanged: (value) => setState(() => _hardDelete = value),
          ),
          const SizedBox(height: 12),
          _WarningsSection(warnings: _impactAnalysis!['warnings']),
          _ErrorsSection(errors: _impactAnalysis!['errors']),
          _DependenciesSection(
            dependencies: _impactAnalysis!['dependencies'],
            userChoices: _userChoices,
            onChoiceChanged: _onCascadeChoiceChanged,
            entityType: widget.entityType,
          ),
        ],
      ),
    );
  }
}

// Extracted widget for deletion type selection
class _DeletionTypeSelector extends StatelessWidget {
  final bool isSmallDevice;
  final bool hardDelete;
  final ValueChanged<bool> onChanged;

  const _DeletionTypeSelector({
    required this.isSmallDevice,
    required this.hardDelete,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Deletion Type:',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 8),
          if (isSmallDevice) ...[
            _buildVerticalRadioOptions(),
          ] else ...[
            _buildHorizontalRadioOptions(),
          ],
        ],
      ),
    );
  }

  Widget _buildVerticalRadioOptions() {
    return Column(
      children: [
        RadioListTile<bool>(
          title: const Text('Soft Delete'),
          subtitle: const Text('Mark as deleted, can be restored'),
          value: false,
          groupValue: hardDelete,
          onChanged: (value) => onChanged(false),
          contentPadding: EdgeInsets.zero,
          dense: true,
        ),
        RadioListTile<bool>(
          title: const Text('Hard Delete'),
          subtitle: const Text('Permanently delete'),
          value: true,
          groupValue: hardDelete,
          onChanged: (value) => onChanged(true),
          contentPadding: EdgeInsets.zero,
          dense: true,
        ),
      ],
    );
  }

  Widget _buildHorizontalRadioOptions() {
    return Row(
      children: [
        Expanded(
          child: RadioListTile<bool>(
            title: const Text('Soft Delete'),
            subtitle: const Text('Mark as deleted, can be restored'),
            value: false,
            groupValue: hardDelete,
            onChanged: (value) => onChanged(false),
          ),
        ),
        Expanded(
          child: RadioListTile<bool>(
            title: const Text('Hard Delete'),
            subtitle: const Text('Permanently delete'),
            value: true,
            groupValue: hardDelete,
            onChanged: (value) => onChanged(true),
          ),
        ),
      ],
    );
  }
}

// Extracted widget for warnings section
class _WarningsSection extends StatelessWidget {
  final dynamic warnings;

  const _WarningsSection({required this.warnings});

  @override
  Widget build(BuildContext context) {
    if (warnings == null || (warnings as List).isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.orange.shade100,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.orange),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.warning, color: Colors.orange, size: 20),
                  SizedBox(width: 8),
                  Text('Warnings:', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 4),
              ...(warnings as List).map((w) => 
                Padding(
                  padding: const EdgeInsets.only(left: 28),
                  child: Text('• $w', style: const TextStyle(fontSize: 13)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
      ],
    );
  }
}

// Extracted widget for errors section
class _ErrorsSection extends StatelessWidget {
  final dynamic errors;

  const _ErrorsSection({required this.errors});

  @override
  Widget build(BuildContext context) {
    if (errors == null || (errors as List).isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.red.shade100,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.red),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.error, color: Colors.red, size: 20),
                  SizedBox(width: 8),
                  Text('Errors:', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 4),
              ...(errors as List).map((e) => 
                Padding(
                  padding: const EdgeInsets.only(left: 28),
                  child: Text('• $e', style: const TextStyle(fontSize: 13)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
      ],
    );
  }
}

// Extracted widget for dependencies section
class _DependenciesSection extends StatelessWidget {
  final dynamic dependencies;
  final Map<String, String> userChoices;
  final Function(String, String) onChoiceChanged;
  final String entityType;

  const _DependenciesSection({
    required this.dependencies,
    required this.userChoices,
    required this.onChoiceChanged,
    required this.entityType,
  });

  @override
  Widget build(BuildContext context) {
    if (dependencies != null && (dependencies as List).isNotEmpty) {
      return _buildDependenciesList();
    } else {
      return _buildNoDependenciesMessage();
    }
  }

  Widget _buildDependenciesList() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Dependencies:',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
        ),
        const SizedBox(height: 8),
        const Text(
          'This item has dependencies. Choose how to handle each type:',
          style: TextStyle(color: Colors.grey, fontSize: 14),
        ),
        const SizedBox(height: 12),
        ...(dependencies as List).map((dep) => 
          _CascadeActionSelector(
            dependency: dep,
            currentChoice: userChoices[dep['relationship_name']] ?? dep['default_action'],
            onChanged: (newChoice) => onChoiceChanged(dep['relationship_name'], newChoice),
            entityType: entityType,
          )
        ),
      ],
    );
  }

  Widget _buildNoDependenciesMessage() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.green.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.green.shade200),
      ),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.check_circle, color: Colors.green, size: 48),
          SizedBox(height: 16),
          Text(
            'No dependencies found.',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text(
            'This item can be safely deleted.',
            style: TextStyle(color: Colors.green),
          ),
        ],
      ),
    );
  }
}

// Extracted widget for individual cascade action selector
class _CascadeActionSelector extends StatelessWidget {
  final Map<String, dynamic> dependency;
  final String currentChoice;
  final ValueChanged<String> onChanged;
  final String entityType;

  const _CascadeActionSelector({
    required this.dependency,
    required this.currentChoice,
    required this.onChanged,
    required this.entityType,
  });

  @override
  Widget build(BuildContext context) {
    final availableActions = (dependency['available_actions'] as List).cast<String>();

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 8),
            if (dependency['description'] != null)
              Text(
                dependency['description'],
                style: const TextStyle(color: Colors.grey, fontSize: 13),
              ),
            const SizedBox(height: 12),
            _buildSampleRecords(),
            _buildActionSelector(availableActions),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        Icon(
          Icons.link,
          size: 20,
          color: dependency['is_critical'] == true ? Colors.red : Colors.blue,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            '${dependency['table_name']} (${dependency['count']} records)',
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
        ),
        if (dependency['is_critical'] == true)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.red.shade100,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.red),
            ),
            child: const Text(
              'CRITICAL',
              style: TextStyle(
                color: Colors.red,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildSampleRecords() {
    if (dependency['sample_records'] == null || 
        (dependency['sample_records'] as List).isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Sample records:',
          style: TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
        ),
        const SizedBox(height: 4),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey.shade100,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: (dependency['sample_records'] as List).take(3).map((record) =>
              Text(
                '• ${_formatSampleRecord(record)}',
                style: const TextStyle(fontSize: 12, fontFamily: 'monospace'),
              ),
            ).toList(),
          ),
        ),
        const SizedBox(height: 12),
      ],
    );
  }

  Widget _buildActionSelector(List<String> availableActions) {
    // Ensure currentChoice is valid, fallback to first available action
    final validChoice = availableActions.contains(currentChoice) 
        ? currentChoice 
        : availableActions.isNotEmpty 
            ? availableActions.first 
            : '';
    
    // If the current choice is invalid, notify parent with the valid choice
    if (validChoice != currentChoice && validChoice.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        onChanged(validChoice);
      });
    }
            
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Choose action:',
          style: TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: validChoice.isEmpty ? null : validChoice,
          decoration: InputDecoration(
            border: const OutlineInputBorder(),
            isDense: false,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            filled: true,
            fillColor: Colors.grey.shade50,
          ),
          isExpanded: true,
          menuMaxHeight: 400,
          itemHeight: 60,
          items: availableActions.map((action) => DropdownMenuItem(
            value: action,
            child: Text(
              _getActionDisplayName(action),
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 16,
                color: Colors.black,
              ),
            ),
          )).toList(),
          onChanged: (value) {
            if (value != null) {
              onChanged(value);
            }
          },
        ),
        const SizedBox(height: 8),
        // Show description of selected action
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.blue.shade50,
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: Colors.blue.shade200),
          ),
          child: Text(
            _getActionDescription(validChoice, entityType, dependency['table_name']),
            style: const TextStyle(
              fontSize: 12,
              color: Colors.blue,
              fontStyle: FontStyle.italic,
            ),
          ),
        ),
      ],
    );
  }

  String _formatSampleRecord(Map<String, dynamic> record) {
    final entries = record.entries.take(3).map((e) => '${e.key}: ${e.value}');
    return entries.join(', ');
  }

  String _getActionDisplayName(String action) {
    switch (action) {
      case 'cascade_soft_delete':
        return 'Also mark as deleted';
      case 'cascade_disable':
        return 'Mark as broken/disabled';
      case 'cascade_nullify':
        return 'Remove connection';
      case 'cascade_ignore':
        return 'Keep unchanged';
      case 'cascade_restrict':
        return 'Prevent deletion';
      case 'cascade_hard_delete':
        return 'Also permanently delete';
      case 'cascade_soft_delete_deps':
        return 'Mark as deleted (soft)';
      case 'cascade_nullify_hard':
        return 'Remove connection (hard)';
      default:
        return action;
    }
  }

  String _getActionDescription(String action, String entityType, String dependencyType) {
    // Special case for self-reference (main entity actions)
    if (dependencyType == entityType && dependencyType != 'Unknown') {
      switch (action) {
        case 'cascade_soft_delete':
          return 'Mark this $entityType as deleted (can be restored later)';
        case 'cascade_disable':
          return 'Mark this $entityType as broken/out of stock (visible but unavailable)';
        default:
          return 'Apply $action to this $entityType';
      }
    }
    
    // Standard dependency actions
    switch (action) {
      case 'cascade_soft_delete':
        return 'Mark related $dependencyType as deleted (restorable)';
      case 'cascade_disable':
        return 'Mark related $dependencyType as broken (keeps records)';
      case 'cascade_nullify':
        return 'Remove connection, keep $dependencyType';
      case 'cascade_ignore':
        return 'Keep $dependencyType unchanged (recommended)';
      case 'cascade_restrict':
        return 'Prevent deletion (dependencies exist)';
      case 'cascade_hard_delete':
        return 'Permanently delete $dependencyType (cannot undo)';
      case 'cascade_soft_delete_deps':
        return 'Soft delete $dependencyType, hard delete $entityType';
      case 'cascade_nullify_hard':
        return 'Remove connections, keep $dependencyType';
      default:
        return 'Custom action';
    }
  }
}

/// Show the flexible deletion dialog
Future<bool?> showFlexibleDeletionDialog({
  required BuildContext context,
  required String entityType,
  required int entityId,
  required String entityName,
}) {
  return showDialog<bool>(
    context: context,
    builder: (context) => FlexibleDeletionDialog(
      entityType: entityType,
      entityId: entityId,
      entityName: entityName,
    ),
  );
}
