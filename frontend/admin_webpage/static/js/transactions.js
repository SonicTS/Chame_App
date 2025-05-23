// Handles dynamic reloading of the transaction table based on filters
$(document).ready(function() {
    function reloadTransactions() {
        const userId = $('#transactionUserSelect').val();
        const type = $('#transactionTypeSelect').val();
        $.get('/users/transactions', { user_id: userId, type: type }, function(data) {
            // data should be a JSON array of transactions
            const tbody = $('#transactionTableBody');
            tbody.empty();
            if (data.length === 0) {
                tbody.append('<tr><td colspan="4">No transactions found.</td></tr>');
                return;
            }
            data.forEach(tx => {
                tbody.append(`
                    <tr>
                        <td>${tx.user_name}</td>
                        <td>${tx.type}</td>
                        <td>${tx.amount}</td>
                        <td>${tx.date}</td>
                    </tr>
                `);
            });
        });
    }
    $('#transactionUserSelect, #transactionTypeSelect').on('change', reloadTransactions);
});
