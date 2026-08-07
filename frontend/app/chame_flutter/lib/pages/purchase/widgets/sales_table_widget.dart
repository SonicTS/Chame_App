import 'package:flutter/material.dart';

/// Paginated, horizontally + vertically scrollable sales history table.
class SalesTableWidget extends StatefulWidget {
  final Map<String, dynamic>? paginatedSalesData;
  final ScrollController mainController;
  final bool isLoading;
  final int currentPage;
  final int totalPages;
  final int totalSales;
  final VoidCallback onNextPage;
  final VoidCallback onPreviousPage;
  final VoidCallback onFirstPage;
  final VoidCallback onLastPage;
  final ValueChanged<Map<String, String>> onFiltersChanged;

  const SalesTableWidget({
    super.key,
    required this.paginatedSalesData,
    required this.mainController,
    required this.isLoading,
    required this.currentPage,
    required this.totalPages,
    required this.totalSales,
    required this.onNextPage,
    required this.onPreviousPage,
    required this.onFirstPage,
    required this.onLastPage,
    required this.onFiltersChanged,
  });

  @override
  State<SalesTableWidget> createState() => _SalesTableWidgetState();
}

class _SalesTableWidgetState extends State<SalesTableWidget> {
  final ScrollController _horizontalScrollController = ScrollController();
  final ScrollController _verticalScrollController = ScrollController();
  final Map<String, TextEditingController> _controllers = {};

  @override
  void dispose() {
    _horizontalScrollController.dispose();
    _verticalScrollController.dispose();
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    // Initialize controllers for column filters
    for (final key in [
      'id',
      'consumer',
      'donator',
      'salesman',
      'product',
      'quantity',
      'price',
      'date',
    ]) {
      _controllers[key] = TextEditingController();
    }
  }

