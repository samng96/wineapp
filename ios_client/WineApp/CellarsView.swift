import SwiftUI

// MARK: - CellarsView

struct CellarsView: View {
    @EnvironmentObject var appState: AppState
    @State private var showAddCellar = false
    @State private var refreshError: Error? = nil

    // MARK: Helpers

    private func cellarInstanceIds(_ cellar: Cellar) -> Set<String> {
        var ids = Set<String>()
        for (_, sides) in cellar.winePositions {
            for (_, positions) in sides {
                for id in positions.compactMap({ $0 }) { ids.insert(id) }
            }
        }
        return ids
    }

    private func labelURLs(for cellar: Cellar) -> [URL] {
        let ids = cellarInstanceIds(cellar)
        var seen = Set<String>()
        var urls: [URL] = []
        for inst in appState.instances where ids.contains(inst.id) {
            if let resolved = appState.resolveWine(for: inst),
               let raw = resolved.labelImageUrl, !seen.contains(raw),
               let url = APIClient.shared.resolveImageURL(raw) {
                seen.insert(raw)
                urls.append(url)
                if urls.count >= 10 { break }
            }
        }
        return urls
    }

    private func breakdown(for cellar: Cellar) -> [(type: String, count: Int)] {
        let ids = cellarInstanceIds(cellar)
        var counts: [String: Int] = [:]
        for inst in appState.instances where ids.contains(inst.id) {
            if let resolved = appState.resolveWine(for: inst) {
                counts[resolved.type, default: 0] += 1
            }
        }
        return counts.map { ($0.key, $0.value) }.sorted { $0.type < $1.type }
    }

    private var unshelvedInstances: [WineInstance] {
        appState.instances.filter { !$0.consumed && appState.locationForInstance($0.id) == nil }
    }

    // MARK: Body

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 16) {
                    if !unshelvedInstances.isEmpty {
                        UnshelvedCard(instances: unshelvedInstances)
                    }

                    ForEach(appState.cellars) { cellar in
                        NavigationLink(destination: CellarDetailView(cellar: cellar)) {
                            CellarCard(
                                cellar: cellar,
                                labelURLs: labelURLs(for: cellar),
                                breakdown: breakdown(for: cellar)
                            )
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal)
                .padding(.top, 8)
                .padding(.bottom, 16)
            }
            .refreshable {
                do {
                    try await appState.refreshCellars()
                } catch {
                    refreshError = error
                }
            }
            .navigationTitle("My Cellars")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showAddCellar = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .overlay {
                if appState.isLoading && appState.cellars.isEmpty {
                    LoadingOverlay()
                } else if !appState.isLoading && appState.cellars.isEmpty && appState.loadError == nil {
                    ContentUnavailableView(
                        "No Cellars",
                        systemImage: "archivebox",
                        description: Text("Add a cellar to get started.")
                    )
                }
            }
            .errorAlert(error: $refreshError)
            .sheet(isPresented: $showAddCellar) {
                AddCellarSheet()
            }
        }
    }
}

// MARK: - CellarCard

private struct CellarCard: View {
    @EnvironmentObject var appState: AppState

    let cellar: Cellar
    let labelURLs: [URL]
    let breakdown: [(type: String, count: Int)]

    @State private var showDeleteConfirm = false
    @State private var showEditSheet = false
    @State private var deleteError: Error? = nil

    private var usedCount: Int {
        var ids = Set<String>()
        for (_, sides) in cellar.winePositions {
            for (_, positions) in sides {
                for id in positions.compactMap({ $0 }) { ids.insert(id) }
            }
        }
        return ids.count
    }

