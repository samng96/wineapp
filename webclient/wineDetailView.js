/**
 * Wine Detail View - Modal for displaying and editing wine details
 */
import { API } from './api.js';
import { findInstanceLocation } from './utils/locationUtils.js';

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

        // Load full global wine reference data, merge with user-specific fields
        try {
            const fullReference = await API.get(`/wine-references/${wineReference.id}`);
            // Preserve user-specific fields from the passed-in reference
            fullReference.userReferenceId = wineReference.userReferenceId;
            fullReference.rating = wineReference.rating;
            fullReference.tastingNotes = wineReference.tastingNotes;
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

        // Other bottles of the same wine
        this.renderOtherBottles();

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
                    // Update via UserWineReference endpoint
                    const userRefId = this.currentReference ? this.currentReference.userReferenceId : null;
                    if (userRefId) {
                        await API.updateUserWineReference(userRefId, { rating });
                    }

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
            // Update via UserWineReference API
            const userRefId = this.currentReference.userReferenceId;
            if (userRefId) {
                await API.updateUserWineReference(userRefId, {
                    tastingNotes: newNotes
                });
            }

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

        // Location
        const locationItemEl = document.getElementById('wine-detail-location-item');
        const locationEl = document.getElementById('wine-detail-location');
        
        if (instance && !instance.consumed) {
            // Find location in cellars using utility function
            // Check both wineManager and cellarManager for cellars
            let cellars = null;
            if (window.cellarManager && window.cellarManager.cellars && window.cellarManager.cellars.length > 0) {
                cellars = window.cellarManager.cellars;
            } else if (window.wineManager && window.wineManager.cellars && window.wineManager.cellars.length > 0) {
                cellars = window.wineManager.cellars;
            }
            
            let locationInfo = null;
            if (cellars) {
                try {
                    locationInfo = findInstanceLocation(instance, cellars);
                } catch (error) {
                    console.error('Error finding instance location:', error);
                }
            }
            
            if (locationInfo) {
                const { cellar, shelfIndex, side, position } = locationInfo;
                const sideDisplay = side === 'single' ? '' : side === 'front' ? 'Front' : 'Back';
                const sideText = sideDisplay ? `, ${sideDisplay}` : '';
                const locationText = `${cellar.name}, Shelf ${shelfIndex + 1}${sideText}, Position ${position + 1}`;
                
                if (locationItemEl) {
                    locationItemEl.style.display = 'flex';
                }
                if (locationEl) {
                    locationEl.textContent = locationText;
                    locationEl.classList.add('wine-detail-location-link');
                    // Store location info for click handler
                    locationEl.dataset.cellarId = cellar.id;
                    locationEl.dataset.shelfIndex = shelfIndex;
                    locationEl.dataset.side = side;
                    locationEl.dataset.position = position;
                    locationEl.dataset.instanceId = instance.id;
                    
                    // Remove existing click handlers and add new one
                    const newLocationEl = locationEl.cloneNode(true);
                    locationEl.parentNode.replaceChild(newLocationEl, locationEl);
                    newLocationEl.addEventListener('click', () => this.navigateToLocation(newLocationEl.dataset));
                }
            } else {
                // Unshelved
                if (locationItemEl) {
                    locationItemEl.style.display = 'flex';
                }
                if (locationEl) {
                    locationEl.textContent = 'Unshelved';
                    locationEl.classList.remove('wine-detail-location-link');
                    // Remove click handler
                    const newLocationEl = locationEl.cloneNode(true);
                    locationEl.parentNode.replaceChild(newLocationEl, locationEl);
                }
            }
        } else {
            // Hide location if consumed
            if (locationItemEl) {
                locationItemEl.style.display = 'none';
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
                const locationInfo = findInstanceLocation(this.currentInstance, window.cellarManager.cellars);
                if (locationInfo) {
                    cellarLocation = {
                        cellarId: locationInfo.cellar.id,
                        shelfIndex: locationInfo.shelfIndex,
                        side: locationInfo.side,
                        position: locationInfo.position
                    };
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

    async navigateToLocation(locationData) {
        /**
         * Navigate to cellar view and scroll to the wine's position
         */
        const { cellarId, shelfIndex, side, position, instanceId } = locationData;
        
        if (!cellarId || !window.cellarManager) return;
        
        // Store reference and instance to reopen modal later
        const referenceToReopen = this.currentReference;
        const instanceToReopen = this.currentInstance;
        
        // Close the wine detail modal
        this.hide();
        
        // Navigate to cellar detail view
        await window.cellarManager.showCellarDetail(cellarId);
        
        // Wait for DOM to update, then scroll to position
        setTimeout(() => {
            // Find the position element
            const positionId = `wine-pos-${shelfIndex}-${side}-${position}`;
            const positionEl = document.getElementById(positionId);
            
            if (positionEl) {
                // Scroll the position into view
                positionEl.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'center'
                });
                
                // Add a red highlight effect
                positionEl.style.outline = '3px solid #d32f2f';
                positionEl.style.outlineOffset = '3px';
                setTimeout(() => {
                    positionEl.style.outline = '';
                    positionEl.style.outlineOffset = '';
                    
                    // Reopen the wine detail modal after highlight disappears
                    if (referenceToReopen && instanceToReopen) {
                        setTimeout(() => {
                            this.show(referenceToReopen, instanceToReopen);
                        }, 100);
                    }
                }, 2000);
            }
        }, 300);
    }

    renderOtherBottles() {
        const container = document.getElementById('wine-detail-other-bottles');
        if (!container) return;

        const instance = this.currentInstance;
        const ref = this.currentReference;
        if (!instance || !ref) {
            container.style.display = 'none';
            return;
        }

        // Find all instances of the same wine from wineManager
        const allInstances = window.wineManager ? window.wineManager.wineInstances : [];
        const cellars = window.wineManager ? window.wineManager.cellars : [];
        const siblings = allInstances.filter(inst =>
            inst.reference.id === ref.id && inst.id !== instance.id && !inst.consumed
        );

        if (siblings.length === 0) {
            container.style.display = 'none';
            return;
        }

        const links = siblings.map(sib => {
            const loc = findInstanceLocation(sib, cellars);
            let locText = 'Unshelved';
            if (loc) {
                const { cellar, shelfIndex, side, position } = loc;
                const sideDisplay = side === 'single' ? '' : side === 'front' ? 'Front' : 'Back';
                const sideText = sideDisplay ? `, ${sideDisplay}` : '';
                locText = `${cellar.name}, Shelf ${shelfIndex + 1}${sideText}, Pos ${position + 1}`;
            }
            return `<a class="wine-detail-other-bottle-link wine-detail-location-link" data-instance-id="${sib.id}">${locText}</a>`;
        }).join('');

        container.innerHTML = `<div class="wine-detail-info-item">
            <span class="wine-detail-storage-label">Other bottles:</span>
            <div class="wine-detail-other-bottles-links">${links}</div>
        </div>`;
        container.style.display = '';

        // Click handlers
        container.querySelectorAll('.wine-detail-other-bottle-link').forEach(el => {
            el.addEventListener('click', () => {
                const sibId = el.getAttribute('data-instance-id');
                const sib = siblings.find(s => s.id === sibId);
                if (sib) this.swapToInstance(sib);
            });
        });
    }

    swapToInstance(newInstance) {
        const content = this.modal.querySelector('.wine-detail-content');
        if (!content) return;

        // Slide down
        content.style.transform = 'translateY(100%)';

        // After slide-down animation completes, swap content and slide back up
        setTimeout(() => {
            this.currentReference = newInstance.reference;
            this.currentInstance = newInstance;
            this.render();
            // Force reflow then slide up
            content.offsetHeight;
            content.style.transform = '';
        }, 300);
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
