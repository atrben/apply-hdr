// script.js

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    const imageUpload = document.getElementById('imageUpload');
    const processButton = document.getElementById('process');
    const downloadButton = document.getElementById('download');
    const downloadStatus = document.getElementById('downloadStatus');
    
    let currentImage = null;
    let filename = null;

    imageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);
                    currentImage = img;
                    uploadImage(file);
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.filename) {
                filename = data.filename;
                // Automatically process the image after upload
                processImage();
            }
        })
        .catch(error => console.error('Error uploading image:', error));
    }

    function processImage() {
        if (!filename) return;
        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(`HTTP error! status: ${response.status}, details: ${JSON.stringify(errData)}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.processed_filename) {
                console.log('Processed filename received:', data.processed_filename);
                downloadButton.style.display = 'inline-block';
                downloadButton.style.backgroundColor = '';
                downloadButton.style.cursor = 'pointer';
                downloadButton.disabled = false;
                downloadButton.removeAttribute('disabled'); // Force remove disabled attribute
                console.log('Download button should now be enabled and clickable', downloadButton);
                downloadButton.onclick = () => {
                    console.log('Initiating download for:', `/download/${data.processed_filename}`);
                    window.location.href = `/download/${data.processed_filename}`;
                    downloadButton.style.display = 'none';
                    downloadStatus.style.display = 'inline-block';
                    // Hide status message after a short delay to indicate download completion
                    setTimeout(() => {
                        downloadStatus.style.display = 'none';
                        downloadButton.style.display = 'inline-block';
                        console.log('Download status hidden, button re-displayed');
                    }, 3000);
                };
                console.log('Processing successful, download button enabled');
                // Display the processed image in the canvas
                const processedImg = new Image();
                processedImg.onload = () => {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    canvas.width = processedImg.width;
                    canvas.height = processedImg.height;
                    ctx.drawImage(processedImg, 0, 0);
                    console.log('Processed image loaded and displayed in canvas');
                };
                processedImg.onerror = (error) => {
                    console.error('Error loading processed image:', error);
                };
                processedImg.src = `/static/processed/${data.processed_filename}`;
                console.log('Attempting to load processed image from:', `/static/processed/${data.processed_filename}`);
            } else {
                console.error('No processed filename in response:', data);
            }
        })
        .catch(error => {
            console.error('Error processing image:', error);
            // Even on error, attempt to unblock the UI for user interaction
            downloadButton.style.display = 'inline-block';
            downloadButton.style.backgroundColor = 'gray';
            downloadButton.style.cursor = 'not-allowed';
            downloadButton.disabled = true;
            console.log('Processing failed, button remains visible but disabled due to error');
        });
    }
}); 