    private var totalCapacity: Int {
        cellar.capacity ?? cellar.shelves.reduce(0) { $0 + $1.positions }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Preview row
            HStack(alignment: .top, spacing: 12) {
                LabelCarousel(urls: labelURLs)
                    .frame(width: 110, height: 130)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                CellarInfoColumn(
                    cellar: cellar,
                    breakdown: breakdown,
                    usedCount: usedCount,
                    totalCapacity: totalCapacity
                )
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(12)

            Divider()

            CellarNameBar(
                name: cellar.name,
                onEdit: { showEditSheet = true },
                onDelete: { showDeleteConfirm = true }
            )
        }
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.08), radius: 4, x: 0, y: 2)
        .confirmationDialog(
            "Delete \"\(cellar.name)\"?",
            isPresented: $showDeleteConfirm,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                Task { await deleteCellar() }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Are you sure you want to delete this cellar? This cannot be undone.")
        }
        .sheet(isPresented: $showEditSheet) {
            // TODO: Implement full edit pre-filled with cellar data
            AddCellarSheet()
        }
        .errorAlert(error: $deleteError)
    }

    private func deleteCellar() async {
        do {
            try await APIClient.shared.delete(API.deleteCellar(cellar.id))
            try await appState.refreshCellars()
        } catch {
            deleteError = error
        }
    }
}

// MARK: - LabelCarousel

private struct LabelCarousel: View {
    let urls: [URL]

    @State private var currentIndex: Int = 0
    @State private var timerTask: Task<Void, Never>? = nil

    var body: some View {
        ZStack {
            if urls.isEmpty {
                ZStack {
                    Color(.systemGray5)
                    Image(systemName: "wineglass")
                        .font(.system(size: 36))
                        .foregroundColor(.secondary)
                }
            } else {
                AsyncImage(url: urls[currentIndex]) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    case .failure, .empty:
                        ZStack {
                            Color(.systemGray5)
                            Image(systemName: "wineglass")
                                .font(.system(size: 36))
                                .foregroundColor(.secondary)
                        }
                    @unknown default:
                        ZStack {
                            Color(.systemGray5)
                            Image(systemName: "wineglass")
                                .font(.system(size: 36))
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .id(currentIndex)
                .transition(.opacity.animation(.easeInOut(duration: 0.5)))
            }
        }
        .onAppear { startTimer() }
        .onDisappear { timerTask?.cancel(); timerTask = nil }
    }

    private func startTimer() {
        guard urls.count > 1 else { return }
        timerTask?.cancel()
        timerTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 3_000_000_000)
                if !Task.isCancelled {
                    withAnimation {
                        currentIndex = (currentIndex + 1) % urls.count
                    }
                }
            }
        }
    }
}

// MARK: - CellarInfoColumn

private struct CellarInfoColumn: View {
    @EnvironmentObject var appState: AppState

    let cellar: Cellar
    let breakdown: [(type: String, count: Int)]
    let usedCount: Int
    let totalCapacity: Int

    private var contentsText: String {
        if breakdown.isEmpty { return "Empty" }
        return breakdown.map { "\($0.count) \($0.type)" }.joined(separator: " · ")
    }

    private var temperatureText: String {
        if let t = cellar.temperature { return "\(t)°F" }
        return "—"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Group {
                HStack(spacing: 0) {
                    Text("Contents: ").font(.caption).bold()
                    Text(contentsText).font(.caption)
                }
                HStack(spacing: 0) {
                    Text("Capacity: ").font(.caption).bold()
                    Text("\(usedCount) / \(totalCapacity)").font(.caption)
                }
                HStack(spacing: 0) {
                    Text("Temperature: ").font(.caption).bold()
                    Text(temperatureText).font(.caption)
                }
            }
            .foregroundColor(.primary)

            Spacer(minLength: 6)

            BottleGridPreview(cellar: cellar)
        }
    }
}

// MARK: - BottleGridPreview

private struct BottleGridPreview: View {
    @EnvironmentObject var appState: AppState
    let cellar: Cellar

