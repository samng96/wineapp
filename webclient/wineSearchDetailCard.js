/**
 * WineSearchDetailCard - Bottom sheet detail card for Vivino search results
 */
import { API } from './api.js';

class WineSearchDetailCard {
    constructor() {
        this.modal = document.getElementById('wine-search-detail-modal');
        this.currentReference = null;
        this.quantity = 1;
        this.populateVintageSelect();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        const closeBtn = document.getElementById('wine-search-detail-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // Overlay click to close
        const overlay = this.modal ? this.modal.querySelector('.wine-detail-overlay') : null;
        if (overlay) {
            overlay.addEventListener('click', () => this.hide());
        }

        // Quantity buttons
        const qtyDown = document.getElementById('wine-search-detail-qty-down');
        const qtyUp = document.getElementById('wine-search-detail-qty-up');
        if (qtyDown) {
            qtyDown.addEventListener('click', () => this.updateQuantity(-1));
        }
        if (qtyUp) {
            qtyUp.addEventListener('click', () => this.updateQuantity(1));
        }

        // Add to collection button
        const addBtn = document.getElementById('wine-search-detail-add-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.handleAddToCollection());
        }
    }

    populateVintageSelect() {
        const select = document.getElementById('wine-search-detail-vintage');
        if (!select) return;
        const currentYear = new Date().getFullYear();
        for (let year = currentYear; year >= 1950; year--) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            select.appendChild(option);
        }
        select.value = '2020';
    }

    show(reference) {
        if (!reference || !this.modal) return;

        this.currentReference = reference;
        this.quantity = 1;

        // Name
        const nameEl = document.getElementById('wine-search-detail-name');
        if (nameEl) {
            const vintageText = reference.vintage ? `${reference.vintage} ` : '';
            nameEl.textContent = `${vintageText}${reference.name || 'Unknown Wine'}`;
        }

        // Meta line (producer, type, region, country)
        const metaEl = document.getElementById('wine-search-detail-meta');
        if (metaEl) {
            const metaParts = [];
            if (reference.producer) metaParts.push(reference.producer);
            if (reference.type) metaParts.push(`${reference.type} Wine`);
            if (reference.region) metaParts.push(reference.region);
            if (reference.country) metaParts.push(reference.country);
            metaEl.textContent = metaParts.join(' \u2022 ');
        }

        // Image
        const imageEl = document.getElementById('wine-search-detail-image');
        const placeholderEl = document.getElementById('wine-search-detail-image-placeholder');
        if (imageEl && placeholderEl) {
            if (reference.labelImageUrl) {
                imageEl.src = reference.labelImageUrl;
                imageEl.style.display = 'block';
                placeholderEl.style.display = 'none';
            } else {
                imageEl.style.display = 'none';
                placeholderEl.style.display = 'flex';
            }
        }

        // Vivino rating (read-only)
        const ratingSection = document.getElementById('wine-search-detail-rating-section');
        const ratingEl = document.getElementById('wine-search-detail-rating');
        if (ratingSection && ratingEl) {
            if (reference.rating) {
                ratingEl.textContent = `${reference.rating} \u2605`;
                ratingSection.style.display = '';
            } else {
                ratingSection.style.display = 'none';
            }
        }

        // Info rows
        this.renderInfoRows(reference);

        // Pre-fill vintage if available, otherwise default to 2020
        const vintageSelect = document.getElementById('wine-search-detail-vintage');
        if (vintageSelect) {
            vintageSelect.value = reference.vintage || '2020';
        }

        // Reset price
        const priceInput = document.getElementById('wine-search-detail-price');
        if (priceInput) {
            priceInput.value = '';
        }

        // Reset quantity
        this.quantity = 1;
        const qtyEl = document.getElementById('wine-search-detail-qty-value');
        if (qtyEl) {
            qtyEl.textContent = '1';
        }

        // Show modal
        this.modal.classList.remove('hidden');
    }

    hide() {
        if (this.modal) {
            this.modal.classList.add('hidden');
        }
        this.currentReference = null;
    }

    renderInfoRows(reference) {
        const container = document.getElementById('wine-search-detail-info');
        if (!container) return;

        let html = '';

        if (reference.type) {
            html += this.renderInfoRow('Type', `${reference.type} Wine`);
        }
        if (reference.producer) {
            html += this.renderInfoRow('Producer', reference.producer);
        }
        if (reference.varietals && reference.varietals.length > 0) {
            html += this.renderInfoRow('Varietals', reference.varietals.join(', '));
        }
        if (reference.region) {
            html += this.renderInfoRow('Region', reference.region);
        }
        if (reference.country) {
            const flag = this.getCountryFlag(reference.country);
            const display = flag ? `${flag} ${this.escapeHtml(reference.country)}` : this.escapeHtml(reference.country);
            html += `<div class="wine-detail-info-item">
                <span class="wine-detail-storage-label">Country</span>
                <span class="wine-detail-info-value">${display}</span>
            </div>`;
        }

        container.innerHTML = html;
    }

    renderInfoRow(label, value) {
        return `<div class="wine-detail-info-item">
            <span class="wine-detail-storage-label">${this.escapeHtml(label)}</span>
            <span class="wine-detail-info-value">${this.escapeHtml(value)}</span>
        </div>`;
    }

