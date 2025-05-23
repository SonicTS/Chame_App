import { showErrorPopup, showSuccessPopup } from './pop_up.js';

function getQueryParam(name) {
    const url = new URL(window.location.href);
    return url.searchParams.get(name) || '';
}

function removeQueryParam(name) {
    const url = new URL(window.location.href);
    url.searchParams.delete(name);
    window.history.replaceState({}, document.title, url.pathname + url.search);
}

$(document).ready(function() {
    // Assuming `users` and `products` are passed as global JavaScript variables
    const users = window.users || [];
    const products = window.products || [];

    // Helper to get toaster_space for a product_id
    function getToasterSpace(productId) {
        const prod = products.find(p => p.product_id == productId);
        return prod ? (prod.toaster_space || 1) : 1;
    }

    // Render 6 rows, each with a user and product dropdown
    function renderRows(selectedProducts) {
        $('#squaresContainer').empty();
        for (let i = 0; i < 6; i++) {
            const selectedProductId = selectedProducts[i] || '';
            const isDisabled = false; // We'll update this after rendering
            const row = $(`
                <div class="user-product-row" style="margin-bottom:8px;display:flex;align-items:center;gap:8px;">
                    <label>User:</label>
                    <select class="userSelect" id="userSelect${i}" name="userSelect${i}" ${isDisabled ? 'disabled' : ''}>
                        ${users.map(user => `<option value="${user.user_id}">${user.name}</option>`).join('')}
                    </select>
                    <label>Product:</label>
                    <select class="productSelect" id="productSelect${i}" name="productSelect${i}" data-row="${i}" ${isDisabled ? 'disabled' : ''}>
                        <option value="">-- Select --</option>
                        ${products.map(product => `<option value="${product.product_id}" data-toaster_space="${product.toaster_space}">${product.name}</option>`).join('')}
                    </select>
                    <span class="occupied-label" style="color:#f44336;display:none;">Occupied</span>
                </div>
            `);
            // Set selected value if any
            row.find('.productSelect').val(selectedProductId);
            $('#squaresContainer').append(row);
        }
        updateOccupiedStates();
    }

    // Update disabled/enabled state based on current product selections
    function updateOccupiedStates() {
        let occupiedUntil = -1;
        $('.user-product-row').each(function(idx) {
            const $row = $(this);
            const $productSelect = $row.find('.productSelect');
            const $userSelect = $row.find('.userSelect');
            const $occupiedLabel = $row.find('.occupied-label');
            if (idx <= occupiedUntil) {
                $productSelect.prop('disabled', true);
                $userSelect.prop('disabled', true);
                $occupiedLabel.show();
            } else {
                $productSelect.prop('disabled', false);
                $userSelect.prop('disabled', false);
                $occupiedLabel.hide();
                const selectedProductId = $productSelect.val();
                if (selectedProductId) {
                    const toasterSpace = getToasterSpace(selectedProductId);
                    if (toasterSpace > 1) {
                        occupiedUntil = idx + toasterSpace - 1;
                    }
                }
            }
        });
    }

    // --- GLOBAL SELECT LOGIC ---
    // Add global selectors above the 6 entry rows
    const globalUserSelect = $('<select id="globalUserSelect"><option value="">-- Select User for All --</option></select>');
    const globalProductSelect = $('<select id="globalProductSelect"><option value="">-- Select Product for All --</option></select>');
    // Populate global selects from window.products and window.users
    if (window.products) {
        window.products.forEach(p => {
            globalProductSelect.append(`<option value="${p.product_id}">${p.name}</option>`);
        });
    }
    if (window.users) {
        window.users.forEach(u => {
            globalUserSelect.append(`<option value="${u.user_id}">${u.name}</option>`);
        });
    }
    // Insert above the 6 entry rows (assume a container with id 'entriesContainer')
    $('#entriesContainer').prepend('<div id="globalSelectors"></div>');
    $('#globalSelectors').append(globalUserSelect).append(globalProductSelect);

    // On change, set all 6 selects to the chosen value and trigger the occupy logic
    globalProductSelect.on('change', function() {
        const val = $(this).val();
        if (!val) return;
        $('.productSelect').val(val).trigger('change');
    });
    globalUserSelect.on('change', function() {
        const val = $(this).val();
        if (!val) return;
        $('.userSelect').val(val).trigger('change');
    });

    // Initial render
    renderRows([]);

    // On product change, update occupied states and show error if not enough space
    $('#squaresContainer').on('change', '.productSelect', function() {
        updateOccupiedStates();
        // Check if the selected product fits in the remaining slots
        const idx = $(this).closest('.user-product-row').index();
        const selectedProductId = $(this).val();
        if (selectedProductId) {
            const toasterSpace = getToasterSpace(selectedProductId);
            if (toasterSpace > 1 && idx + toasterSpace > 6) {
                showErrorPopup('Not enough space for this product in the remaining slots.');
                // Optionally, reset the selection
                $(this).val('');
                updateOccupiedStates();
            }
        }
    });

    // Submit button click handler
    $('#submitButton').click(function() {
        const userSelections = [];
        const productSelections = [];
        $('.user-product-row').each(function(idx) {
            const $row = $(this);
            const $userSelect = $row.find('.userSelect');
            const $productSelect = $row.find('.productSelect');
            if (!$productSelect.prop('disabled') && $productSelect.val()) {
                userSelections.push($userSelect.val());
                productSelections.push($productSelect.val());
            }
        });
        // Send data to backend
        $.post('/toast_round', {
            product_ids: productSelections,
            user_selections: userSelections
        }, function(response) {
            // Create a temporary DOM to extract the message
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = response;
            const errorMatch = tempDiv.innerHTML.match(/window\._errorMsg\s*=\s*"([^"]*)"/);
            const successMatch = tempDiv.innerHTML.match(/window\._successMsg\s*=\s*"([^"]*)"/);
            const errorMsg = errorMatch && errorMatch[1] ? errorMatch[1] : '';
            const successMsg = successMatch && successMatch[1] ? successMatch[1] : '';
            if (errorMsg) {
                showErrorPopup(errorMsg);
            } else if (successMsg) {
                showSuccessPopup(successMsg);
            } else {
                // No backend message, reload the page with a frontend-defined success message
                const msg = encodeURIComponent('Toast round submitted successfully!');
                window.location.search = '?success=' + msg;
            }
        }).fail(function() {
            showErrorPopup('Error submitting data.');
        });
    });

    // Show popups if error or success messages are present
    if (window._errorMsg) showErrorPopup(window._errorMsg);
    if (window._successMsg) showSuccessPopup(window._successMsg);

    // Show popup if success param is present in URL
    const urlSuccess = getQueryParam('success');
    if (urlSuccess) {
        showSuccessPopup(urlSuccess);
        removeQueryParam('success');
    }
});
