/**
 * AddWineManager - Manages the "Add Wines" view with camera and photo selection
 */
export class AddWineManager {
    constructor() {
        this.stream = null;
        this.capturedPhoto = null;
        this.hasCamera = false;
        this.currentState = 'viewfinder'; // 'viewfinder', 'preview', 'confirm'
        
        this.init();
    }

    init() {
        this.setupElements();
        this.setupEventListeners();
        this.ensureInitialState();
        this.checkCameraAvailability();
    }

    ensureInitialState() {
        // Ensure preview is hidden on initialization
        if (this.previewEl) {
            this.previewEl.classList.add('hidden');
            this.previewEl.src = '';
            this.previewEl.style.display = 'none';
        }
        // Ensure video is hidden initially (will be shown when camera starts)
        if (this.videoEl) {
            this.videoEl.classList.add('hidden');
            this.videoEl.style.display = 'none';
        }
    }

    setupElements() {
        // Video and canvas elements
        this.videoEl = document.getElementById('add-wine-video');
        this.canvasEl = document.getElementById('add-wine-canvas');
        this.previewEl = document.getElementById('add-wine-preview');
        this.containerEl = document.getElementById('add-wine-camera-container');
        
        // Buttons
        this.albumBtn = document.getElementById('add-wine-album-btn');
        this.photoBtn = document.getElementById('add-wine-photo-btn');
        this.detailsBtn = document.getElementById('add-wine-details-btn');
        this.retakeBtn = document.getElementById('add-wine-retake-btn');
        this.confirmBtn = document.getElementById('add-wine-confirm-btn');
        this.fileInput = document.getElementById('add-wine-file-input');
        
        // Action bar
        this.actionBar = document.getElementById('add-wine-action-bar');
    }

