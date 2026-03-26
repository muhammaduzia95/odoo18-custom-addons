// Simple vanilla JavaScript for file attachments - no Odoo dependencies
document.addEventListener('DOMContentLoaded', function() {
    var attachmentInput = document.getElementById('attachments');
    var form = document.querySelector('.timeoff-card form');

    if (attachmentInput) {
        attachmentInput.addEventListener('change', handleFileSelection);
    }

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    function handleFileSelection(event) {
        var input = event.target;
        var filePreview = document.getElementById('file-preview');
        var fileList = document.getElementById('file-list');
        var files = input.files;

        if (files.length > 0) {
            filePreview.style.display = 'block';
            fileList.innerHTML = '';

            Array.from(files).forEach(function(file, index) {
                var fileItem = document.createElement('div');
                fileItem.className = 'file-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded';

                var fileInfo = document.createElement('div');
                fileInfo.innerHTML =
                    '<i class="fa fa-file me-2"></i>' +
                    '<strong>' + escapeHtml(file.name) + '</strong>' +
                    '<small class="text-muted ms-2">(' + formatFileSize(file.size) + ')</small>';

                var removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'btn btn-sm btn-outline-danger';
                removeBtn.innerHTML = '<i class="fa fa-times"></i>';
                removeBtn.onclick = function() {
                    removeFile(index);
                };

                fileItem.appendChild(fileInfo);
                fileItem.appendChild(removeBtn);
                fileList.appendChild(fileItem);
            });
        } else {
            filePreview.style.display = 'none';
        }
    }

    function removeFile(indexToRemove) {
        var input = document.getElementById('attachments');
        var dt = new DataTransfer();

        Array.from(input.files).forEach(function(file, index) {
            if (index !== indexToRemove) {
                dt.items.add(file);
            }
        });

        input.files = dt.files;
        handleFileSelection({ target: input });
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function escapeHtml(text) {
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) {
            return map[m];
        });
    }

    function handleFormSubmit(event) {
        var submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Submitting...';
        }
    }
});