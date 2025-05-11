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