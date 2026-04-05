import Foundation
import Combine

// MARK: - AppState

@MainActor
final class AppState: ObservableObject {

    // MARK: Published State

    @Published var globalRefs: [GlobalWineReference] = []
    @Published var userRefs: [UserWineReference] = []
    @Published var instances: [WineInstance] = []
    @Published var cellars: [Cellar] = []
    @Published var filters = WineFilters()
    @Published var isLoading = false
    @Published var loadError: String? = nil

    // MARK: Private Lookup Maps

    /// id → GlobalWineReference
    private var globalRefMap: [String: GlobalWineReference] = [:]
    /// id → UserWineReference
    private var userRefMap: [String: UserWineReference] = [:]
    /// userRefId → [WineInstance]
    private var instancesByUserRef: [String: [WineInstance]] = [:]
    /// instanceId → InstanceLocation
    private var cellarPositionMap: [String: InstanceLocation] = [:]

    // MARK: - Computed: resolvedWines

    /// Joins every UserWineReference with its corresponding GlobalWineReference.
    var resolvedWines: [ResolvedWine] {
        userRefs.compactMap { userRef in
            guard let globalRef = globalRefMap[userRef.globalReferenceId] else { return nil }
            return ResolvedWine(globalRef: globalRef, userRef: userRef)
        }
    }

    // MARK: - Computed: filteredWines

    var filteredWines: [(resolved: ResolvedWine, instances: [WineInstance])] {
        let f = filters

        // Build a normalised search string once
        let search = f.searchText
            .folding(options: [.caseInsensitive, .diacriticInsensitive], locale: .current)

        var result: [(resolved: ResolvedWine, instances: [WineInstance])] = []

        for resolved in resolvedWines {
            // ---- Attribute filters (OR within each category = all selected must match) ----
            if !f.selectedTypes.isEmpty, !f.selectedTypes.contains(resolved.type) { continue }

            if !f.selectedVarietals.isEmpty {
                let wineVarietals = Set(resolved.varietals ?? [])
                if f.selectedVarietals.isDisjoint(with: wineVarietals) { continue }
            }

            if !f.selectedCountries.isEmpty {
                guard let country = resolved.country, f.selectedCountries.contains(country) else { continue }
            }

            // ---- Search text ----
            if !search.isEmpty {
                let fields: [String?] = [
                    resolved.name,
                    resolved.producer,
                    resolved.region,
                    resolved.country,
                    resolved.type,
                ]
                let variadicsString = resolved.varietals?.joined(separator: " ")
                let allText = (fields.compactMap { $0 } + [variadicsString].compactMap { $0 })
                    .joined(separator: " ")
                    .folding(options: [.caseInsensitive, .diacriticInsensitive], locale: .current)

                if !allText.contains(search) { continue }
            }

            // ---- Status filter ----
            // Collect all instances for this userRef, then keep those that match any
            // checked status. If no status checkbox is checked, show everything.
            let allInstances = instancesByUserRef[resolved.id] ?? []

            let anyStatusChecked = f.showConsumed || f.showShelved || f.showUnshelved || f.showCoravined
            let matchingInstances: [WineInstance]

            if anyStatusChecked {
                matchingInstances = allInstances.filter { instance in
                    let isShelved  = cellarPositionMap[instance.id] != nil
                    let isConsumed = instance.consumed
                    let isCoravined = instance.coravined
                    let isUnshelved = !isConsumed && !isShelved

                    var passes = false
                    if f.showConsumed  && isConsumed  { passes = true }
                    if f.showShelved   && isShelved    { passes = true }
                    if f.showUnshelved && isUnshelved  { passes = true }
                    if f.showCoravined && isCoravined  { passes = true }
                    return passes
                }
            } else {
                matchingInstances = allInstances
            }

            guard !matchingInstances.isEmpty else { continue }

            result.append((resolved: resolved, instances: matchingInstances))
        }

        // ---- Sort ----
        result.sort { a, b in
            let ascending = f.sortAscending
            switch f.sortBy {
            case .name:
                let cmp = a.resolved.name.localizedCompare(b.resolved.name)
                return ascending ? cmp == .orderedAscending : cmp == .orderedDescending

            case .vintage:
                let av = a.resolved.vintage ?? 0
                let bv = b.resolved.vintage ?? 0
                return ascending ? av < bv : av > bv

            case .stored:
                // Use the earliest storedDate among the instances in the group
                let ad = a.instances.compactMap(\.storedDate).sorted().first ?? ""
                let bd = b.instances.compactMap(\.storedDate).sorted().first ?? ""
                return ascending ? ad < bd : ad > bd

            case .drinkBy:
                let ad = a.instances.compactMap(\.drinkByDate).sorted().first ?? ""
                let bd = b.instances.compactMap(\.drinkByDate).sorted().first ?? ""
                return ascending ? ad < bd : ad > bd

            case .rating:
                let ar = a.resolved.rating ?? 0
                let br = b.resolved.rating ?? 0
                return ascending ? ar < br : ar > br
            }
        }

        return result
    }

