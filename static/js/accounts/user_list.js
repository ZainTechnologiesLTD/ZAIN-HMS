function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Create a temporary tooltip
        const tooltip = document.createElement('div');
        tooltip.textContent = 'Copied!';
        tooltip.style.position = 'absolute';
        tooltip.style.background = '#28a745';
        tooltip.style.color = 'white';
        tooltip.style.padding = '4px 8px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '12px';
        tooltip.style.zIndex = '1000';
        tooltip.style.pointerEvents = 'none';

        document.body.appendChild(tooltip);

        const rect = event.target.getBoundingClientRect();
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.top - 30) + 'px';

        setTimeout(() => {
            document.body.removeChild(tooltip);
        }, 1000);
    });
}

function confirmDelete(username, deleteUrl) {
    document.getElementById('userToDelete').textContent = username;
    document.getElementById('confirmDeleteBtn').href = deleteUrl;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}
