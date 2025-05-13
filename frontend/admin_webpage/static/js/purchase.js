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