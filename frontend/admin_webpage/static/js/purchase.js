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