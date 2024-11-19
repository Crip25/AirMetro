// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');
    const tagInput = document.getElementById('tagInput');
    const addTagButton = document.getElementById('addTag');
    const tagContainer = document.getElementById('tagContainer');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    
    let currentFile = null;
    let tags = [];

    // Progress steps handling
    const updateProgress = (step) => {
        const steps = document.querySelectorAll('.progress-step');
        steps.forEach((s, index) => {
            if (index < step) {
                s.classList.add('active');
                s.querySelector('.bg-gray-300').classList.replace('bg-gray-300', 'bg-blue-500');
            } else {
                s.classList.remove('active');
                s.querySelector('.bg-blue-500')?.classList.replace('bg-blue-500', 'bg-gray-300');
            }
        });
    };

    // Drag and drop handlers with visual feedback
    dropZone.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-active');
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-active');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        if (e.currentTarget === dropZone) {
            dropZone.classList.remove('drag-active');
        }
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-active');
        
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    // File selection handling
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        currentFile = file;
        fileName.textContent = file.name;
        fileInfo.classList.remove('hidden');
        updateProgress(1);
    }

    removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        currentFile = null;
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        updateProgress(0);
    });

    // Tag handling with visual feedback
    addTagButton.addEventListener('click', addTag);
    tagInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag();
        }
    });

    function addTag() {
        const tag = tagInput.value.trim();
        if (tag && !tags.includes(tag)) {
            tags.push(tag);
            updateTagDisplay();
            tagInput.value = '';
            
            // Animate new tag
            const newTag = tagContainer.lastElementChild;
            newTag.classList.add('upload-success');
        }
    }

    function updateTagDisplay() {
        tagContainer.innerHTML = tags.map(tag => `
            <span class="tag-item">
                <i class="fas fa-tag
