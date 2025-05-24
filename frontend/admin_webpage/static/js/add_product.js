// Import popup functions for use in this file
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
    // Initialize Select2 for searchable ingredient select
    $('#ingredientSelect').select2({width: 'resolve'});
    // Focus the search field when opening any Select2 dropdown
    $(document).off('select2:open').on('select2:open', function() {
        setTimeout(function() {
            let searchField = document.querySelector('.select2-container--open .select2-search__field');
            if (searchField) searchField.focus();
        }, 0);
    });

    // --- POPUP LOGIC ---
    window.toggleAdditionalInput = toggleAdditionalInput;
    if (window._errorMsg) showErrorPopup(window._errorMsg);
    if (window._successMsg) showSuccessPopup(window._successMsg);
    const urlSuccess = getQueryParam('success');
    if (urlSuccess) {
        showSuccessPopup(urlSuccess);
        removeQueryParam('success');
    }

    // --- CATEGORY TOGGLE LOGIC ---
    function toggleAdditionalInput() {
        const category = $('#categorySelect').val();
        if (category === 'toast') {
            $('#toasterSpaceQuantitySelect').show();
        } else {
            $('#toasterSpaceQuantitySelect').hide();
        }
    }
    $('#categorySelect').on('change', toggleAdditionalInput);
    toggleAdditionalInput(); // Initial call

    // --- INGREDIENT TABLE LOGIC ---
    let selectedIngredients = [];

    function calculateCurrentCost() {
        let total = 0;
        selectedIngredients.forEach(item => {
            // Get cost per unit from the ingredientSelect options
            const option = $('#ingredientSelect option[value="' + item.id + '"]');
            const costPerUnit = parseFloat(option.data('cost')) || 0;
            total += costPerUnit * item.quantity;
        });
        return total;
    }

    function updateCurrentCostDisplay() {
        const total = calculateCurrentCost();
        $('#currentCost').text('Current Cost: ' + total.toFixed(2));
    }

    function updateIngredientTable() {
        const tbody = $('#ingredientList');
        tbody.empty();
        selectedIngredients.forEach((item, idx) => {
            const row = $('<tr>');
            row.append($('<td>').text(item.name));
            row.append($('<td>').text(item.quantity));
            const removeBtn = $('<button type="button">Remove</button>').on('click', function() {
                selectedIngredients.splice(idx, 1);
                updateIngredientTable();
                updateCurrentCostDisplay();
            });
            row.append($('<td>').append(removeBtn));
            tbody.append(row);
        });
        // Remove any old hidden inputs
        $('input[name="ingredients[]"]').remove();
        $('input[name="quantities[]"]').remove();
        // Add hidden inputs for form submission
        selectedIngredients.forEach(item => {
            $('<input>').attr({type: 'hidden', name: 'ingredients[]', value: item.id}).appendTo('form');
            $('<input>').attr({type: 'hidden', name: 'quantities[]', value: item.quantity}).appendTo('form');
        });
        updateCurrentCostDisplay();
    }

    window.addIngredient = function() {
        const select = $('#ingredientSelect');
        const id = select.val();
        const name = select.find('option:selected').text();
        const quantity = parseInt($('#ingredientQuantity').val(), 10);
        if (!id || !quantity || quantity < 1) {
            showErrorPopup('Please select an ingredient and enter a valid quantity.');
            return;
        }
        // Prevent duplicate ingredient
        if (selectedIngredients.some(item => item.id === id)) {
            showErrorPopup('Ingredient already added.');
            return;
        }
        selectedIngredients.push({id, name, quantity});
        updateIngredientTable();
        $('#ingredientQuantity').val('');
        updateCurrentCostDisplay();
    };

    // If the form is reloaded with errors, try to restore selected ingredients from hidden inputs
    $('input[name="ingredients[]"]').each(function(idx) {
        const id = $(this).val();
        const name = $('#ingredientSelect option[value="' + id + '"]').text();
        const quantity = $('input[name="quantities[]"]').eq(idx).val();
        if (id && name && quantity) {
            selectedIngredients.push({id, name, quantity: parseInt(quantity, 10)});
        }
    });
    updateIngredientTable();
});

