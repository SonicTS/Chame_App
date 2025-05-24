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

document.addEventListener('DOMContentLoaded', function () {
    const salesConfig = document.getElementById('salesConfig');
    if (salesConfig) {
        salesConfig.addEventListener('change', function () {
            const selectedConfig = this.value;
            // Redirect to the same page with the selected configuration as a query parameter
            window.location.href = `?config=${selectedConfig}`;
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const config = urlParams.get('config');
    if (config) {
        const salesConfigDropdown = document.getElementById('salesConfig');
        salesConfigDropdown.value = config;
    }
});

$(document).ready(function() {
    $('#userSelect').select2({width: 'resolve', dropdownAutoWidth: true});
    $('#productSelect').select2({width: 'resolve', dropdownAutoWidth: true});
    // Ensure the select fields themselves expand to fill available width
    $('#userSelect').css('width', '500px');
    $('#productSelect').css('width', '250px');
    // Focus the search field when opening any Select2 dropdown
    $(document).off('select2:open').on('select2:open', function() {
        setTimeout(function() {
            let searchField = document.querySelector('.select2-container--open .select2-search__field');
            if (searchField) searchField.focus();
        }, 0);
    });

    if (window._errorMsg) showErrorPopup(window._errorMsg);
    if (window._successMsg) showSuccessPopup(window._successMsg);

    const urlSuccess = getQueryParam('success');
    if (urlSuccess) {
        showSuccessPopup(urlSuccess);
        removeQueryParam('success');
    }

    // Example: If you have a submit handler, use this pattern
    function handleFormSubmit(event) {
        event.preventDefault();
        // ...collect form data as needed...
        $.post('/purchase', $(event.target).serialize(), function(response) {
            if (response.includes('window._errorMsg') || response.includes('window._successMsg')) {
                document.open();
                document.write(response);
                document.close();
            } else {
                showSuccessPopup('Purchase completed successfully!');
            }
        }).fail(function() {
            showErrorPopup('Error submitting purchase.');
        });
    }
    // ...attach handleFormSubmit to your form if not already...
});