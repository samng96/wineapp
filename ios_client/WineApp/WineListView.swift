import SwiftUI

// MARK: - WineListView

struct WineListView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedWine: ResolvedWine? = nil
    @State private var selectedInstances: [WineInstance] = []

    var body: some View {
        NavigationStack {
            ZStack {
                VStack(spacing: 0) {
                    FilterPillsRow()
                        .padding(.horizontal)
                        .padding(.vertical, 8)
                        .background(Color(.systemGroupedBackground))

                    List {
                        ForEach(appState.filteredWines, id: \.resolved.id) { item in
                            WineRowView(resolved: item.resolved, instances: item.instances)
                                .contentShape(Rectangle())
                                .onTapGesture {
                                    selectedWine = item.resolved
                                    selectedInstances = item.instances
                                }
                                .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                        }
                    }
                    .listStyle(.insetGrouped)
                    .searchable(text: $appState.filters.searchText)
                    .refreshable {
                        await appState.loadAll()
                    }
                }

                if appState.isLoading && appState.filteredWines.isEmpty {
                    LoadingOverlay()
                }
            }
            .navigationTitle("My Wines")
            .sheet(item: $selectedWine) { wine in
                WineDetailSheet(resolved: wine, instances: selectedInstances)
            }
        }
    }
}

// MARK: - FilterPillsRow

private struct FilterPillsRow: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                TypeFilterMenu()
                StatusPill(label: "Shelved",    isOn: $appState.filters.showShelved)
                StatusPill(label: "Unshelved",  isOn: $appState.filters.showUnshelved)
                StatusPill(label: "Consumed",   isOn: $appState.filters.showConsumed)
                StatusPill(label: "Coravined",  isOn: $appState.filters.showCoravined)
                SortPickerPill()
            }
        }
    }
}

// MARK: TypeFilterMenu

private struct TypeFilterMenu: View {
    @EnvironmentObject var appState: AppState

    private var label: String {
        if appState.filters.selectedTypes.isEmpty {
            return "All Types"
        }
        return appState.filters.selectedTypes.sorted().joined(separator: ", ")
    }

    var body: some View {
        Menu {
            Button("All Types") {
                appState.filters.selectedTypes = []
            }
            Divider()
            ForEach(appState.allTypes, id: \.self) { type in
                Button {
                    if appState.filters.selectedTypes.contains(type) {
                        appState.filters.selectedTypes.remove(type)
                    } else {
                        appState.filters.selectedTypes.insert(type)
                    }
                } label: {
                    HStack {
                        Text(type)
                        if appState.filters.selectedTypes.contains(type) {
                            Image(systemName: "checkmark")
                        }
                    }
                }
            }
        } label: {
            PillLabel(
                text: label,
                isActive: !appState.filters.selectedTypes.isEmpty,
                systemImage: "line.3.horizontal.decrease.circle"
            )
        }
    }
}

// MARK: StatusPill

private struct StatusPill: View {
    let label: String
    @Binding var isOn: Bool

    var body: some View {
        Button {
            isOn.toggle()
        } label: {
            PillLabel(text: label, isActive: isOn, systemImage: nil)
        }
    }
}

// MARK: SortPickerPill

private struct SortPickerPill: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        Menu {
            ForEach(WineFilters.SortField.allCases) { field in
                Button {
                    if appState.filters.sortBy == field {
                        appState.filters.sortAscending.toggle()
                    } else {
                        appState.filters.sortBy = field
                        appState.filters.sortAscending = true
                    }
                } label: {
                    HStack {
                        Text(field.displayName)
                        if appState.filters.sortBy == field {
                            Image(systemName: appState.filters.sortAscending ? "chevron.up" : "chevron.down")
                        }
                    }
                }
            }
        } label: {
            PillLabel(
                text: "Sort: \(appState.filters.sortBy.displayName)",
                isActive: true,
                systemImage: "arrow.up.arrow.down"
            )
        }
    }
}

// MARK: PillLabel

private struct PillLabel: View {
    let text: String
    let isActive: Bool
    let systemImage: String?

    var body: some View {
        HStack(spacing: 4) {
            if let systemImage = systemImage {
                Image(systemName: systemImage)
                    .font(.caption)
            }
            Text(text)
                .font(.caption)
                .lineLimit(1)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(isActive ? Color.accentColor.opacity(0.15) : Color(.systemGray5))
        .foregroundColor(isActive ? .accentColor : .secondary)
        .clipShape(Capsule())
    }
}

// MARK: - WineRowView

struct WineRowView: View {
    let resolved: ResolvedWine
    let instances: [WineInstance]

    private var earliestDrinkBy: String? {
        instances
            .compactMap { $0.drinkByDate }
            .sorted()
            .first
            .flatMap { drinkByYear(from: $0) }
    }

    private var bottleCount: Int {
        instances.filter { !$0.consumed }.count
    }

    var body: some View {
        HStack(spacing: 12) {
            AsyncWineImage(
                url: APIClient.shared.resolveImageURL(resolved.labelImageUrl),
                width: 50,
                height: 70
            )

            VStack(alignment: .leading, spacing: 4) {
                Text(resolved.name)
                    .font(.headline)
                    .lineLimit(2)

                HStack(spacing: 4) {
                    if let producer = resolved.producer {
                        Text(producer)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    if let vintage = resolved.vintage {
                        Text("·")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(String(vintage))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                HStack(spacing: 6) {
                    TypeBadge(type: resolved.type)
                    Text("\(bottleCount) bottle\(bottleCount == 1 ? "" : "s")")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 6) {
                if let year = earliestDrinkBy {
                    VStack(alignment: .trailing, spacing: 1) {
                        Text("Drink by")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        Text(year)
                            .font(.caption)
                            .fontWeight(.medium)
                    }
                }

                if let rating = resolved.rating, rating > 0 {
                    StarRatingView(rating: .constant(rating), displayOnly: true)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - TypeBadge helper

struct TypeBadge: View {
    let type: String

    var body: some View {
        Text(type)
            .font(.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(WineTypeColor(type: type).opacity(0.15))
            .foregroundColor(WineTypeColor(type: type))
            .clipShape(Capsule())
    }
}

// MARK: - SortField display name

extension WineFilters.SortField {
    var displayName: String {
        switch self {
        case .name:     return "Name"
        case .vintage:  return "Vintage"
        case .stored:   return "Stored"
        case .drinkBy:  return "Drink By"
        case .rating:   return "Rating"
        }
    }
}