    // MARK: - Computed: Filter Dropdown Options

    var allTypes: [String] {
        Array(Set(globalRefs.map(\.type))).sorted()
    }

    var allVarietals: [String] {
        Array(Set(globalRefs.flatMap { $0.varietals ?? [] })).sorted()
    }

    var allCountries: [String] {
        Array(Set(globalRefs.compactMap(\.country))).sorted()
    }

    // MARK: - Load All

    func loadAll() async {
        isLoading = true
        loadError = nil

        do {
            async let fetchedGlobalRefs: [GlobalWineReference] = APIClient.shared.get(API.wineReferences)
            async let fetchedUserRefs: [UserWineReference]     = APIClient.shared.get(API.userWineReferences)
            async let fetchedInstances: [WineInstance]         = APIClient.shared.get(API.wineInstances)
            async let fetchedCellars: [Cellar]                 = APIClient.shared.get(API.cellars)

            let (gr, ur, inst, cel) = try await (fetchedGlobalRefs, fetchedUserRefs, fetchedInstances, fetchedCellars)

            globalRefs = gr
            userRefs   = ur
            instances  = inst
            cellars    = cel
            rebuildMaps()
        } catch {
            loadError = error.localizedDescription
        }

        isLoading = false
    }

    // MARK: - Refresh

    func refreshInstances() async throws {
        let fetched: [WineInstance] = try await APIClient.shared.get(API.wineInstances)
        instances = fetched
        rebuildMaps()
    }

    func refreshCellars() async throws {
        let fetched: [Cellar] = try await APIClient.shared.get(API.cellars)
        cellars = fetched
        rebuildMaps()
    }

    // MARK: - Consume / Coravin

    func consumeWine(instanceId: String) async throws {
        let updated: WineInstance = try await APIClient.shared.postEmpty(API.consume(instanceId))
        updateInstanceLocally(updated)
        // The server removes the bottle from the cellar on consume; refresh cellar state too.
        try await refreshCellars()
    }

    func coravinWine(instanceId: String) async throws {
        let updated: WineInstance = try await APIClient.shared.postEmpty(API.coravin(instanceId))
        updateInstanceLocally(updated)
    }

    // MARK: - Rating / Tasting Notes

    func updateRating(userRefId: String, rating: Int) async throws {
        let body = UpdateUserWineReferenceRequest(rating: rating, tastingNotes: userRefMap[userRefId]?.tastingNotes)
        let updated: UserWineReference = try await APIClient.shared.put(API.updateUserRef(userRefId), body: body)
        updateUserRefLocally(updated)
    }

    func updateTastingNotes(userRefId: String, notes: String) async throws {
        let body = UpdateUserWineReferenceRequest(rating: userRefMap[userRefId]?.rating, tastingNotes: notes)
        let updated: UserWineReference = try await APIClient.shared.put(API.updateUserRef(userRefId), body: body)
        updateUserRefLocally(updated)
    }

    // MARK: - Add To Collection

    /// Adds a wine to the user's collection from a Vivino search result.
    /// - Parameters:
    ///   - result: The Vivino search result to add.
    ///   - vintage: The vintage year chosen by the user.
    ///   - price: Optional purchase price.
    ///   - quantity: Number of bottles to add.
    ///   - drinkByDate: Optional ISO-8601 drink-by date string.
    func addToCollection(
        result: VivinoResult,
        vintage: Int,
        price: Double?,
        quantity: Int,
        drinkByDate: String?
    ) async throws {
        // Step 1: create (or retrieve existing) global wine reference
        let globalRefRequest = CreateWineReferenceRequest(
            name: result.name,
            type: result.type ?? "Red",
            vintage: vintage,
            producer: result.producer,
            varietals: result.varietals,
            region: result.region,
            country: result.country,
            labelImageUrl: result.labelImageUrl
        )
        let globalRef: GlobalWineReference = try await APIClient.shared.createOrConflict(
            API.wineReferences, body: globalRefRequest
        )

        // Upsert globalRef into local state
        if let idx = globalRefs.firstIndex(where: { $0.id == globalRef.id }) {
            globalRefs[idx] = globalRef
        } else {
            globalRefs.append(globalRef)
        }

        // Step 2: find or create a user wine reference for this global ref
        let existingUserRef = userRefs.first(where: { $0.globalReferenceId == globalRef.id })
        let userRef: UserWineReference
        if let existing = existingUserRef {
            userRef = existing
        } else {
            let userRefRequest = CreateUserWineReferenceRequest(
                globalReferenceId: globalRef.id,
                rating: nil,
                tastingNotes: nil
            )
            let created: UserWineReference = try await APIClient.shared.post(
                API.userWineReferences, body: userRefRequest
            )
            userRefs.append(created)
            userRef = created
        }

        // Step 3: create `quantity` wine instances
        let resolvedDrinkBy = drinkByDate ?? result.drinkByDate
        for _ in 0..<quantity {
            let instanceRequest = CreateWineInstanceRequest(
                referenceId: userRef.id,
                price: price,
                purchaseDate: nil,
                drinkByDate: resolvedDrinkBy
            )
            let newInstance: WineInstance = try await APIClient.shared.post(
                API.wineInstances, body: instanceRequest
            )
            instances.append(newInstance)
        }

        // Step 4: refresh instances to get server-canonical state
        try await refreshInstances()
    }