    /// Build a map of instanceId → wine type for coloring circles
    private var instanceTypeMap: [String: String] {
        var map: [String: String] = [:]
        for (_, sides) in cellar.winePositions {
            for (_, positions) in sides {
                for idOpt in positions {
                    guard let id = idOpt else { continue }
                    if let inst = appState.instances.first(where: { $0.id == id }),
                       let resolved = appState.resolveWine(for: inst) {
                        map[id] = resolved.type
                    }
                }
            }
        }
        return map
    }

    var body: some View {
        let typeMap = instanceTypeMap
        VStack(spacing: 2) {
            ForEach(Array(cellar.shelves.enumerated()), id: \.offset) { idx, shelf in
                let shelfKey = String(idx)
                let shelfData = cellar.winePositions[shelfKey] ?? [:]
                ShelfCircleRow(
                    shelf: shelf,
                    shelfData: shelfData,
                    instanceTypeMap: typeMap
                )
            }
        }
    }
}

// MARK: - ShelfCircleRow

private struct ShelfCircleRow: View {
    let shelf: Cellar.ShelfConfig
    let shelfData: [String: [String?]]
    let instanceTypeMap: [String: String]

    private let circleDiameter: CGFloat = 6
    private let circleGap: CGFloat = 2
    private let maxVisible = 12

    private func circleColor(for idOpt: String?) -> Color {
        guard let id = idOpt,
              let type = instanceTypeMap[id] else {
            return Color(.systemGray4)
        }
        switch type {
        case "Red":       return Color(red: 0.6, green: 0, blue: 0.1)
        case "White":     return Color(red: 0.9, green: 0.7, blue: 0.1)
        case "Rosé":      return .pink
        case "Sparkling": return .blue
        default:          return .purple
        }
    }

    private func circleRow(positions: [String?]) -> some View {
        let visible = Array(positions.prefix(maxVisible))
        let hasMore = positions.count > maxVisible
        return HStack(spacing: circleGap) {
            ForEach(Array(visible.enumerated()), id: \.offset) { _, idOpt in
                Circle()
                    .fill(circleColor(for: idOpt))
                    .frame(width: circleDiameter, height: circleDiameter)
            }
            if hasMore {
                Text("…")
                    .font(.system(size: 8))
                    .foregroundColor(.secondary)
            }
        }
    }

    var body: some View {
        if shelf.isDouble {
            let backPositions = shelfData["back"] ?? []
            let frontPositions = shelfData["front"] ?? []
            VStack(spacing: 1) {
                circleRow(positions: backPositions)
                circleRow(positions: frontPositions)
                    .offset(x: (circleDiameter + circleGap) / 2)
            }
        } else {
            let singlePositions = shelfData["single"] ?? []
            circleRow(positions: singlePositions)
        }
    }
}

// MARK: - CellarNameBar

private struct CellarNameBar: View {
    let name: String
    let onEdit: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack {
            Text(name.uppercased())
                .font(.caption)
                .fontWeight(.bold)
                .foregroundColor(.primary)
                .lineLimit(1)
                .truncationMode(.tail)

            Spacer()

            Menu {
                Button(action: onEdit) {
                    Label("Edit", systemImage: "pencil")
                }
                Button(role: .destructive, action: onDelete) {
                    Label("Delete", systemImage: "trash")
                }
            } label: {
                Image(systemName: "ellipsis")
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .contentShape(Rectangle())
            }
            .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
    }
}

// MARK: - UnshelvedCard

private struct UnshelvedCard: View {
    @EnvironmentObject var appState: AppState
    let instances: [WineInstance]

    private var labelURLs: [URL] {
        var seen = Set<String>()
        var urls: [URL] = []
        for inst in instances {
            if let resolved = appState.resolveWine(for: inst),
               let raw = resolved.labelImageUrl, !seen.contains(raw),
               let url = APIClient.shared.resolveImageURL(raw) {
                seen.insert(raw)
                urls.append(url)
                if urls.count >= 10 { break }
            }
        }
        return urls
    }

