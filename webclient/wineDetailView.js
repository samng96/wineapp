/**
 * Wine Detail View - Modal for displaying and editing wine details
 */
import { API } from './api.js';

class WineDetailView {
    constructor() {
        this.modal = null;
        this.currentReference = null;
        this.currentInstance = null;
        this.originalTastingNotes = null;
        this.init();
    }

    init() {
        this.modal = document.getElementById('wine-detail-modal');
        if (!this.modal) {
            console.error('Wine detail modal not found!');
            return;
        }

        // Close button
        const closeBtn = document.getElementById('wine-detail-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // Overlay click to close
        const overlay = this.modal.querySelector('.wine-detail-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.hide());
        }

        // Save tasting notes button
        const saveBtn = document.getElementById('wine-detail-save-notes');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveTastingNotes());
        }

        // Coravin button
        const coravinBtn = document.getElementById('wine-detail-coravin-btn');
        if (coravinBtn) {
            coravinBtn.addEventListener('click', () => this.openWithCoravin());
        }

        // Drink wine button
        const drinkBtn = document.getElementById('wine-detail-drink-btn');
        if (drinkBtn) {
            drinkBtn.addEventListener('click', () => this.drinkWine());
        }

        // Close modal when clicking on bottom nav bar
        const bottomNav = document.getElementById('bottom-nav');
        if (bottomNav) {
            bottomNav.addEventListener('click', (e) => {
                // Only close if clicking on nav buttons, not if modal is hidden
                if (!this.modal.classList.contains('hidden')) {
                    const navBtn = e.target.closest('.nav-btn');
                    if (navBtn) {
                        this.hide();
                    }
                }
            });
        }

