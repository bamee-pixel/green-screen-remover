document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const workspace = document.getElementById('workspace');
    const originalCanvas = document.getElementById('original-canvas');
    const resultImage = document.getElementById('result-image');
    const colorPreview = document.getElementById('color-preview');
    const colorHex = document.getElementById('color-hex');
    const sensitivityInput = document.getElementById('sensitivity');
    const sensitivityVal = document.getElementById('sensitivity-val');
    const smoothingInput = document.getElementById('smoothing');
    const smoothingVal = document.getElementById('smoothing-val');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const loadingOverlay = document.getElementById('loading');

    // State
    let currentState = {
        file: null,
        imageData: null, // Base64
        color: '#00FF00',
        sensitivity: 50,
        smoothing: 0
    };

    // Canvas Context
    const ctx = originalCanvas.getContext('2d');

    // --- Upload Handling ---

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file (JPG, PNG, WEBP).');
            return;
        }

        currentState.file = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            currentState.imageData = e.target.result;
            // Draw to canvas
            const img = new Image();
            img.onload = () => {
                // Resize logic if needed, for now just fit to width
                originalCanvas.width = img.width;
                originalCanvas.height = img.height;
                ctx.drawImage(img, 0, 0);

                // Show workspace
                dropZone.style.display = 'none';
                workspace.style.display = 'flex';

                // Trigger initial process
                processImage();
            };
            img.src = currentState.imageData;
        };
        reader.readAsDataURL(file);
    }

    // --- Color Picking ---

    originalCanvas.addEventListener('click', (e) => {
        const rect = originalCanvas.getBoundingClientRect();

        // Calculate scale factor in case displayed size != actual canvas size
        const scaleX = originalCanvas.width / rect.width;
        const scaleY = originalCanvas.height / rect.height;

        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;

        const pixel = ctx.getImageData(x, y, 1, 1).data;
        const hex = rgbToHex(pixel[0], pixel[1], pixel[2]);

        updateColor(hex);
        processImage();
    });

    function rgbToHex(r, g, b) {
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
    }

    function updateColor(hex) {
        currentState.color = hex;
        colorPreview.style.backgroundColor = hex;
        colorHex.textContent = hex;
    }

    // --- Controls ---

    sensitivityInput.addEventListener('input', (e) => {
        currentState.sensitivity = e.target.value;
        sensitivityVal.textContent = e.target.value;
        debouncedProcess();
    });

    smoothingInput.addEventListener('input', (e) => {
        currentState.smoothing = e.target.value;
        smoothingVal.textContent = e.target.value;
        debouncedProcess();
    });

    resetBtn.addEventListener('click', () => {
        currentState.file = null;
        currentState.imageData = null;
        dropZone.style.display = 'block';
        workspace.style.display = 'none';
        fileInput.value = ''; // Reset input
    });

    downloadBtn.addEventListener('click', () => {
        if (resultImage.src) {
            const a = document.createElement('a');
            a.href = resultImage.src;
            a.download = 'processed_image.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    });

    // --- Processing ---

    let debounceTimer;
    function debouncedProcess() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(processImage, 200); // 200ms delay
    }

    async function processImage() {
        if (!currentState.imageData) return;

        loadingOverlay.style.display = 'flex';

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: currentState.imageData,
                    color: currentState.color,
                    sensitivity: currentState.sensitivity,
                    smoothing: currentState.smoothing
                })
            });

            if (!response.ok) throw new Error('Processing failed');

            const data = await response.json();
            if (data.processed_image) {
                resultImage.src = data.processed_image;
            } else if (data.error) {
                console.error(data.error);
                alert('Error processing image: ' + data.error);
            }

        } catch (err) {
            console.error(err);
            alert('Failed to connect to server.');
        } finally {
            loadingOverlay.style.display = 'none';
        }
    }
});