    private var breakdown: [(type: String, count: Int)] {
        var counts: [String: Int] = [:]
        for inst in instances {
            if let resolved = appState.resolveWine(for: inst) {
                counts[resolved.type, default: 0] += 1
            }
        }
        return counts.map { ($0.key, $0.value) }.sorted { $0.type < $1.type }
    }

    private var lastAddedText: String? {
        guard let latest = instances.sorted(by: {
            ($0.createdAt ?? "") > ($1.createdAt ?? "")
        }).first,
              let resolved = appState.resolveWine(for: latest) else {
            return nil
        }
        let vintageStr = resolved.vintage.map { " \($0)" } ?? ""
        return "\(resolved.name)\(vintageStr)"
    }

    private var contentsText: String {
        if breakdown.isEmpty { return "Empty" }
        return breakdown.map { "\($0.count) \($0.type)" }.joined(separator: " · ")
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 12) {
                LabelCarousel(urls: labelURLs)
                    .frame(width: 110, height: 130)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 0) {
                        Text("Contents: ").font(.caption).bold()
                        Text(contentsText).font(.caption)
                    }

                    if let lastAdded = lastAddedText {
                        HStack(spacing: 0) {
                            Text("Last added: ").font(.caption).bold()
                            Text(lastAdded).font(.caption)
                        }
                    }

                    Text("Store these wines in a cellar to track their location.")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .padding(.top, 2)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(12)

            Divider()

            HStack {
                Text("UNSHELVED WINES")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.08), radius: 4, x: 0, y: 2)
    }
}

// MARK: - AddCellarSheet

private struct ShelfDraft: Identifiable {
    let id = UUID()
    var positions: Int = 6
    var isDouble: Bool = false
}

private struct AddCellarSheet: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.dismiss) private var dismiss

    @State private var name: String = ""
    @State private var temperatureText: String = ""
    @State private var shelves: [ShelfDraft] = []
    @State private var isSaving = false
    @State private var saveError: String? = nil

    private var trimmedName: String { name.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var canSave: Bool { !trimmedName.isEmpty && !isSaving }

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text("Cellar Info")) {
                    TextField("Name (required)", text: $name)
                    TextField("Temperature (°F, optional)", text: $temperatureText)
                        .keyboardType(.numberPad)
                }

                Section(header: HStack {
                    Text("Shelves")
                    Spacer()
                    Button(action: { shelves.append(ShelfDraft()) }) {
                        Image(systemName: "plus")
                    }
                }) {
                    ForEach($shelves) { $shelf in
                        VStack(alignment: .leading, spacing: 6) {
                            let idx = shelves.firstIndex(where: { $0.id == shelf.id }).map { $0 + 1 } ?? 0
                            Text("Shelf \(idx): \(shelf.positions) positions, \(shelf.isDouble ? "Double" : "Single")")
                                .font(.subheadline)
                            Stepper("Positions: \(shelf.positions)", value: $shelf.positions, in: 1...24)
                            Toggle("Double-sided", isOn: $shelf.isDouble)
                        }
                        .padding(.vertical, 4)
                    }
                    .onDelete { indexSet in
                        shelves.remove(atOffsets: indexSet)
                    }
                }

                if let error = saveError {
                    Section {
                        Text(error)
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Add Cellar")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { Task { await save() } }
                        .disabled(!canSave)
                }
            }
        }
    }

    private func save() async {
        isSaving = true
        saveError = nil
        let temperature = Int(temperatureText.trimmingCharacters(in: .whitespacesAndNewlines))
        let shelfConfigs = shelves.map { Cellar.ShelfConfig(positions: $0.positions, isDouble: $0.isDouble) }
        let body = CreateCellarRequest(name: trimmedName, temperature: temperature, shelves: shelfConfigs)
        do {
            let _: Cellar = try await APIClient.shared.post(API.cellars, body: body)
            try await appState.refreshCellars()
            dismiss()
        } catch {
            saveError = error.localizedDescription
        }
        isSaving = false
    }
}
