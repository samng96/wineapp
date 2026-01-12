/**
 * WineReference model - represents a wine reference (singleton for each wine type)
 * 
 * @property {string} id - Unique identifier
 * @property {string} name - Name of the wine
 * @property {string} type - Type of wine (e.g., 'Red', 'White', 'Rosé', 'Sparkling')
 * @property {number|null} vintage - Year the wine was produced
 * @property {string|null} producer - Name of the wine producer/winery
 * @property {Array<string>|null} varietals - List of grape varietals used
 * @property {string|null} region - Wine region
 * @property {string|null} country - Country of origin
 * @property {number|null} rating - Rating from 1-5
 * @property {string|null} tastingNotes - Tasting notes or description
 * @property {string|null} labelImageUrl - URL to the wine label image in blob storage
 * @property {string|null} labelImageLocalPath - Local file path for downloaded label image (client-side only)
 * @property {number} version - Version number for conflict resolution
 * @property {string|null} createdAt - ISO 8601 timestamp when created
 * @property {string|null} updatedAt - ISO 8601 timestamp when last updated
 */
export class WineReference {
    constructor(id, name, type, vintage = null, producer = null, varietals = null, 
                region = null, country = null, rating = null, tastingNotes = null, 
                labelImageUrl = null, version = 1, createdAt = null, updatedAt = null) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.vintage = vintage;
        this.producer = producer;
        this.varietals = varietals;
        this.region = region;
        this.country = country;
        this.rating = rating;
        this.tastingNotes = tastingNotes;
        this.labelImageUrl = labelImageUrl;
        this.labelImageLocalPath = null; // Client-side only: local file path
        this.version = version;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    /**
     * Get unique key for deduplication (name, vintage, producer)
     * @returns {Array} Tuple of [name, vintage, producer]
     */
    getUniqueKey() {
        return [this.name, this.vintage, this.producer];
    }

    /**
     * Create a WineReference instance from API response dictionary
     * @param {Object} dict - Dictionary from API response
     * @returns {WineReference} WineReference instance
     */
    static fromDict(dict) {
        return new WineReference(
            dict.id,
            dict.name,
            dict.type,
            dict.vintage,
            dict.producer,
            dict.varietals,
            dict.region,
            dict.country,
            dict.rating,
            dict.tastingNotes,
            dict.labelImageUrl,
            dict.version || 1,
            dict.createdAt,
            dict.updatedAt
        );
    }
}