  String _formatTimestamp(dynamic ts) {
    if (ts == null) return '';
    if (ts is DateTime) return ts.toString();
    if (ts is String) return ts;
    return ts.toString();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    final salesData = widget.paginatedSalesData;
    if (salesData == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20.0),
          child: Text('No sales data available.'),
        ),
      );
    }

    final allSales =
        (salesData['sales'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ??
        [];

    return Column(
      children: [
        // Column filter inputs (compact)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterField('ID', 'id', width: 80),
                const SizedBox(width: 8),
                _buildFilterField('Consumer', 'consumer', width: 120),
                const SizedBox(width: 8),
                _buildFilterField('Donator', 'donator', width: 120),
                const SizedBox(width: 8),
                _buildFilterField('Salesman', 'salesman', width: 120),
                const SizedBox(width: 8),
                _buildFilterField('Product', 'product', width: 140),
                const SizedBox(width: 8),
                _buildFilterField('Qty', 'quantity', width: 60),
                const SizedBox(width: 8),
                _buildFilterField('Price', 'price', width: 80),
                const SizedBox(width: 8),
                _buildFilterField('Date', 'date', width: 120),
              ],
            ),
          ),
        ),
        // Pagination info and controls
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(8),
              topRight: Radius.circular(8),
            ),
          ),
          child: Column(
            children: [
              // Sales count info
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Flexible(
                    child: Text(
                      'Showing ${allSales.length} of ${widget.totalSales} sales',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Pagination controls
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Page ${widget.currentPage} of ${widget.totalPages}',
                    style: const TextStyle(fontSize: 14),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.first_page),
                    onPressed: widget.currentPage > 1
                        ? widget.onFirstPage
                        : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(
                      minWidth: 28,
                      minHeight: 28,
                    ),
                    padding: const EdgeInsets.all(2),
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: widget.currentPage > 1
                        ? widget.onPreviousPage
                        : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(
                      minWidth: 28,
                      minHeight: 28,
                    ),
                    padding: const EdgeInsets.all(2),
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: widget.currentPage < widget.totalPages
                        ? widget.onNextPage
                        : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(
                      minWidth: 28,
                      minHeight: 28,
                    ),
                    padding: const EdgeInsets.all(2),
                  ),
                  IconButton(
                    icon: const Icon(Icons.last_page),
                    onPressed: widget.currentPage < widget.totalPages
                        ? widget.onLastPage
                        : null,
                    iconSize: 18,
                    constraints: const BoxConstraints(
                      minWidth: 28,
                      minHeight: 28,
                    ),
                    padding: const EdgeInsets.all(2),
                  ),
                ],
              ),
            ],
          ),
        ),
        // Sales table
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey.shade300),
              borderRadius: const BorderRadius.only(
                bottomLeft: Radius.circular(8),
                bottomRight: Radius.circular(8),
              ),
            ),
            child: Scrollbar(
              controller: _horizontalScrollController,
              thumbVisibility: true,
              child: SingleChildScrollView(
                controller: _horizontalScrollController,
                scrollDirection: Axis.horizontal,
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minWidth: MediaQuery.of(context).size.width - 32,
                  ),
                  child: Scrollbar(
                    controller: _verticalScrollController,
                    thumbVisibility: true,
                    child: SingleChildScrollView(
                      controller: _verticalScrollController,
                      scrollDirection: Axis.vertical,
                      physics: CoordinatedScrollPhysics(
                        mainController: widget.mainController,
                      ),
                      child: _buildDataTable(allSales),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDataTable(List<Map<String, dynamic>> sales) {
    return DataTable(
      columnSpacing: 12,
      horizontalMargin: 12,
      dataRowMinHeight: 48,
      headingRowHeight: 48,
      columns: const [
        DataColumn(
          label: Text('ID', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        DataColumn(
          label: Text(
            'Consumer',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        DataColumn(
          label: Text('Donator', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        DataColumn(
          label: Text(
            'Salesman',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        DataColumn(
          label: Text('Product', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        DataColumn(
          label: Text('Qty', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        DataColumn(
          label: Text('Price', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        DataColumn(
          label: Text('Date', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
      rows: sales.map((sale) => _buildDataRow(sale)).toList(),
    );
  }

  Map<String, String> get _activeFilters => {
    for (final entry in _controllers.entries)
      entry.key: entry.value.text.trim(),
  };

  Widget _buildFilterField(String label, String key, {double width = 120}) {
    final controller = _controllers[key]!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 4),
        SizedBox(
          width: width,
          child: TextField(
            controller: controller,
            decoration: const InputDecoration(
              isDense: true,
              contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 8),
              border: OutlineInputBorder(),
              hintText: 'filter',
            ),
            onChanged: (_) => widget.onFiltersChanged(_activeFilters),
          ),
        ),
      ],
    );
  }

  DataRow _buildDataRow(Map<String, dynamic> sale) {
    String consumer = '';
    String donator = '';
    String salesman = '';
    String product = '';

    try {
      final consumerField = sale['consumer'];
      final donatorField = sale['donator'];
      final salesmanField = sale['salesman'];
      final productField = sale['product'];

      consumer = consumerField is Map && consumerField['name'] != null
          ? consumerField['name'].toString()
          : consumerField?.toString() ?? '';
      donator = donatorField == null
          ? ''
          : (donatorField is Map && donatorField['name'] != null
                ? donatorField['name'].toString()
                : donatorField.toString());
      salesman = salesmanField is Map && salesmanField['name'] != null
          ? salesmanField['name'].toString()
          : salesmanField?.toString() ?? '';
      product = productField is Map && productField['name'] != null
          ? productField['name'].toString()
          : productField?.toString() ?? '';
    } catch (e) {
      consumer = sale['consumer']?.toString() ?? '';
      donator = sale['donator']?.toString() ?? '';
      salesman = sale['salesman']?.toString() ?? '';
      product = sale['product']?.toString() ?? '';
    }

    String formattedDate = '';
    try {
      final timestamp = sale['timestamp'];
      if (timestamp != null) {
        final dateStr = _formatTimestamp(timestamp);
        if (dateStr.isNotEmpty) {
          final parts = dateStr.split(' ');
          if (parts.length >= 2) {
            final datePart = parts[0];
            final timePart = parts[1].split(':').take(2).join(':');
            formattedDate = '$datePart\n$timePart';
          } else {
            formattedDate = dateStr;
          }
        }
      }
    } catch (e) {
      formattedDate = _formatTimestamp(sale['timestamp']);
    }

    return DataRow(
      key: ValueKey(sale['sale_id']),
      cells: [
        DataCell(
          Text(
            sale['sale_id']?.toString() ?? '',
            style: const TextStyle(fontSize: 12),
          ),
        ),
        DataCell(
          SizedBox(
            width: 80,
            child: Text(
              consumer,
              style: const TextStyle(fontSize: 12),
              overflow: TextOverflow.ellipsis,
              maxLines: 2,
            ),
          ),
        ),
        DataCell(
          SizedBox(
            width: 80,
            child: Text(
              donator,
              style: const TextStyle(fontSize: 12),
              overflow: TextOverflow.ellipsis,
              maxLines: 2,
            ),
          ),
        ),
        DataCell(
          SizedBox(
            width: 80,
            child: Text(
              salesman,
              style: const TextStyle(fontSize: 12),
              overflow: TextOverflow.ellipsis,
              maxLines: 2,
            ),
          ),
        ),
        DataCell(
          SizedBox(
            width: 100,
            child: Text(
              product,
              style: const TextStyle(fontSize: 12),
              overflow: TextOverflow.ellipsis,
              maxLines: 2,
            ),
          ),
        ),
        DataCell(
          Text(
            sale['quantity']?.toString() ?? '',
            style: const TextStyle(fontSize: 12),
          ),
        ),
        DataCell(
          Text(
            '€${sale['total_price']?.toString() ?? ''}',
            style: const TextStyle(fontSize: 12),
          ),
        ),
        DataCell(
          SizedBox(
            width: 80,
            child: Text(
              formattedDate,
              style: const TextStyle(fontSize: 10),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
      ],
    );
  }
}

/// Lets the sales table's inner vertical scroll view hand scroll gestures
/// off to the page's main [ScrollController] once it hits the top/bottom of
/// its own content, so the whole page scrolls smoothly instead of getting
/// "stuck" inside the table.
class CoordinatedScrollPhysics extends ScrollPhysics {
  final ScrollController mainController;

  const CoordinatedScrollPhysics({required this.mainController, super.parent});

  @override
  CoordinatedScrollPhysics applyTo(ScrollPhysics? ancestor) {
    return CoordinatedScrollPhysics(
      mainController: mainController,
      parent: buildParent(ancestor),
    );
  }

  @override
  double applyPhysicsToUserOffset(ScrollMetrics position, double offset) {
    // If we're at the top of the sales table and trying to scroll up
    if (position.pixels <= 0 && offset > 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent,
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the sales table
      }
    }
    // If we're at the bottom of the sales table and trying to scroll down
    else if (position.pixels >= position.maxScrollExtent && offset < 0) {
      // Scroll the main page instead
      if (mainController.hasClients) {
        double newPosition = mainController.position.pixels - offset;
        newPosition = newPosition.clamp(
          0.0,
          mainController.position.maxScrollExtent,
        );
        mainController.jumpTo(newPosition);
        return 0; // Don't scroll the sales table
      }
    }
    return super.applyPhysicsToUserOffset(position, offset);
  }
}
