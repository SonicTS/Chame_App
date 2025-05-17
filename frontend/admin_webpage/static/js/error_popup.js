// error_popup.js - Include this in all HTML templates for error popups
function showErrorPopup(message) {
    let popup = document.createElement('div');
    popup.id = 'error-popup';
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
