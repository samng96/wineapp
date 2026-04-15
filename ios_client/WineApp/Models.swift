import Foundation

// MARK: - GlobalWineReference

struct GlobalWineReference: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let type: String
    let vintage: Int?
    let producer: String?
    let varietals: [String]?
    let region: String?
    let country: String?
    let labelImageUrl: String?
    let version: Int
    let createdAt: String?
    let updatedAt: String?

    static func == (lhs: GlobalWineReference, rhs: GlobalWineReference) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - UserWineReference

struct UserWineReference: Codable, Identifiable, Hashable {
    let id: String
    let globalReferenceId: String
    let rating: Int?
    let tastingNotes: String?
    let version: Int
    let createdAt: String?
    let updatedAt: String?

    static func == (lhs: UserWineReference, rhs: UserWineReference) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - WineInstance

struct WineInstance: Codable, Identifiable, Hashable {
    let id: String
    /// referenceId maps to the UserWineReference id (called `referenceId` in the JSON)
    let referenceId: String
    let price: Double?
    let purchaseDate: String?
    let drinkByDate: String?
    let consumed: Bool
    let consumedDate: String?
    let coravined: Bool
    let coravinedDate: String?
    let storedDate: String?
    let version: Int
    let createdAt: String?
    let updatedAt: String?

    private enum CodingKeys: String, CodingKey {
        case id, referenceId, price, purchaseDate, drinkByDate
        case consumed, consumedDate, coravined, coravinedDate
        case storedDate, version, createdAt, updatedAt
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        referenceId = try c.decode(String.self, forKey: .referenceId)
        // price can arrive as a number or a string from the server
        if let d = try? c.decodeIfPresent(Double.self, forKey: .price) {
            price = d
        } else if let s = try? c.decodeIfPresent(String.self, forKey: .price) {
            price = Double(s)
        } else {
            price = nil
        }
        purchaseDate = try c.decodeIfPresent(String.self, forKey: .purchaseDate)
        drinkByDate = try c.decodeIfPresent(String.self, forKey: .drinkByDate)
        consumed = try c.decode(Bool.self, forKey: .consumed)
        consumedDate = try c.decodeIfPresent(String.self, forKey: .consumedDate)
        coravined = try c.decode(Bool.self, forKey: .coravined)
        coravinedDate = try c.decodeIfPresent(String.self, forKey: .coravinedDate)
        storedDate = try c.decodeIfPresent(String.self, forKey: .storedDate)
        version = try c.decode(Int.self, forKey: .version)
        createdAt = try c.decodeIfPresent(String.self, forKey: .createdAt)
        updatedAt = try c.decodeIfPresent(String.self, forKey: .updatedAt)
    }

    static func == (lhs: WineInstance, rhs: WineInstance) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - Cellar

struct Cellar: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let temperature: Int?
    let capacity: Int?
    let version: Int
    let createdAt: String?
    let updatedAt: String?
    /// Each element is a [positions, isDouble] tuple decoded as ShelfConfig
    let shelves: [ShelfConfig]
    /// shelfIndex (string) → side (string) → array of optional instance IDs
    let winePositions: [String: [String: [String?]]]

    // MARK: ShelfConfig

    struct ShelfConfig: Codable, Hashable {
        let positions: Int
        let isDouble: Bool

        init(positions: Int, isDouble: Bool) {
            self.positions = positions
            self.isDouble = isDouble
        }

        /// The server serialises each shelf as a 2-element JSON array: [positions, isDouble]
        init(from decoder: Decoder) throws {
            var container = try decoder.unkeyedContainer()
            positions = try container.decode(Int.self)
            isDouble = try container.decode(Bool.self)
        }

        func encode(to encoder: Encoder) throws {
            var container = encoder.unkeyedContainer()
            try container.encode(positions)
            try container.encode(isDouble)
        }
    }

    // MARK: Codable

