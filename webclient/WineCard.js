/**
 * Wine Card Component - Reusable hover card for displaying wine details
 */
class WineCard {
    constructor() {
        this.card = null;
        this.hideTimeout = null;
        this.init();
    }

    init() {
        // Create the wine card element
        this.card = document.createElement('div');
        this.card.id = 'wine-card';
        this.card.className = 'wine-card hidden';
        document.body.appendChild(this.card);
    }

    show(wineReference, wineInstance = null, x = 0, y = 0, options = {}) {
        if (!wineReference) return;

        // Clear any pending hide timeout
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }

        // Extract data
        const ref = wineReference;
        const instance = wineInstance;
        const cellars = options.cellars || [];
        const allInstances = options.allInstances || [];
        const locationInfo = options.locationInfo || null;

        // Count bottles stored for this reference
        const bottlesStored = this.countBottlesStored(ref.id, allInstances);
        
        // Count other bottles (excluding this instance if not consumed)
        const otherBottlesCount = instance && bottlesStored > 0 && !instance.consumed ? bottlesStored - 1 : bottlesStored;
        
        // Format location string
        let locationStr = 'Unshelved';
        if (locationInfo) {
            const { cellar, shelfIndex, side, position } = locationInfo;
            const sideDisplay = side === 'single' ? '' : side === 'front' ? 'Front' : 'Back';
            const sideText = sideDisplay ? `, ${sideDisplay}` : '';
            locationStr = `${cellar.name}, Shelf ${shelfIndex + 1}${sideText}, Position ${position + 1}`;
        }
        
        // Get country flag
        const flag = this.getCountryFlag(ref.country);
        
        // Format wine type
        const wineTypeDisplay = ref.type ? `${ref.type} Wine` : '';
        
        // Format region and country
        const regionText = ref.region ? `${ref.region}, ` : '';
        const countryText = ref.country ? `<b>${this.escapeHtml(ref.country)}</b>` : '';

        let html = '<div class="wine-card-content">';
        
        // Left side - Label image
        html += '<div class="wine-card-image">';
        if (ref.labelImageUrl) {
            html += `<img src="${this.escapeHtml(ref.labelImageUrl)}" alt="${this.escapeHtml(ref.name)}" />`;
        } else {
            html += '<div class="wine-card-image-placeholder">🍷</div>';
        }
        html += '</div>';

        // Right side - Details (matching wine list format)
        html += '<div class="wine-card-details">';
        
        // Vintage and Name
        html += '<div class="wine-card-name">';
        if (ref.vintage) {
            html += `<span class="wine-card-vintage">${ref.vintage}</span> `;
        }
        html += `<span class="wine-card-title">${this.escapeHtml(ref.name)}</span>`;
        html += '</div>';
        
        // Producer
        if (ref.producer) {
            html += `<div class="wine-card-producer">${this.escapeHtml(ref.producer)}</div>`;
        }
        
        // Country info with flag
        html += '<div class="wine-card-country-info">';
        if (flag) {
            html += `<span class="wine-card-flag">${flag}</span> `;
        }
        if (wineTypeDisplay) {
            html += `<span>${this.escapeHtml(wineTypeDisplay)}</span>`;
        }
        if (ref.region || ref.country) {
            html += ` <span class="wine-card-separator">•</span> ${regionText}${countryText}`;
        }
        html += '</div>';
        
        // Storage info
        html += '<div class="wine-card-storage">';
        html += `<span>Stored: ${instance && instance.storedDate ? this.formatStoredDate(instance.storedDate) : 'N/A'}${otherBottlesCount > 0 ? ',' : ''}</span>`;
        if (otherBottlesCount > 0) {
            html += `<span>${otherBottlesCount} additional bottle${otherBottlesCount !== 1 ? 's' : ''} owned</span>`;
        }
        html += '</div>';
        
        // Location
        html += `<div class="wine-card-location">Location: ${this.escapeHtml(locationStr)}</div>`;

        html += '</div>'; // wine-card-details
        html += '</div>'; // wine-card-content

        this.card.innerHTML = html;
        this.card.classList.remove('hidden');

        // Position the card
        this.positionCard(x, y);
    }

    getCountryFlag(country) {
        if (!country) return '';
        
        const countryMap = {
            'United States': '🇺🇸',
            'US': '🇺🇸',
            'USA': '🇺🇸',
            'U.S.A.': '🇺🇸',
            'France': '🇫🇷',
            'Italy': '🇮🇹',
            'Spain': '🇪🇸',
            'Australia': '🇦🇺',
            'Chile': '🇨🇱',
            'Argentina': '🇦🇷',
            'Germany': '🇩🇪',
            'Portugal': '🇵🇹',
            'South Africa': '🇿🇦',
            'New Zealand': '🇳🇿',
            'Canada': '🇨🇦',
            'Greece': '🇬🇷',
            'Austria': '🇦🇹',
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

    countBottlesStored(referenceId, allInstances) {
        return allInstances.filter(inst => {
            // Handle both WineInstance objects (with reference.id) and plain API objects (with referenceId)
            const instRefId = inst.reference ? inst.reference.id : inst.referenceId;
            return instRefId === referenceId && !inst.consumed;
        }).length;
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

    positionCard(x, y) {
        if (!this.card) return;

        // Get card dimensions
        const cardRect = this.card.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const offset = 15; // Distance from cursor

        let left = x + offset;
        let top = y + offset;

        // Adjust if card would go off right edge
        if (left + cardRect.width > viewportWidth) {
            left = x - cardRect.width - offset;
        }

        // Adjust if card would go off bottom edge
        if (top + cardRect.height > viewportHeight) {
            top = y - cardRect.height - offset;
        }

        // Ensure card doesn't go off left or top edges
        left = Math.max(10, left);
        top = Math.max(10, top);

        this.card.style.left = `${left}px`;
        this.card.style.top = `${top}px`;
    }

    hide(delay = 0) {
        if (delay > 0) {
            // Delay hiding to allow moving from element to card
            this.hideTimeout = setTimeout(() => {
                if (this.card) {
                    this.card.classList.add('hidden');
                }
                this.hideTimeout = null;
            }, delay);
        } else {
            if (this.hideTimeout) {
                clearTimeout(this.hideTimeout);
                this.hideTimeout = null;
            }
            if (this.card) {
                this.card.classList.add('hidden');
            }
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create singleton instance
let wineCardInstance = null;

export function getWineCard() {
    if (!wineCardInstance) {
        wineCardInstance = new WineCard();
    }
    return wineCardInstance;
}

export { WineCard };
