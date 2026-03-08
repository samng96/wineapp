/**
 * Wine Detail View - Modal for displaying and editing wine details
 */
import { API } from './api.js';
import { findInstanceLocation } from './utils/locationUtils.js';
import { getNotificationOverlay } from './notificationOverlay.js';

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

        // Move wine button
        const moveBtn = document.getElementById('wine-detail-move-btn');
        if (moveBtn) {
            moveBtn.addEventListener('click', () => this.moveWine());
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
            // Preserve userReferenceId from the passed-in reference
            fullReference.userReferenceId = wineReference.userReferenceId;
            
            // Load user-specific fields (rating, tastingNotes) from UserWineReference if available
            if (fullReference.userReferenceId) {
                try {
                    const userRef = await API.get(`/user-wine-references/${fullReference.userReferenceId}`);
                    fullReference.rating = userRef.rating;
                    fullReference.tastingNotes = userRef.tastingNotes;
                } catch (error) {
                    console.error('Error loading user wine reference:', error);
                    // Fall back to passed-in reference values if API call fails
                    fullReference.rating = wineReference.rating;
                    fullReference.tastingNotes = wineReference.tastingNotes;
                }
            } else {
                // No user reference, use passed-in values
                fullReference.rating = wineReference.rating;
                fullReference.tastingNotes = wineReference.tastingNotes;
            }
            
            this.currentReference = fullReference;
            
            // Reload instance data to get latest location if we have an instance ID
            if (wineInstance && wineInstance.id) {
                try {
                    const updatedInstance = await API.get(`/wine-instances/${wineInstance.id}`);
                    this.currentInstance = updatedInstance;
                } catch (error) {
                    console.error('Error reloading instance data:', error);
                    // Continue with passed instance if reload fails
                }
            }
            
            // Reload cellars to ensure we have latest location data
            // Location is stored in cellar winePositions, not on the instance
            if (window.cellarManager) {
                try {
                    const cellars = await API.get('/cellars');
                    window.cellarManager.cellars = cellars;
                } catch (error) {
                    console.error('Error reloading cellars:', error);
                    // Continue with existing cellars if reload fails
                }
            }

            // Fetch fresh instances so renderOtherBottles shows newly added bottles
            try {
                this.freshInstances = await API.get('/wine-instances');
            } catch (error) {
                this.freshInstances = null;
            }

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

        // Varietals
        const varietalsItemEl = document.getElementById('wine-detail-varietals-item');
        const varietalsEl = document.getElementById('wine-detail-varietals');
        if (varietalsItemEl && varietalsEl) {
            if (ref.varietals && ref.varietals.length > 0) {
                varietalsEl.textContent = ref.varietals.join(', ');
                varietalsItemEl.style.display = 'flex';
            } else {
                varietalsItemEl.style.display = 'none';
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
        }

        // Show saving notification
        const ref = this.currentReference;
        const notification = getNotificationOverlay();
        notification.show('Saving...', {
            durationMs: 0, // Don't auto-dismiss - we'll hide it manually
            imageUrl: ref?.labelImageUrl || null
        });

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

            // Update notification message to success (keep same window)
            notification.updateMessage('Notes saved!', { durationMs: 2000 });

            if (saveBtn) {
                saveBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error saving tasting notes:', error);
            
            // Update notification message to error (keep same window)
            notification.updateMessage(`Failed to save: ${error.message || 'Unknown error'}`, { durationMs: 3000 });
            
            if (saveBtn) {
                saveBtn.disabled = false;
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

        // Price
        const priceItemEl = document.getElementById('wine-detail-price-item');
        const priceEl = document.getElementById('wine-detail-price');
        if (priceItemEl && priceEl) {
            if (instance && instance.price != null) {
                priceEl.textContent = `$${Number(instance.price).toFixed(2)}`;
                priceItemEl.style.display = 'flex';
            } else {
                priceItemEl.style.display = 'none';
            }
        }

        // Purchase date
        const purchaseDateItemEl = document.getElementById('wine-detail-purchase-date-item');
        const purchaseDateEl = document.getElementById('wine-detail-purchase-date');
        if (purchaseDateItemEl && purchaseDateEl) {
            if (instance && instance.purchaseDate) {
                purchaseDateEl.textContent = this.formatStoredDate(instance.purchaseDate);
                purchaseDateItemEl.style.display = 'flex';
            } else {
                purchaseDateItemEl.style.display = 'none';
            }
        }

        // Drink by date
        const drinkByItemEl = document.getElementById('wine-detail-drink-by-item');
        const drinkByEl = document.getElementById('wine-detail-drink-by-date');
        if (drinkByItemEl && drinkByEl) {
            if (instance && instance.drinkByDate) {
                drinkByEl.textContent = new Date(instance.drinkByDate).getFullYear();
                drinkByItemEl.style.display = 'flex';
            } else {
                drinkByItemEl.style.display = 'none';
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
        const moveBtn = document.getElementById('wine-detail-move-btn');
        
        // Check if wine is shelved (has location)
        let isShelved = false;
        if (instance && !instance.consumed) {
            let cellars = null;
            if (window.cellarManager && window.cellarManager.cellars && window.cellarManager.cellars.length > 0) {
                cellars = window.cellarManager.cellars;
            } else if (window.wineManager && window.wineManager.cellars && window.wineManager.cellars.length > 0) {
                cellars = window.wineManager.cellars;
            }
            if (cellars) {
                try {
                    const locationInfo = findInstanceLocation(instance, cellars);
                    isShelved = locationInfo !== null;
                } catch (error) {
                    console.error('Error finding instance location:', error);
                }
            }
        }
        
        if (instance && !instance.consumed) {
            if (instance.coravined && instance.coravinedDate) {
                // Show coravined date
                if (coravinedItemEl) {
                    coravinedItemEl.style.display = 'flex';
                }
                if (coravinedDateEl) {
                    coravinedDateEl.textContent = this.formatStoredDate(instance.coravinedDate);
                }
                // Hide coravin button but show action buttons container for drink/move buttons
                if (coravinBtn) {
                    coravinBtn.style.display = 'none';
                }
                if (actionButtonsEl) {
                    actionButtonsEl.style.display = 'flex';
                }
                // Show move button only if shelved
                if (moveBtn) {
                    moveBtn.style.display = isShelved ? 'inline-block' : 'none';
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
                // Show move button only if shelved
                if (moveBtn) {
                    moveBtn.style.display = isShelved ? 'inline-block' : 'none';
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

        // Show confirmation via notification overlay
        const ref = this.currentReference;
        const confirmed = await getNotificationOverlay().confirm(
            'Are you sure you want to open this wine with a Coravin?',
            { imageUrl: ref?.labelImageUrl || null }
        );
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

    async moveWine() {
        if (!this.currentInstance) return;

        // Find the wine's current location in cellars
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

        // If not shelved, nothing to do
        if (!cellarLocation) {
            return;
        }

        const moveBtn = document.getElementById('wine-detail-move-btn');
        if (moveBtn) {
            moveBtn.disabled = true;
        }

        try {
            // Remove from cellar location (unshelve) - now supported by API
            await API.updateWineInstanceLocation(this.currentInstance.id, {
                oldCellarId: cellarLocation.cellarId,
                newCellarId: null,  // Remove from cellar (unshelve)
                shelfIndex: null,
                side: null,
                position: null
            });

            // Update local cellar data structure
            if (window.cellarManager && window.cellarManager.cellars) {
                const cellar = window.cellarManager.cellars.find(c => c.id === cellarLocation.cellarId);
                if (cellar) {
                    // Remove instance from cellar's winePositions
                    const shelfKey = String(cellarLocation.shelfIndex);
                    if (cellar.winePositions && cellar.winePositions[shelfKey]) {
                        const shelfPositions = cellar.winePositions[shelfKey];
                        const sideArray = shelfPositions[cellarLocation.side];
                        if (sideArray) {
                            const posIndex = sideArray.indexOf(this.currentInstance.id);
                            if (posIndex !== -1) {
                                sideArray[posIndex] = null;
                            }
                        }
                    }
                }
            }

            // Reload cellars to ensure we have latest location data
            if (window.cellarManager) {
                try {
                    const cellars = await API.get('/cellars');
                    window.cellarManager.cellars = cellars;
                } catch (error) {
                    console.error('Error reloading cellars:', error);
                }
            }

            // Re-render storage info to update location and hide move button
            this.renderStorageInfo();

            // Refresh wine list so the unshelved/shelved status stays accurate
            if (window.wineManager) {
                window.wineManager.loadWines();
            }

            // Show success notification
            const ref = this.currentReference;
            getNotificationOverlay().show('Wine is now unshelved. Click on an empty shelf to place the wine there.', {
                durationMs: 4000,
                imageUrl: ref?.labelImageUrl || null
            });

            if (moveBtn) {
                moveBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error moving wine:', error);
            alert(`Failed to move wine: ${error.message || 'Unknown error'}`);
            
            if (moveBtn) {
                moveBtn.disabled = false;
            }
        }
    }

    async drinkWine() {
        if (!this.currentInstance) return;

        // Show confirmation via notification overlay
        const ref = this.currentReference;
        const confirmed = await getNotificationOverlay().confirm(
            'Are you sure you want to mark this wine as consumed?',
            { imageUrl: ref?.labelImageUrl || null }
        );
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

            // Update freshInstances so this bottle no longer appears in sibling "other bottles"
            if (this.freshInstances) {
                const idx = this.freshInstances.findIndex(i => i.id === this.currentInstance.id);
                if (idx !== -1) this.freshInstances[idx].consumed = true;
            }

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
                positionEl.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });

                this.blinkHighlight(positionEl, () => {
                    if (referenceToReopen && instanceToReopen) {
                        this.show(referenceToReopen, instanceToReopen);
                    }
                });
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

        let siblings = [];
        let cellars = [];

        // Use freshInstances fetched in show() — ensures newly added bottles appear
        if (this.freshInstances && ref.userReferenceId) {
            if (window.cellarManager && window.cellarManager.cellars) {
                cellars = window.cellarManager.cellars;
            } else if (window.wineManager) {
                cellars = window.wineManager.cellars || [];
            }
            siblings = this.freshInstances
                .filter(inst => inst && inst.referenceId === ref.userReferenceId && inst.id !== instance.id && !inst.consumed)
                .map(inst => ({ ...inst, reference: ref }));
        } else {
            // Fall back to cached instances from cellarManager / wineManager
            let allInstances = [];
            if (window.cellarManager) {
                if (window.cellarManager.currentInstanceMap) {
                    allInstances = Object.values(window.cellarManager.currentInstanceMap);
                } else if (window.cellarManager.wineInstances) {
                    allInstances = window.cellarManager.wineInstances;
                }
                if (window.cellarManager.cellars && window.cellarManager.cellars.length > 0) {
                    cellars = window.cellarManager.cellars;
                }
            }
            if (allInstances.length === 0 && window.wineManager) {
                allInstances = window.wineManager.wineInstances || [];
            }
            if (cellars.length === 0 && window.wineManager) {
                cellars = window.wineManager.cellars || [];
            }

            const getGlobalRefId = (inst) => {
                if (!inst) return null;
                if (inst.reference && inst.reference.id) return inst.reference.id;
                if (!inst.referenceId) return null;
                if (window.cellarManager && window.cellarManager.userRefToGlobalRefId) {
                    return window.cellarManager.userRefToGlobalRefId[inst.referenceId] || inst.referenceId;
                }
                if (window.wineManager && window.wineManager.userRefToGlobalRefId) {
                    return window.wineManager.userRefToGlobalRefId[inst.referenceId] || inst.referenceId;
                }
                return inst.referenceId;
            };

            const refGlobalId = ref.id;
            siblings = allInstances.filter(inst => {
                if (!inst) return false;
                const instGlobalRefId = getGlobalRefId(inst);
                return instGlobalRefId === refGlobalId && inst.id !== instance.id && !inst.consumed;
            });
        }

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
                if (!sib) return;

                // Check if the sibling has a cellar location
                const loc = findInstanceLocation(sib, cellars);
                if (loc && window.cellarManager) {
                    // Navigate to cellar, highlight position, then reopen card for this bottle
                    this.navigateToOtherBottle(sib, loc);
                } else {
                    // Unshelved — just swap the card content
                    this.swapToInstance(sib);
                }
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

    async navigateToOtherBottle(siblingInstance, location) {
        const { cellar, shelfIndex, side, position } = location;

        // Close the wine detail modal
        this.hide();

        // Navigate to the cellar detail view
        await window.cellarManager.showCellarDetail(cellar.id);

        // Wait for DOM to update, then scroll to position and highlight
        setTimeout(() => {
            const positionId = `wine-pos-${shelfIndex}-${side}-${position}`;
            const positionEl = document.getElementById(positionId);

            if (positionEl) {
                positionEl.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });

                this.blinkHighlight(positionEl, () => {
                    this.show(siblingInstance.reference, siblingInstance);
                });
            }
        }, 300);
    }

    blinkHighlight(el, onComplete) {
        const on = () => {
            el.style.outline = '3px solid #d32f2f';
            el.style.outlineOffset = '3px';
        };
        const off = () => {
            el.style.outline = '';
            el.style.outlineOffset = '';
        };

        // Blink 3 times: on 400ms, off 200ms, repeat — then callback
        const blink = (count) => {
            on();
            setTimeout(() => {
                off();
                if (count > 1) {
                    setTimeout(() => blink(count - 1), 200);
                } else {
                    setTimeout(() => { if (onComplete) onComplete(); }, 100);
                }
            }, 400);
        };
        blink(3);
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
