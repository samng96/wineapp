/**
 * WineReferenceFormManager - Manages the wine reference form view
 */
import { API } from './api.js';

export class WineReferenceFormManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupElements();
        this.setupEventListeners();
    }

    setupElements() {
        this.form = document.getElementById('wine-reference-form');
        this.cancelBtn = document.getElementById('wine-form-cancel');
        this.backBtn = document.getElementById('back-to-add-wine-btn');
    }

    setupEventListeners() {
        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Cancel button
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.handleCancel());
        }

        // Back button
        if (this.backBtn) {
            this.backBtn.addEventListener('click', () => this.handleCancel());
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.form);
        const data = {
            name: formData.get('name'),
            type: formData.get('type'),
        };

        // Optional fields
        const vintage = formData.get('vintage');
        if (vintage) {
            data.vintage = parseInt(vintage);
        }

        const producer = formData.get('producer');
        if (producer) {
            data.producer = producer;
        }

        const varietals = formData.get('varietals');
        if (varietals) {
            // Split by comma and trim each varietal
            data.varietals = varietals.split(',').map(v => v.trim()).filter(v => v.length > 0);
        }

        const region = formData.get('region');
        if (region) {
            data.region = region;
        }

        const country = formData.get('country');
        if (country) {
            data.country = country;
        }

        const rating = formData.get('rating');
        if (rating) {
            data.rating = parseInt(rating);
        }

        const tastingNotes = formData.get('tastingNotes');
        if (tastingNotes) {
            data.tastingNotes = tastingNotes;
        }

        // If there's a captured photo from addWineManager, include it
        if (window.addWineManager && window.addWineManager.capturedPhoto) {
            // TODO: Upload image and get URL
            // For now, we'll skip the image upload
        }

        try {
            const reference = await API.createWineReference(data);
            
            // Show success message
            alert('Wine reference created successfully!');
            
            // Navigate back to add wines view
            this.handleCancel();
            
            // TODO: Optionally create a wine instance from this reference
        } catch (error) {
            console.error('Error creating wine reference:', error);
            if (error.message.includes('already exists')) {
                alert('This wine reference already exists. Please check your wine list.');
            } else {
                alert('Error creating wine reference: ' + error.message);
            }
        }
    }

    handleCancel() {
        // Navigate back to add wines view
        if (window.app && window.app.showView) {
            window.app.showView('photo');
        }
    }

    // Called when view is shown
    show(options = {}) {
        // Reset form
        if (this.form) {
            this.form.reset();
            
            // Pre-fill name if provided
            if (options.prefillName) {
                const nameInput = document.getElementById('wine-name');
                if (nameInput) {
                    nameInput.value = options.prefillName;
                }
            }
        }
    }

    // Called when view is hidden
    hide() {
        // Nothing to do
    }
}
