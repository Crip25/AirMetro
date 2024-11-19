// static/script.js
// Add this to the top of your existing script.js file
document.addEventListener('DOMContentLoaded', function() {
    // ... (keep existing code)

    // Add Browse Data functionality
    const browseButton = document.getElementById('browseData');
    browseButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/files/');
            if (response.ok) {
                const data = await response.json();
                showBrowseModal(data.files);
            } else {
                showStatus('Failed to load files', 'error');
            }
        } catch (error) {
            showStatus('Error loading files: ' + error.message, 'error');
        }
    });

    // Create and show the browse modal
    function showBrowseModal(files) {
        // Create modal container
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        
        // Modal content
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">Browse Datasets</h2>
                    <button class="text-gray-500 hover:text-gray-700" onclick="this.closest('.fixed').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="max-h-96 overflow-y-auto">
                    ${files.length ? `
                        <div class="space-y-4">
                            ${files.map(file => `
                                <div class="border rounded-lg p-4 hover:bg-gray-50">
                                    <div class="flex justify-between items-start">
                                        <div>
                                            <h3 class="font-semibold">${file.title || file.file_id}</h3>
                                            <p class="text-sm text-gray-600">${file.description || 'No description'}</p>
                                            <div class="flex flex-wrap gap-2 mt-2">
                                                ${(file.tags || []).map(tag => `
                                                    <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                                        ${tag}
                                                    </span>
                                                `).join('')}
                                            </div>
                                        </div>
                                        <a href="/file/${file.file_id}" 
                                           class="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 text-sm">
                                            Download
                                        </a>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p class="text-gray-500 text-center py-8">No datasets available</p>'}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }
});
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
