$(document).ready(function() {
    // Assuming `users` is passed as a global JavaScript variable
    const users = window.users || [];

    // Debugging: Log the users array to verify its content
    console.log("Users array:", users);

    // Function to generate squares based on selected product
    function configureSquaresForProduct(productId, quantity) {
        // Clear existing squares
        $('#squaresContainer').empty();

        // Generate squares
        for (let i = 0; i < quantity; i++) {
            const square = $(
                `<div>
                    <label for="userSelect${i}">Select User for Toast ${i + 1}:</label>
                    <select id="userSelect${i}" name="userSelect${i}">
                        ${users.map(user => `<option value="${user.user_id}">${user.name}</option>`).join('')}
                    </select>
                </div>`
            );
            $('#squaresContainer').append(square);

            // Debugging: Log the generated square
            console.log("Generated square for user selection:", square.html());
        }
    }

    // On page load, configure squares for the first toast product if available
    const firstProductOption = $('#toastProduct option:first');
    if (firstProductOption.length > 0) {
        const firstProductId = firstProductOption.val();
        const firstProductQuantity = firstProductOption.data('quantity');
        configureSquaresForProduct(firstProductId, firstProductQuantity);
    }

    // Handle product change event
    $('#toastProduct').change(function() {
        const selectedOption = $(this).find(':selected');
        const productId = selectedOption.val();
        const quantity = selectedOption.data('quantity');

        // Debugging: Log the selected product and quantity
        console.log("Selected product:", productId);
        console.log("Toast round quantity:", quantity);

        configureSquaresForProduct(productId, quantity);
    });

    // Submit button click handler
    $('#submitButton').click(function() {
        const selectedProduct = $('#toastProduct').val();
        const userSelections = [];

        // Collect user selections
        $('#squaresContainer select').each(function() {
            userSelections.push($(this).val());
        });

        // Debugging: Log the collected user selections
        console.log("User selections:", userSelections);

        // Send data to backend
        $.post('/toast_round', {
            product_id: selectedProduct,
            user_selections: userSelections
        }, function(response) {
            // Refresh the page after successful submission
            location.reload();
        }).fail(function() {
            alert('Error submitting data.');
        });
    });
});

// Global AJAX error handler for popups
function showErrorPopup(message) {
    let popup = document.createElement('div');
    popup.id = 'ajax-error-popup';
    popup.style.position = 'fixed';
    popup.style.top = '20px';
    popup.style.left = '50%';
    popup.style.transform = 'translateX(-50%)';
    popup.style.background = '#f44336';
    popup.style.color = 'white';
    popup.style.padding = '16px';
    popup.style.borderRadius = '8px';
    popup.style.zIndex = '10000';
    popup.style.minWidth = '200px';
    popup.style.textAlign = 'center';
    popup.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
    popup.innerHTML = message + '<button onclick="this.parentElement.style.display=\'none\'" style="margin-left:16px;background:transparent;border:none;color:white;font-weight:bold;font-size:16px;cursor:pointer;">&times;</button>';
    document.body.appendChild(popup);
    setTimeout(function(){
        if(popup) popup.style.display = 'none';
    }, 5000);
}

// If using fetch for AJAX, wrap it to show popup on error
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments).then(function(response) {
        if (!response.ok) {
            response.json().then(function(data) {
                showErrorPopup(data.error || 'An error occurred.');
            }).catch(function() {
                showErrorPopup('An error occurred.');
            });
        }
        return response;
    }).catch(function(error) {
        showErrorPopup('A network error occurred.');
        throw error;
    });
};