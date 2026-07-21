import 'package:flutter/material.dart';

/// Card showing a user's current balance, optionally with a pending
/// deduction (e.g. the cost of items currently in a shopping cart) shown
/// alongside it.
class UserBalanceCard extends StatelessWidget {
  final double balance;
  final double? pendingDeduction;
  final bool isProcessing;

  const UserBalanceCard({
    super.key,
    required this.balance,
    this.pendingDeduction,
    this.isProcessing = false,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBalance = pendingDeduction != null 
        ? balance - pendingDeduction! 
        : balance;
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isProcessing 
            ? [Colors.orange.shade50, Colors.orange.shade100]
            : [Colors.blue.shade50, Colors.blue.shade100],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isProcessing 
            ? Colors.orange.shade300 
            : Colors.blue.shade300, 
          width: 2
        ),
        boxShadow: [
          BoxShadow(
            color: (isProcessing 
              ? Colors.orange.shade200 
              : Colors.blue.shade200).withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isProcessing 
                ? Colors.orange.shade600 
                : Colors.blue.shade600,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              isProcessing 
                ? Icons.hourglass_empty 
                : Icons.account_balance_wallet, 
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isProcessing ? 'Processing...' : 'Current Balance',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Row(
                  children: [
                    Text(
                      '€${effectiveBalance.toStringAsFixed(2)}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 24,
                        color: effectiveBalance > 0 ? Colors.green : Colors.red,
                      ),
                    ),
                    if (pendingDeduction != null && !isProcessing) ...[
                      const SizedBox(width: 8),
                      Text(
                        '(-€${pendingDeduction!.toStringAsFixed(2)})',
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.red,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          if (isProcessing)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            Icon(
              effectiveBalance > 0 ? Icons.check_circle : Icons.warning,
              color: effectiveBalance > 0 ? Colors.green : Colors.orange,
              size: 20,
            ),
        ],
      ),
    );
  }
}
