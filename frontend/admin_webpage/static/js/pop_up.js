// pop_up.js - Centralized popup logic for both error and success popups
// Usage: showPopup(message, type) where type is 'error' or 'success'

export function showPopup(message, type = 'error') {
    // Remove any existing popup
    const existing = document.getElementById('popup-message');
    if (existing) existing.remove();

    let popup = document.createElement('div');
    popup.id = 'popup-message';
    popup.style.position = 'fixed';
    popup.style.top = '20px';
    popup.style.left = '50%';
    popup.style.transform = 'translateX(-50%)';
    popup.style.background = type === 'success' ? '#4CAF50' : '#f44336';
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

// Convenience wrappers
export function showErrorPopup(message) {
    showPopup(message, 'error');
}
export function showSuccessPopup(message) {
    showPopup(message, 'success');
}