    private enum CodingKeys: String, CodingKey {
        case id, name, temperature, capacity, version, createdAt, updatedAt
        case shelves, winePositions
    }

    static func == (lhs: Cellar, rhs: Cellar) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - VivinoResult

struct VivinoResult: Codable, Identifiable, Hashable {
    let name: String
    let type: String?
    let vintage: Int?
    let producer: String?
    let varietals: [String]?
    let region: String?
    let country: String?
    let rating: Double?
    let labelImageUrl: String?
    let drinkByDate: String?
    let drinkByYearsOffset: Int?

    var id: String {
        name + (producer ?? "") + String(vintage ?? 0)
    }

    static func == (lhs: VivinoResult, rhs: VivinoResult) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - WineFilters

struct WineFilters {
    var selectedTypes: Set<String> = []
    var selectedVarietals: Set<String> = []
    var selectedCountries: Set<String> = []

    var showConsumed: Bool = false
    var showShelved: Bool = true
    var showUnshelved: Bool = true
    var showCoravined: Bool = false

    var searchText: String = ""
    var sortBy: SortField = .name
    var sortAscending: Bool = true

    enum SortField: String, CaseIterable, Identifiable {
        case name
        case vintage
        case stored
        case drinkBy
        case rating

        var id: String { rawValue }
    }

    mutating func reset() {
        selectedTypes = []
        selectedVarietals = []
        selectedCountries = []
        showConsumed = false
        showShelved = true
        showUnshelved = true
        showCoravined = false
        searchText = ""
        sortBy = .name
        sortAscending = true
    }
}

// MARK: - ResolvedWine

/// A joined view of a GlobalWineReference and its corresponding UserWineReference.
/// The dedup key is the userRef.id so that two users with the same globalRef have separate entries.
struct ResolvedWine: Identifiable {
    let globalRef: GlobalWineReference
    let userRef: UserWineReference

    var id: String { userRef.id }

    // Forwarding properties from globalRef
    var name: String { globalRef.name }
    var type: String { globalRef.type }
    var vintage: Int? { globalRef.vintage }
    var producer: String? { globalRef.producer }
    var varietals: [String]? { globalRef.varietals }
    var region: String? { globalRef.region }
    var country: String? { globalRef.country }
    var labelImageUrl: String? { globalRef.labelImageUrl }

    // Forwarding properties from userRef
    var rating: Int? { userRef.rating }
    var tastingNotes: String? { userRef.tastingNotes }
}

// MARK: - InstanceLocation

struct InstanceLocation {
    let cellar: Cellar
    let shelfIndex: Int
    let side: String
    let position: Int

    /// Human-readable location string, e.g. "Main Cellar, Shelf 2, Front, Pos 3"
    var displayString: String {
        let sideLabel: String
        switch side.lowercased() {
        case "front":  sideLabel = "Front"
        case "back":   sideLabel = "Back"
        case "single": sideLabel = "Single"
        default:       sideLabel = side.capitalized
        }
        return "\(cellar.name), Shelf \(shelfIndex + 1), \(sideLabel), Pos \(position + 1)"
    }
}

// MARK: - Request / Response Body Structs

struct CreateWineReferenceRequest: Codable {
    let name: String
    let type: String
    let vintage: Int?
    let producer: String?
    let varietals: [String]?
    let region: String?
    let country: String?
    let labelImageUrl: String?
}

struct CreateUserWineReferenceRequest: Codable {
    let globalReferenceId: String
    let rating: Int?
    let tastingNotes: String?
}

struct CreateWineInstanceRequest: Codable {
    let referenceId: String
    let price: Double?
    let purchaseDate: String?
    let drinkByDate: String?
}

struct UpdateUserWineReferenceRequest: Codable {
    let rating: Int?
    let tastingNotes: String?
}

struct CreateCellarRequest: Encodable {
    let name: String
    let temperature: Int?
    let shelves: [Cellar.ShelfConfig]
}
