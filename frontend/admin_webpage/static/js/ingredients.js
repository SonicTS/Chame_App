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
        $.post('/ingredients/restock', $(event.target).serialize(), function(response) {
            if (response.includes('window._errorMsg') || response.includes('window._successMsg')) {
                document.open();
                document.write(response);
                document.close();
            } else {
                showSuccessPopup('Ingredient restocked successfully!');
            }
        }).fail(function() {
            showErrorPopup('Error restocking ingredient.');
        });
    }
    // ...attach handleFormSubmit to your form if not already...

    // Example for AJAX POST handler:
    // $.post('/some_url', data, function(response) {
    //     const tempDiv = document.createElement('div');
    //     tempDiv.innerHTML = response;
    //     const errorMatch = tempDiv.innerHTML.match(/window\._errorMsg\s*=\s*"([^"]*)"/);
    //     const successMatch = tempDiv.innerHTML.match(/window\._successMsg\s*=\s*"([^"]*)"/);
    //     const errorMsg = errorMatch && errorMatch[1] ? errorMatch[1] : '';
    //     const successMsg = successMatch && successMatch[1] ? successMatch[1] : '';
    //     if (errorMsg) {
    //         showErrorPopup(errorMsg);
    //     } else if (successMsg) {
    //         showSuccessPopup(successMsg);
    //     } else {
    //         // No backend message, reload the page with a frontend-defined success message
    //         const msg = encodeURIComponent('Action completed successfully!');
    //         window.location.search = '?success=' + msg;
    //     }
    // }).fail(function() {
    //     showErrorPopup('Error submitting data.');
    // });
});