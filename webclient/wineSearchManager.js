/**
 * WineSearchManager - Manages the wine search view with Vivino integration
 */
import { API } from './api.js';
import { WineReference } from './models/WineReference.js';

export class WineSearchManager {
    constructor() {
        this.searchResults = [];
        this.init();
    }

    init() {
        this.setupElements();
        this.setupEventListeners();
    }

    setupElements() {
        this.searchInput = document.getElementById('wine-search-name');
        this.searchBtn = document.getElementById('wine-search-btn');
        this.addManuallyBtn = document.getElementById('wine-add-manually-btn');
        this.resultsContainer = document.getElementById('wine-search-results');
        this.backBtn = document.getElementById('back-to-add-wine-from-search-btn');
    }

    setupEventListeners() {
        // Search button
        if (this.searchBtn) {
            this.searchBtn.addEventListener('click', () => this.performSearch());
        }

        // Enter key on search input
        if (this.searchInput) {
            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performSearch();
                }
            });
        }

        // Add manually button
        if (this.addManuallyBtn) {
            this.addManuallyBtn.addEventListener('click', () => {
                if (window.app && window.app.showView) {
                    window.app.showView('wine-reference-form');
                }
            });
        }

        // Back button
        if (this.backBtn) {
            this.backBtn.addEventListener('click', () => {
                if (window.app && window.app.showView) {
                    window.app.showView('photo');
                }
            });
        }
    }

    async performSearch() {
        const searchTerm = this.searchInput ? this.searchInput.value.trim() : '';
        
        if (!searchTerm) {
            alert('Please enter a wine name to search');
            return;
        }

        // Show loading state
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">Searching...</p>';
        }

        try {
            // Search Vivino
            const results = await API.searchVivino(searchTerm);
            
            // Convert to WineReference objects
            this.searchResults = results.map(result => {
                // If result is already in WineReference format, use fromDict
                // Otherwise, create a temporary reference object
                if (result.id) {
                    return WineReference.fromDict(result);
                } else {
                    // Create a temporary reference from Vivino data
                    return new WineReference(
                        `vivino-${Date.now()}-${Math.random()}`, // Temporary ID
                        result.name || searchTerm,
                        result.type || 'Other',
                        result.vintage,
                        result.producer,
                        result.varietals || [],
                        result.region,
                        result.country,
                        result.rating,
                        result.tastingNotes,
                        result.labelImageUrl
                    );
                }
            });

            // Render results
            this.renderResults();
        } catch (error) {
            console.error('Error searching Vivino:', error);
            if (this.resultsContainer) {
                this.resultsContainer.innerHTML = `<p style="text-align: center; padding: 40px; color: #f44336;">Error searching: ${error.message || 'Unknown error'}</p>`;
            }
        }
    }

    renderResults() {
        if (!this.resultsContainer) return;

        if (this.searchResults.length === 0) {
            this.resultsContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No wines found</p>';
            return;
        }

        // Render results similar to wine list but without Location and Stored date
        this.resultsContainer.innerHTML = this.searchResults.map(reference => {
            // Get country flag (reuse logic from wineManager)
            const flag = this.getCountryFlag(reference.country);
            
            // Format wine type
            const wineTypeDisplay = reference.type ? `${reference.type} Wine` : '';
            
            // Format region and country
            const regionText = reference.region ? `${reference.region}, ` : '';
            const countryText = reference.country ? `${this.escapeHtml(reference.country)}` : '';

            // Format varietals
            const varietalsText = reference.varietals && reference.varietals.length > 0 
                ? reference.varietals.join(', ') 
                : '';

            return `
                <div class="wine-item wine-reference-item" data-reference-id="${reference.id}">
                    <div class="wine-item-image">
                        ${reference.labelImageUrl ? 
                            `<img src="${this.escapeHtml(reference.labelImageUrl)}" alt="${this.escapeHtml(reference.name)}" />` :
                            '<div class="wine-item-placeholder">🍷</div>'
                        }
                    </div>
                    <div class="wine-item-details">
                        <div class="wine-item-meta">
                            ${reference.vintage ? `<span class="wine-item-vintage">${reference.vintage}</span>` : ''}
                            <span class="wine-item-title">${this.escapeHtml(reference.name)}</span>
                        </div>
                        ${reference.producer ? `<div class="wine-item-producer">${this.escapeHtml(reference.producer)}</div>` : ''}
                        <div class="wine-item-country-info">
                            ${flag ? `<span class="wine-item-flag">${flag}</span> ` : ''}
                            ${wineTypeDisplay ? `${this.escapeHtml(wineTypeDisplay)}` : ''}
                            ${(reference.region || reference.country) ? ` • ${regionText}${countryText}` : ''}
                        </div>
                        ${varietalsText ? `<div class="wine-item-varietals">${this.escapeHtml(varietalsText)}</div>` : ''}
                        ${reference.rating ? `<div class="wine-item-rating">
                            <span class="wine-item-rating-label">Rating: </span>
                            <span class="wine-item-rating-stars">
                                ${[1, 2, 3, 4, 5].map(star => 
                                    `<span class="rating-star ${star <= reference.rating ? 'filled' : ''}" title="${star} star${star !== 1 ? 's' : ''}">★</span>`
                                ).join('')}
                            </span>
                        </div>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        // Set up click handlers
        this.setupResultClickHandlers();
    }

    setupResultClickHandlers() {
        const resultItems = document.querySelectorAll('.wine-reference-item');
        resultItems.forEach(item => {
            item.addEventListener('click', () => {
                const referenceId = item.getAttribute('data-reference-id');
                const reference = this.searchResults.find(ref => ref.id === referenceId);
                
                if (reference) {
                    // Create wine reference from search result
                    this.createWineFromReference(reference);
                }
            });
        });
    }

    async createWineFromReference(reference) {
        try {
            // Create wine reference via API
            const referenceData = {
                name: reference.name,
                type: reference.type,
                vintage: reference.vintage,
                producer: reference.producer,
                varietals: reference.varietals || [],
                region: reference.region,
                country: reference.country,
                rating: reference.rating,
                tastingNotes: reference.tastingNotes,
                labelImageUrl: reference.labelImageUrl
            };

            const createdReference = await API.createWineReference(referenceData);
            
            alert('Wine reference created successfully!');
            
            // Navigate back to add wines view
            if (window.app && window.app.showView) {
                window.app.showView('photo');
            }
        } catch (error) {
            console.error('Error creating wine reference:', error);
            if (error.message.includes('already exists')) {
                alert('This wine reference already exists. You can add it from your wine list.');
            } else {
                alert('Error creating wine reference: ' + error.message);
            }
        }
    }

    getCountryFlag(country) {
        // Reuse the same flag mapping logic as wineManager
        if (!country) return '';
        
        const countryMap = {
            'USA': '🇺🇸',
            'United States': '🇺🇸',
            'US': '🇺🇸',
            'France': '🇫🇷',
            'Italy': '🇮🇹',
            'Spain': '🇪🇸',
            'Germany': '🇩🇪',
            'Portugal': '🇵🇹',
            'Australia': '🇦🇺',
            'Chile': '🇨🇱',
            'Argentina': '🇦🇷',
            'South Africa': '🇿🇦',
            'New Zealand': '🇳🇿',
            'Canada': '🇨🇦',
            'Austria': '🇦🇹',
            'Greece': '🇬🇷',
            'Hungary': '🇭🇺',
            'Romania': '🇷🇴',
            'Bulgaria': '🇧🇬',
            'Croatia': '🇭🇷',
            'Slovenia': '🇸🇮',
            'Georgia': '🇬🇪',
            'Lebanon': '🇱🇧',
            'Israel': '🇮🇱',
            'Turkey': '🇹🇷',
            'Brazil': '🇧🇷',
            'Uruguay': '🇺🇾',
            'Mexico': '🇲🇽',
            'Japan': '🇯🇵',
            'China': '🇨🇳',
            'India': '🇮🇳',
            'United Kingdom': '🇬🇧',
            'UK': '🇬🇧',
            'England': '🇬🇧'
        };
        
        const normalizedCountry = country.trim();
        return countryMap[normalizedCountry] || '';
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Called when view is shown
    show() {
        // Clear previous results
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '';
        }
        // Focus search input
        if (this.searchInput) {
            this.searchInput.value = '';
            this.searchInput.focus();
        }
    }

    // Called when view is hidden
    hide() {
        // Nothing to do
    }
}
