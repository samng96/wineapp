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

    show(wineReference, wineInstance = null, x = 0, y = 0) {
        if (!wineReference) return;

        // Clear any pending hide timeout
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }

        // Build card content
        const labelImage = wineReference.labelImageUrl || '';
        const name = wineReference.name || 'Unknown Wine';
        const producer = wineReference.producer || '';
        const vintage = wineReference.vintage || 'NV';
        const type = wineReference.type || '';
        const region = wineReference.region || '';
        const country = wineReference.country || '';
        const varietals = wineReference.varietals || [];
        const rating = wineReference.rating || null;
        const tastingNotes = wineReference.tastingNotes || '';

        let html = '<div class="wine-card-content">';
        
        // Left side - Label image
        html += '<div class="wine-card-image">';
        if (labelImage) {
            html += `<img src="${this.escapeHtml(labelImage)}" alt="${this.escapeHtml(name)}" />`;
        } else {
            html += '<div class="wine-card-image-placeholder">No Image</div>';
        }
        html += '</div>';

        // Right side - Details
        html += '<div class="wine-card-details">';
        
        // Name
        html += `<h3 class="wine-card-name">${this.escapeHtml(name)}</h3>`;
        
        // Producer
        if (producer) {
            html += `<div class="wine-card-producer">${this.escapeHtml(producer)}</div>`;
        }
        
        // Vintage and Type
        html += '<div class="wine-card-meta">';
        html += `<span class="wine-card-vintage">${vintage === 'NV' ? 'Non-Vintage' : vintage}</span>`;
        if (type) {
            html += `<span class="wine-card-type">${this.escapeHtml(type)}</span>`;
        }
        html += '</div>';

        // Region and Country
        if (region || country) {
            html += '<div class="wine-card-location">';
            if (region) html += `<span>${this.escapeHtml(region)}</span>`;
            if (region && country) html += '<span>, </span>';
            if (country) html += `<span>${this.escapeHtml(country)}</span>`;
            html += '</div>';
        }

        // Varietals
        if (varietals.length > 0) {
            html += `<div class="wine-card-varietals">${varietals.map(v => this.escapeHtml(v)).join(', ')}</div>`;
        }

        // Rating
        if (rating !== null && rating !== undefined) {
            html += '<div class="wine-card-rating">';
            html += '<span class="wine-card-rating-label">Rating: </span>';
            html += '<span class="wine-card-rating-value">';
            // If rating is a number, show stars; otherwise show as text
            if (typeof rating === 'number') {
                html += '<span class="wine-card-rating-stars">';
                for (let i = 0; i < 5; i++) {
                    html += `<span class="star ${i < Math.round(rating) ? 'filled' : ''}">★</span>`;
                }
                html += '</span>';
            } else {
                html += `<span>${this.escapeHtml(String(rating))}</span>`;
            }
            html += '</span>';
            html += '</div>';
        }

        // Tasting Notes
        if (tastingNotes) {
            html += `<div class="wine-card-notes">${this.escapeHtml(tastingNotes)}</div>`;
        }

        html += '</div>'; // wine-card-details
        html += '</div>'; // wine-card-content

        this.card.innerHTML = html;
        this.card.classList.remove('hidden');

        // Position the card
        this.positionCard(x, y);
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