        // Rating star handlers (will be set up when showing)
        this.setupRatingStars();
    }

    async show(wineReference, wineInstance = null) {
        if (!wineReference) return;

        this.currentReference = wineReference;
        this.currentInstance = wineInstance;

        // Show modal
        this.modal.classList.remove('hidden');

        // Load full wine reference data
        try {
            const fullReference = await API.get(`/wine-references/${wineReference.id}`);
            this.currentReference = fullReference;
            this.render();
        } catch (error) {
            console.error('Error loading wine details:', error);
            // Still render with what we have
            this.render();
        }
    }

    hide() {
        this.modal.classList.add('hidden');
        this.currentReference = null;
        this.currentInstance = null;
        this.originalTastingNotes = null;
    }

    render() {
        if (!this.currentReference) return;

        const ref = this.currentReference;

        // Title and name
        const titleEl = document.getElementById('wine-detail-title');
        if (titleEl) {
            titleEl.textContent = ref.name || 'Wine Details';
        }

        const nameEl = document.getElementById('wine-detail-name');
        if (nameEl) {
            const vintageText = ref.vintage ? `${ref.vintage} ` : '';
            nameEl.textContent = `${vintageText}${ref.name || 'Unknown Wine'}`;
        }

        // Meta information
        const metaEl = document.getElementById('wine-detail-meta');
        if (metaEl) {
            const metaParts = [];
            if (ref.producer) metaParts.push(ref.producer);
            if (ref.type) metaParts.push(`${ref.type} Wine`);
            if (ref.region) metaParts.push(ref.region);
            if (ref.country) metaParts.push(ref.country);
            metaEl.textContent = metaParts.join(' • ');
        }

        // Image
        const imageEl = document.getElementById('wine-detail-image');
        if (imageEl) {
            if (ref.labelImageUrl) {
                imageEl.src = ref.labelImageUrl;
                imageEl.style.display = 'block';
            } else {
                imageEl.style.display = 'none';
            }
        }

        // Rating stars
        this.renderRatingStars();

        // Storage info (Stored and Coravined dates)
        this.renderStorageInfo();

        // Tasting notes
        const notesEl = document.getElementById('wine-detail-tasting-notes');
        if (notesEl) {
            this.originalTastingNotes = ref.tastingNotes || '';
            notesEl.value = this.originalTastingNotes;
        }

        // Vivino info (placeholder for now)
        this.renderVivinoInfo();
    }

    renderRatingStars() {
        const ratingContainer = document.getElementById('wine-detail-rating');
        if (!ratingContainer || !this.currentReference) return;

        const rating = this.currentReference.rating || 0;
        ratingContainer.innerHTML = [1, 2, 3, 4, 5].map(star => 
            `<span class="rating-star ${star <= rating ? 'filled' : ''}" 
                  data-rating="${star}" 
                  data-reference-id="${this.currentReference.id}"
                  title="Rate ${star} star${star !== 1 ? 's' : ''}">★</span>`
        ).join('');

        // Set up click handlers
        this.setupRatingStars();
    }

    setupRatingStars() {
        const ratingStars = this.modal.querySelectorAll('.rating-star');
        ratingStars.forEach(star => {
            // Remove existing listeners by cloning
            const newStar = star.cloneNode(true);
            star.parentNode.replaceChild(newStar, star);
            
            newStar.addEventListener('click', async (e) => {
                e.stopPropagation();
                const rating = parseInt(newStar.getAttribute('data-rating'));
                const referenceId = newStar.getAttribute('data-reference-id');
                
                if (!referenceId || !rating) return;
                
                try {
                    await API.updateWineReferenceRating(referenceId, rating);
                    
                    if (this.currentReference) {
                        this.currentReference.rating = rating;
                    }
                    
                    // Re-render rating stars
                    this.renderRatingStars();
                } catch (error) {
                    console.error('Error updating rating:', error);
                    alert(`Failed to update rating: ${error.message || 'Unknown error'}`);
                }
            });
        });
    }

    async saveTastingNotes() {
        if (!this.currentReference) return;

        const notesEl = document.getElementById('wine-detail-tasting-notes');
        if (!notesEl) return;

        const newNotes = notesEl.value;
        
        // Check if changed
        if (newNotes === this.originalTastingNotes) {
            return; // No changes
        }

        const saveBtn = document.getElementById('wine-detail-save-notes');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
        }

        try {
            // Update via API
            await API.updateWineReference(this.currentReference.id, {
                tastingNotes: newNotes
            });

            // Update local reference
            this.currentReference.tastingNotes = newNotes;
            this.originalTastingNotes = newNotes;

            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Saved!';
                setTimeout(() => {
                    saveBtn.textContent = 'Save Notes';
                }, 2000);
            }
        } catch (error) {
            console.error('Error saving tasting notes:', error);
            alert(`Failed to save tasting notes: ${error.message || 'Unknown error'}`);
            
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save Notes';
            }
        }
    }

    renderStorageInfo() {
        const instance = this.currentInstance;
        
        // Stored date
        const storedDateEl = document.getElementById('wine-detail-stored-date');
        if (storedDateEl) {
            if (instance && instance.storedDate) {
                storedDateEl.textContent = this.formatStoredDate(instance.storedDate);
            } else {
                storedDateEl.textContent = 'N/A';
            }
        }

        // Consumed date
        const consumedItemEl = document.getElementById('wine-detail-consumed-item');
        const consumedDateEl = document.getElementById('wine-detail-consumed-date');
        const consumedButtonItemEl = document.getElementById('wine-detail-drink-btn');
        
        if (instance && instance.consumed && instance.consumedDate) {
            if (consumedItemEl) {
                consumedItemEl.style.display = 'flex';
            }
            if (consumedDateEl) {
                consumedDateEl.textContent = this.formatStoredDate(instance.consumedDate);
            }
        } else {
            if (consumedItemEl) {
                consumedItemEl.style.display = 'none';
            }
        }

        // Coravined date or button
        const coravinedItemEl = document.getElementById('wine-detail-coravined-item');
        const coravinedDateEl = document.getElementById('wine-detail-coravined-date');
        const actionButtonsEl = document.getElementById('wine-detail-action-buttons');
        const coravinBtn = document.getElementById('wine-detail-coravin-btn');
        
        if (instance && !instance.consumed) {
            if (instance.coravined && instance.coravinedDate) {
                // Show coravined date
                if (coravinedItemEl) {
                    coravinedItemEl.style.display = 'flex';
                }
                if (coravinedDateEl) {
                    coravinedDateEl.textContent = this.formatStoredDate(instance.coravinedDate);
                }
                // Hide coravin button but show action buttons container for drink button
                if (coravinBtn) {
                    coravinBtn.style.display = 'none';
                }
                if (actionButtonsEl) {
                    actionButtonsEl.style.display = 'flex';
                }
            } else {
                // Show both buttons
                if (coravinBtn) {
                    coravinBtn.style.display = 'inline-block';
                }
                if (actionButtonsEl) {
                    actionButtonsEl.style.display = 'flex';
                }
                if (coravinedItemEl) {
                    coravinedItemEl.style.display = 'none';
                }
            }
        } else {
            // Hide everything if consumed
            if (coravinedItemEl) {
                coravinedItemEl.style.display = 'none';
            }
            if (actionButtonsEl) {
                actionButtonsEl.style.display = 'none';
            }
        }
    }

    async openWithCoravin() {
        if (!this.currentInstance) return;

        // Show confirmation dialog
        const confirmed = confirm('Are you sure you want to open this wine with a Coravin?');
        if (!confirmed) return;

        const coravinBtn = document.getElementById('wine-detail-coravin-btn');
        if (coravinBtn) {
            coravinBtn.disabled = true;
            coravinBtn.textContent = 'Marking...';
        }

        try {
            // Call API to mark as coravined
            await API.coravinWineInstance(this.currentInstance.id);

            // Update local instance
            this.currentInstance.coravined = true;
            this.currentInstance.coravinedDate = new Date().toISOString();

            // Re-render storage info to show date instead of button
            this.renderStorageInfo();
        } catch (error) {
            console.error('Error marking wine as coravined:', error);
            alert(`Failed to mark wine as coravined: ${error.message || 'Unknown error'}`);
            
            // Reset button
            if (coravinBtn) {
                coravinBtn.disabled = false;
                coravinBtn.textContent = 'Open with a Coravin';
            }
        }
    }

    async drinkWine() {
        if (!this.currentInstance) return;

        // Show confirmation dialog
        const confirmed = confirm('Are you sure you want to mark this wine as consumed?');
        if (!confirmed) return;

        const drinkBtn = document.getElementById('wine-detail-drink-btn');
        if (drinkBtn) {
            drinkBtn.disabled = true;
            drinkBtn.textContent = 'Marking...';
        }

        try {
            // Find the wine's current location in cellars (if any)
            let cellarLocation = null;
            if (window.cellarManager && window.cellarManager.cellars) {
                const cellars = window.cellarManager.cellars;
                for (const cellar of cellars) {
                    if (cellar.winePositions) {
                        for (const shelfIndex in cellar.winePositions) {
                            const shelfPositions = cellar.winePositions[shelfIndex];
                            for (const side of ['front', 'back', 'single']) {
                                const positions = shelfPositions[side] || [];
                                const position = positions.indexOf(this.currentInstance.id);
                                if (position !== -1) {
                                    cellarLocation = {
                                        cellarId: cellar.id,
                                        shelfIndex: parseInt(shelfIndex),
                                        side,
                                        position
                                    };
                                    break;
                                }
                            }
                            if (cellarLocation) break;
                        }
                    }
                    if (cellarLocation) break;
                }
            }

            // Call API to mark as consumed
            await API.consumeWineInstance(this.currentInstance.id);

            // Remove from cellar location if it was shelved
            if (cellarLocation) {
                try {
                    await API.updateWineInstanceLocation(this.currentInstance.id, {
                        oldCellarId: cellarLocation.cellarId,
                        newCellarId: null,  // Remove from cellar
                        shelfIndex: null,
                        side: null,
                        position: null
                    });

                    // Update local cellar data structure
                    if (window.cellarManager && window.cellarManager.cellars) {
                        const cellar = window.cellarManager.cellars.find(c => c.id === cellarLocation.cellarId);
                        if (cellar && cellar.winePositions) {
                            const shelfPositions = cellar.winePositions[cellarLocation.shelfIndex];
                            if (shelfPositions && shelfPositions[cellarLocation.side]) {
                                shelfPositions[cellarLocation.side][cellarLocation.position] = null;
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error removing wine from cellar:', error);
                    // Continue anyway - the wine is still marked as consumed
                }
            }

            // Update local instance
            this.currentInstance.consumed = true;
            this.currentInstance.consumedDate = new Date().toISOString();

            // Re-render storage info to show consumed date instead of buttons
            this.renderStorageInfo();

            // Trigger a reload of both cellar and wine views
            if (window.cellarManager) {
                // If viewing a specific cellar, reload that cellar detail view
                if (window.cellarManager.currentCellar) {
                    await window.cellarManager.showCellarDetail(window.cellarManager.currentCellar.id);
                } else {
                    // Otherwise reload the cellar list
                    window.cellarManager.loadCellars();
                }
            }
            if (window.wineManager) {
                window.wineManager.loadWines();
            }
        } catch (error) {
            console.error('Error marking wine as consumed:', error);
            alert(`Failed to mark wine as consumed: ${error.message || 'Unknown error'}`);
            
            // Reset button
            if (drinkBtn) {
                drinkBtn.disabled = false;
                drinkBtn.textContent = 'Drink wine';
            }
        }
    }

    formatStoredDate(storedDate) {
        if (!storedDate) return 'N/A';
        try {
            const date = new Date(storedDate);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch (e) {
            return storedDate;
        }
    }

    renderVivinoInfo() {
        // Placeholder for Vivino data
        // TODO: Fetch from Vivino API or store in wine reference
        const drinkTimeEl = document.getElementById('wine-detail-drink-time');
        const drinkWindowEl = document.getElementById('wine-detail-drink-window');
        
        if (drinkTimeEl) {
            drinkTimeEl.textContent = 'Not available';
        }
        if (drinkWindowEl) {
            drinkWindowEl.textContent = 'Not available';
        }
    }
}

// Create singleton instance
let wineDetailViewInstance = null;

export function getWineDetailView() {
    if (!wineDetailViewInstance) {
        wineDetailViewInstance = new WineDetailView();
    }
    return wineDetailViewInstance;
}

export { WineDetailView };