    setupEventListeners() {
        // Re-fetch elements in case view was hidden during init
        this.albumBtn = document.getElementById('add-wine-album-btn');
        this.photoBtn = document.getElementById('add-wine-photo-btn');
        this.detailsBtn = document.getElementById('add-wine-details-btn');
        this.retakeBtn = document.getElementById('add-wine-retake-btn');
        this.confirmBtn = document.getElementById('add-wine-confirm-btn');
        this.fileInput = document.getElementById('add-wine-file-input');
        
        // Photo button - take photo
        if (this.photoBtn) {
            this.photoBtn.addEventListener('click', () => this.takePhoto());
        }

        // Album button - open file picker
        if (this.albumBtn) {
            this.albumBtn.addEventListener('click', () => this.openAlbum());
        }

        // File input change - handle selected file
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Retake button - go back to viewfinder
        if (this.retakeBtn) {
            this.retakeBtn.addEventListener('click', () => this.retakePhoto());
        }

        // Confirm button - proceed to confirmation page
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.confirmPhoto());
        }

        // Details button (placeholder for now)
        if (this.detailsBtn) {
            this.detailsBtn.addEventListener('click', () => {
                // TODO: Implement details functionality
            });
        }
    }

    async checkCameraAvailability() {
        try {
            // Check if getUserMedia is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.showNoCamera();
                return;
            }

            // Try to enumerate devices to check for video input
            const devices = await navigator.mediaDevices.enumerateDevices();
            const hasVideoInput = devices.some(device => device.kind === 'videoinput');
            
            if (!hasVideoInput) {
                this.showNoCamera();
                return;
            }

            // Try to get camera stream (without showing it yet)
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'environment' } // Prefer back camera
                });
                // Stop the test stream immediately
                stream.getTracks().forEach(track => track.stop());
                this.hasCamera = true;
                this.photoBtn.disabled = false;
                this.photoBtn.classList.remove('disabled');
            } catch (error) {
                this.showNoCamera();
            }
        } catch (error) {
            console.error('Error checking camera availability:', error);
            this.showNoCamera();
        }
    }

    showNoCamera() {
        this.hasCamera = false;
        if (this.photoBtn) {
            this.photoBtn.disabled = true;
            this.photoBtn.classList.add('disabled');
        }
        // Hide everything - video and preview (show nothing)
        if (this.videoEl) {
            this.videoEl.classList.add('hidden');
            this.videoEl.style.display = 'none';
        }
        if (this.previewEl) {
            this.previewEl.classList.add('hidden');
            this.previewEl.style.display = 'none';
        }
    }

    async startCamera() {
        if (!this.hasCamera || this.stream) {
            return; // Already started or no camera
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment', // Prefer back camera
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });

            // Hide preview if it was showing
            if (this.previewEl) {
                this.previewEl.classList.add('hidden');
                this.previewEl.style.display = 'none';
            }

            // Show video
            if (this.videoEl) {
                this.videoEl.srcObject = this.stream;
                this.videoEl.classList.remove('hidden');
                this.videoEl.style.display = 'block';
                this.videoEl.play();
            }
        } catch (error) {
            console.error('Error starting camera:', error);
            this.showNoCamera();
            alert('Unable to access camera. Please check permissions.');
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.videoEl) {
            this.videoEl.srcObject = null;
        }
    }

    takePhoto() {
        if (!this.videoEl || !this.canvasEl || !this.hasCamera) {
            return;
        }

        try {
            // Set canvas dimensions to match video
            this.canvasEl.width = this.videoEl.videoWidth;
            this.canvasEl.height = this.videoEl.videoHeight;

            // Draw video frame to canvas
            const ctx = this.canvasEl.getContext('2d');
            ctx.drawImage(this.videoEl, 0, 0);

            // Convert canvas to blob
            this.canvasEl.toBlob((blob) => {
                if (blob) {
                    const photoUrl = URL.createObjectURL(blob);
                    this.capturedPhoto = {
                        blob: blob,
                        url: photoUrl,
                        type: 'camera'
                    };
                    this.showPreview(photoUrl);
                }
            }, 'image/jpeg', 0.95);
        } catch (error) {
            console.error('Error taking photo:', error);
            alert('Error taking photo. Please try again.');
        }
    }

    showPreview(photoUrl) {
        // Stop camera
        this.stopCamera();

        // Hide video, show preview
        if (this.videoEl) {
            this.videoEl.classList.add('hidden');
            this.videoEl.style.display = 'none';
        }
        if (this.previewEl) {
            this.previewEl.src = photoUrl;
            this.previewEl.classList.remove('hidden');
            this.previewEl.style.display = 'block';
        }

        // Switch action bar buttons
        this.switchToPreviewMode();
    }

    switchToPreviewMode() {
        // Hide initial buttons
        if (this.albumBtn) this.albumBtn.classList.add('hidden');
        if (this.photoBtn) this.photoBtn.classList.add('hidden');
        if (this.detailsBtn) this.detailsBtn.classList.add('hidden');

        // Show retake and confirm buttons
        if (this.retakeBtn) {
            this.retakeBtn.classList.remove('hidden');
            // Ensure it's styled as a button with label
            this.retakeBtn.classList.remove('add-wine-photo-btn-circle');
        }
        if (this.confirmBtn) {
            this.confirmBtn.classList.remove('hidden');
            // Ensure it's styled as a button with label
            this.confirmBtn.classList.remove('add-wine-photo-btn-circle');
        }

        this.currentState = 'preview';
    }

    switchToViewfinderMode() {
        // Show initial buttons
        if (this.albumBtn) this.albumBtn.classList.remove('hidden');
        if (this.photoBtn) {
            this.photoBtn.classList.remove('hidden');
            // Ensure photo button has circle styling
            this.photoBtn.classList.add('add-wine-photo-btn-circle');
        }
        if (this.detailsBtn) this.detailsBtn.classList.remove('hidden');

        // Hide retake and confirm buttons
        if (this.retakeBtn) this.retakeBtn.classList.add('hidden');
        if (this.confirmBtn) this.confirmBtn.classList.add('hidden');

        this.currentState = 'viewfinder';
    }

    retakePhoto() {
        // Clear captured photo
        if (this.capturedPhoto && this.capturedPhoto.url) {
            URL.revokeObjectURL(this.capturedPhoto.url);
        }
        this.capturedPhoto = null;

        // Hide preview
        if (this.previewEl) {
            this.previewEl.classList.add('hidden');
            this.previewEl.style.display = 'none';
            this.previewEl.src = '';
        }

        // Switch back to viewfinder mode
        this.switchToViewfinderMode();

        // Restart camera if available (will show video) or show nothing if no camera
        if (this.hasCamera) {
            this.startCamera();
        } else {
            // Ensure video is hidden if no camera
            if (this.videoEl) {
                this.videoEl.classList.add('hidden');
                this.videoEl.style.display = 'none';
            }
        }
    }

    openAlbum() {
        if (this.fileInput) {
            // Remove capture attribute for desktop/album selection
            // On iOS, the browser will show photo picker
            // On desktop/Mac, it will show Finder file picker
            this.fileInput.removeAttribute('capture');
            this.fileInput.click();
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }

        // Create object URL for preview
        const photoUrl = URL.createObjectURL(file);
        this.capturedPhoto = {
            blob: file,
            url: photoUrl,
            type: 'album'
        };

        // Stop camera if it was running
        this.stopCamera();

        // Show preview
        this.showPreview(photoUrl);

        // Reset file input
        if (this.fileInput) {
            this.fileInput.value = '';
        }
    }

    confirmPhoto() {
        if (!this.capturedPhoto) {
            return;
        }

        // TODO: Navigate to confirmation/image processing page
        // For now, just store it - we'll implement the confirmation page next
        // This will be handled in a future step
    }

    // Called when view is shown
    show() {
        // Re-setup event listeners in case they weren't attached (view was hidden during init)
        this.setupEventListeners();
        
        // Reset to viewfinder state if needed
        if (this.currentState === 'preview' && !this.capturedPhoto) {
            this.switchToViewfinderMode();
        }
        
        // Ensure preview is hidden when showing viewfinder
        if (this.currentState === 'viewfinder') {
            if (this.previewEl) {
                this.previewEl.classList.add('hidden');
                this.previewEl.style.display = 'none';
            }
            // Start camera if available
            if (this.hasCamera) {
                this.startCamera();
            } else {
                // Hide video if no camera - show nothing
                if (this.videoEl) {
                    this.videoEl.classList.add('hidden');
                    this.videoEl.style.display = 'none';
                }
            }
        }
    }

    // Called when view is hidden
    hide() {
        this.stopCamera();
    }

    // Cleanup
    cleanup() {
        this.stopCamera();
        if (this.capturedPhoto && this.capturedPhoto.url) {
            URL.revokeObjectURL(this.capturedPhoto.url);
        }
    }
}