    // MARK: - Lookup Helpers

    func locationForInstance(_ id: String) -> InstanceLocation? {
        cellarPositionMap[id]
    }

    func resolveWine(for instance: WineInstance) -> ResolvedWine? {
        guard let userRef = userRefMap[instance.referenceId],
              let globalRef = globalRefMap[userRef.globalReferenceId] else { return nil }
        return ResolvedWine(globalRef: globalRef, userRef: userRef)
    }

    /// All non-consumed bottles sharing the same userRefId but with a different instanceId.
    func otherBottles(for instance: WineInstance) -> [WineInstance] {
        (instancesByUserRef[instance.referenceId] ?? [])
            .filter { $0.id != instance.id && !$0.consumed }
    }

    /// All non-consumed bottles for wines with the same name + producer as `instance`
    /// but a different vintage. Results grouped by vintage.
    func otherVintages(for instance: WineInstance) -> [(vintage: Int?, instances: [WineInstance])] {
        guard let resolved = resolveWine(for: instance) else { return [] }
        let targetName     = resolved.name
        let targetProducer = resolved.producer
        let targetVintage  = resolved.vintage

        // Collect all userRefs whose globalRef matches name+producer but differs in vintage
        var grouped: [Int?: [WineInstance]] = [:]
        for userRef in userRefs {
            guard let globalRef = globalRefMap[userRef.globalReferenceId] else { continue }
            guard globalRef.name == targetName,
                  globalRef.producer == targetProducer,
                  globalRef.vintage != targetVintage else { continue }

            let bottlesForRef = (instancesByUserRef[userRef.id] ?? []).filter { !$0.consumed }
            guard !bottlesForRef.isEmpty else { continue }

            let v = globalRef.vintage
            grouped[v, default: []].append(contentsOf: bottlesForRef)
        }

        return grouped
            .map { (vintage: $0.key, instances: $0.value) }
            .sorted { a, b in (a.vintage ?? 0) < (b.vintage ?? 0) }
    }

    // MARK: - Private: rebuildMaps

    private func rebuildMaps() {
        // Rebuild globalRefMap
        globalRefMap = Dictionary(uniqueKeysWithValues: globalRefs.map { ($0.id, $0) })

        // Rebuild userRefMap
        userRefMap = Dictionary(uniqueKeysWithValues: userRefs.map { ($0.id, $0) })

        // Rebuild instancesByUserRef
        var byRef: [String: [WineInstance]] = [:]
        for instance in instances {
            byRef[instance.referenceId, default: []].append(instance)
        }
        instancesByUserRef = byRef

        // Rebuild cellarPositionMap by walking all cellars → shelves → winePositions
        var positionMap: [String: InstanceLocation] = [:]
        for cellar in cellars {
            for (shelfIndexStr, sidesDict) in cellar.winePositions {
                guard let shelfIndex = Int(shelfIndexStr) else { continue }
                for (side, positions) in sidesDict {
                    for (positionIndex, instanceIdOpt) in positions.enumerated() {
                        guard let instanceId = instanceIdOpt else { continue }
                        let location = InstanceLocation(
                            cellar: cellar,
                            shelfIndex: shelfIndex,
                            side: side,
                            position: positionIndex
                        )
                        positionMap[instanceId] = location
                    }
                }
            }
        }
        cellarPositionMap = positionMap
    }

    // MARK: - Private: Local Update Helpers

    private func updateInstanceLocally(_ updated: WineInstance) {
        if let idx = instances.firstIndex(where: { $0.id == updated.id }) {
            instances[idx] = updated
        }
        rebuildMaps()
    }

    private func updateUserRefLocally(_ updated: UserWineReference) {
        if let idx = userRefs.firstIndex(where: { $0.id == updated.id }) {
            userRefs[idx] = updated
        }
        userRefMap[updated.id] = updated
    }
}
