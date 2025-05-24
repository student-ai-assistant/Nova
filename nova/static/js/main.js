// Document Deletion Logic
function confirmAndDeleteDocument(subjectId, documentId, documentName, elementToRemove) {
    if (confirm(`Are you sure you want to delete the document: "${documentName}"? This action cannot be undone.`)) {
        fetch(`/api/subjects/${subjectId}/documents/${documentId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                // Include CSRF token if your app uses them
                // 'X-CSRFToken': '{{ csrf_token() }}' // Example for Flask-WTF
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message || 'Document deleted successfully.');
                // Remove the document item from the list
                const docElement = document.getElementById(elementToRemove);
                if (docElement) {
                    docElement.remove();
                }
            } else {
                alert('Error deleting document: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while trying to delete the document.');
        });
    }
}