    updateQuantity(delta) {
        const newQty = this.quantity + delta;
        if (newQty < 1) return;
        this.quantity = newQty;
        const qtyEl = document.getElementById('wine-search-detail-qty-value');
        if (qtyEl) {
            qtyEl.textContent = String(this.quantity);
        }
    }

    async handleAddToCollection() {
        const vintageSelect = document.getElementById('wine-search-detail-vintage');
        const priceInput = document.getElementById('wine-search-detail-price');

        const vintageValue = vintageSelect ? parseInt(vintageSelect.value) : null;
        const priceText = priceInput ? priceInput.value.trim() : '';
        const priceValue = priceText ? parseFloat(priceText) : null;
        const quantity = this.quantity;
        const reference = this.currentReference;

        if (!reference) return;

        try {
            // 1. Create or get GlobalWineReference
            const globalRef = await API.createOrGetWineReference({
                name: reference.name,
                type: reference.type,
                vintage: vintageValue,
                producer: reference.producer,
                varietals: reference.varietals || [],
                region: reference.region,
                country: reference.country,
                labelImageUrl: reference.labelImageUrl,
            });

            // 2. Find or create UserWineReference
            const allUserRefs = await API.getUserWineReferences();
            let userRef = allUserRefs.find(r => r.globalReferenceId === globalRef.id);
            if (!userRef) {
                const userRefData = { globalReferenceId: globalRef.id };
                if (reference.rating) userRefData.rating = Math.round(reference.rating);
                userRef = await API.createUserWineReference(userRefData);
            }

            // 3. Create WineInstances (one per bottle)
            for (let i = 0; i < quantity; i++) {
                const instanceData = { referenceId: userRef.id };
                if (priceValue !== null) instanceData.price = priceValue;
                await API.createWineInstance(instanceData);
            }

            // 4. Hide detail card and navigate to wines view showing unshelved, sorted by stored date
            this.hide();
            if (window.app && window.app.showView) {
                window.app.showView('wines', {
                    showUnshelvedOnly: true,
                    sortBy: 'stored',
                    sortOrder: 'desc'
                });
            }
        } catch (error) {
            console.error('Error adding to collection:', error);
            alert('Error adding wine to collection: ' + error.message);
        }
    }

    getCountryFlag(country) {
        if (!country) return '';
        const countryMap = {
            'United States': '\ud83c\uddfa\ud83c\uddf8',
            'US': '\ud83c\uddfa\ud83c\uddf8',
            'USA': '\ud83c\uddfa\ud83c\uddf8',
            'France': '\ud83c\uddeb\ud83c\uddf7',
            'Italy': '\ud83c\uddee\ud83c\uddf9',
            'Spain': '\ud83c\uddea\ud83c\uddf8',
            'Australia': '\ud83c\udde6\ud83c\uddfa',
            'Chile': '\ud83c\udde8\ud83c\uddf1',
            'Argentina': '\ud83c\udde6\ud83c\uddf7',
            'Germany': '\ud83c\udde9\ud83c\uddea',
            'Portugal': '\ud83c\uddf5\ud83c\uddf9',
            'South Africa': '\ud83c\uddff\ud83c\udde6',
            'New Zealand': '\ud83c\uddf3\ud83c\uddff',
            'Canada': '\ud83c\udde8\ud83c\udde6',
            'Greece': '\ud83c\uddec\ud83c\uddf7',
            'Austria': '\ud83c\udde6\ud83c\uddf9',
            'Hungary': '\ud83c\udded\ud83c\uddfa',
            'Romania': '\ud83c\uddf7\ud83c\uddf4',
            'Bulgaria': '\ud83c\udde7\ud83c\uddec',
            'Croatia': '\ud83c\udded\ud83c\uddf7',
            'Slovenia': '\ud83c\uddf8\ud83c\uddee',
            'Georgia': '\ud83c\uddec\ud83c\uddea',
            'Lebanon': '\ud83c\uddf1\ud83c\udde7',
            'Israel': '\ud83c\uddee\ud83c\uddf1',
            'Turkey': '\ud83c\uddf9\ud83c\uddf7',
            'Brazil': '\ud83c\udde7\ud83c\uddf7',
            'Uruguay': '\ud83c\uddfa\ud83c\uddfe',
            'Mexico': '\ud83c\uddf2\ud83c\uddfd',
            'Japan': '\ud83c\uddef\ud83c\uddf5',
            'China': '\ud83c\udde8\ud83c\uddf3',
            'India': '\ud83c\uddee\ud83c\uddf3',
            'United Kingdom': '\ud83c\uddec\ud83c\udde7',
            'UK': '\ud83c\uddec\ud83c\udde7',
            'England': '\ud83c\uddec\ud83c\udde7'
        };
        return countryMap[country.trim()] || '';
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Singleton
let wineSearchDetailCardInstance = null;

export function getWineSearchDetailCard() {
    if (!wineSearchDetailCardInstance) {
        wineSearchDetailCardInstance = new WineSearchDetailCard();
    }
    return wineSearchDetailCardInstance;
}

export { WineSearchDetailCard };
