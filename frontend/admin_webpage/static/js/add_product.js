function addIngredient() {
    const ingredientSelect = document.getElementById("ingredientSelect");
    const quantityInput = document.getElementById("ingredientQuantity");
    const selectedIngredient = ingredientSelect.options[ingredientSelect.selectedIndex];
    const quantity = quantityInput.value;

    console.debug("Selected ingredient:", selectedIngredient.text, "Value:", selectedIngredient.value);
    console.debug("Entered quantity:", quantity);

    if (!quantity || quantity <= 0) {
        alert("Please enter a valid quantity.");
        console.warn("Invalid quantity entered:", quantity);
        return;
    }

    const ingredientList = document.getElementById("ingredientList");
    const row = document.createElement("tr");
    row.innerHTML = `
        <td>${selectedIngredient.text}</td>
        <td>${quantity}</td>
        <td><button type="button" onclick="removeIngredient(this)">Remove</button></td>
        <input type="hidden" name="ingredients[]" value="${selectedIngredient.value}">
        <input type="hidden" name="quantities[]" value="${quantity}">
    `;
    ingredientList.appendChild(row);

    console.info("Added ingredient:", selectedIngredient.text, "with quantity:", quantity);

    // Reset the input fields
    ingredientSelect.selectedIndex = 0;
    quantityInput.value = "";
    console.debug("Reset ingredient select and quantity input fields.");
}

function removeIngredient(button) {
    const row = button.parentElement.parentElement;
    row.remove();
}

function toggleAdditionalInput() {
    const categorySelect = document.getElementById("categorySelect");
    const additionalInput = document.getElementById("toastRoundQuantitySelect");

    if (categorySelect.value === "toast") {
        additionalInput.style.display = "block"; // Show the additional input
    } else {
        additionalInput.style.display = "none"; // Hide the additional input
    }
}

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
}

