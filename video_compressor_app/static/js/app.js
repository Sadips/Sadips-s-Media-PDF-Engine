/**
 * Google Antigravity - Modular Media, PDF & Image Compressor Frontend Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const dropzoneContent = document.getElementById('dropzoneContent');
    const fileInfo = document.getElementById('fileInfo');
    const fileIcon = document.getElementById('fileIcon');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const typeBadge = document.getElementById('typeBadge');
    const btnRemove = document.getElementById('btnRemove');
    const btnCompress = document.getElementById('btnCompress');
    
    const uploadForm = document.getElementById('uploadForm');
    const progressState = document.getElementById('progressState');
    const statusTitle = document.getElementById('statusTitle');
    const statusSub = document.getElementById('statusSub');
    const successState = document.getElementById('successState');
    const errorBanner = document.getElementById('errorBanner');
    const errorMessage = document.getElementById('errorMessage');
    const btnCloseError = document.getElementById('btnCloseError');
    const btnReset = document.getElementById('btnReset');

    let selectedFile = null;

    // SVG Icons
    const videoSvg = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
        <line x1="7" y1="2" x2="7" y2="22"></line>
        <line x1="17" y1="2" x2="17" y2="22"></line>
        <line x1="2" y1="12" x2="22" y2="12"></line>
        <line x1="2" y1="7" x2="7" y2="7"></line>
        <line x1="2" y1="17" x2="7" y2="17"></line>
        <line x1="17" y1="17" x2="22" y2="17"></line>
        <line x1="17" y1="7" x2="22" y2="7"></line>
    </svg>`;

    const pdfSvg = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
    </svg>`;

    const imageSvg = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
        <circle cx="8.5" cy="8.5" r="1.5"></circle>
        <polyline points="21 15 16 10 5 21"></polyline>
    </svg>`;

    // Helper: Format bytes into readable string
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // Update UI when file is selected
    function handleFileSelection(file) {
        if (!file) return;
        
        const nameLower = file.name.toLowerCase();
        const isPdf = nameLower.endsWith('.pdf');
        const isImage = file.type.startsWith('image/') || nameLower.match(/\.(jpg|jpeg|png|webp|bmp|tiff)$/i);
        const isVideo = file.type.startsWith('video/') || nameLower.match(/\.(mp4|mov|avi|mkv|webm|flv|wmv|m4v)$/i);

        if (!isPdf && !isImage && !isVideo) {
            showError('Please select a supported Video file, PDF document, or Image.');
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);

        if (isImage) {
            fileIcon.innerHTML = imageSvg;
            typeBadge.textContent = 'Image File';
            typeBadge.className = 'type-badge image';
        } else if (isPdf) {
            fileIcon.innerHTML = pdfSvg;
            typeBadge.textContent = 'PDF Document';
            typeBadge.className = 'type-badge pdf';
        } else {
            fileIcon.innerHTML = videoSvg;
            typeBadge.textContent = 'Video File';
            typeBadge.className = 'type-badge video';
        }

        dropzoneContent.classList.add('hidden');
        fileInfo.classList.remove('hidden');
        btnCompress.disabled = false;
        hideError();
    }

    function clearFileSelection() {
        selectedFile = null;
        fileInput.value = '';
        dropzoneContent.classList.remove('hidden');
        fileInfo.classList.add('hidden');
        btnCompress.disabled = true;
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorBanner.classList.remove('hidden');
    }

    function hideError() {
        errorBanner.classList.add('hidden');
    }

    // Drag and Drop event listeners
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('drag-over');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files.length > 0) {
            fileInput.files = dt.files;
            handleFileSelection(dt.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    btnRemove.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFileSelection();
    });

    btnCloseError.addEventListener('click', hideError);

    btnReset.addEventListener('click', () => {
        successState.classList.add('hidden');
        uploadForm.classList.remove('hidden');
        clearFileSelection();
    });

    // Handle Form Submission & Async Upload
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        // Monetag Ad link trigger on button click
        try {
            window.open('https://omg10.com/4/11506746', '_blank');
        } catch (err) {
            console.log('Ad window trigger:', err);
        }

        const nameLower = selectedFile.name.toLowerCase();
        const isPdf = nameLower.endsWith('.pdf');
        const isImage = selectedFile.type.startsWith('image/') || nameLower.match(/\.(jpg|jpeg|png|webp|bmp|tiff)$/i);

        hideError();
        uploadForm.classList.add('hidden');
        progressState.classList.remove('hidden');

        if (isImage) {
            statusTitle.textContent = 'Compressing Image File...';
            statusSub.textContent = 'Executing Pillow stream optimizer. Download will start automatically.';
        } else if (isPdf) {
            statusTitle.textContent = 'Compressing PDF Document...';
            statusSub.textContent = 'Executing PyMuPDF stream optimizer. Download will start automatically.';
        } else {
            statusTitle.textContent = 'Compressing Video File...';
            statusSub.textContent = 'Executing FFmpeg libx264 engine. Download will start automatically.';
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/compress', true);
        xhr.responseType = 'blob';

        xhr.onload = function () {
            if (xhr.status === 200) {
                const disposition = xhr.getResponseHeader('Content-Disposition');
                let extMatch = selectedFile.name.match(/\.([^/.]+)$/);
                let ext = extMatch ? extMatch[0] : '';
                let downloadName = selectedFile.name.replace(/\.[^/.]+$/, "") + "_compressed" + ext;

                if (disposition && disposition.indexOf('filename=') !== -1) {
                    const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                    if (matches != null && matches[1]) {
                        downloadName = matches[1].replace(/['"]/g, '');
                    }
                }

                // Trigger automatic file download
                const blob = xhr.response;
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = downloadName;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(downloadUrl);

                // Show success view
                progressState.classList.add('hidden');
                successState.classList.remove('hidden');
            } else {
                const reader = new FileReader();
                reader.onload = function () {
                    try {
                        const res = JSON.parse(reader.result);
                        showError(res.error || res.details || 'Compression failed on server.');
                    } catch (err) {
                        showError('Compression failed. Server returned status: ' + xhr.status);
                    }
                    progressState.classList.add('hidden');
                    uploadForm.classList.remove('hidden');
                };
                reader.readAsText(xhr.response);
            }
        };

        xhr.onerror = function () {
            showError('Network error occurred during file upload.');
            progressState.classList.add('hidden');
            uploadForm.classList.remove('hidden');
        };

        xhr.send(formData);
    });
});
