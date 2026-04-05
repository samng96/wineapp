import SwiftUI

// MARK: - WineDetailSheet

struct WineDetailSheet: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.dismiss) private var dismiss

    let resolved: ResolvedWine
    let instances: [WineInstance]

    @State private var rating: Int
    @State private var tastingNotes: String
    @State private var isEditingNotes = false
    @State private var showingConsumed = false
    @State private var actionError: Error? = nil
    @State private var isWorking = false
    @State private var selectedOtherVintage: ResolvedWine? = nil
    @State private var selectedOtherInstances: [WineInstance] = []

    init(resolved: ResolvedWine, instances: [WineInstance]) {
        self.resolved = resolved
        self.instances = instances
        _rating = State(initialValue: resolved.rating ?? 0)
        _tastingNotes = State(initialValue: resolved.tastingNotes ?? "")
    }

    private var activeInstances: [WineInstance] {
        if showingConsumed {
            return instances
        }
        return instances.filter { !$0.consumed }
    }

    private var otherVintages: [(vintage: Int?, instances: [WineInstance])] {
        guard let first = instances.first else { return [] }
        return appState.otherVintages(for: first)
    }

    var body: some View {
        NavigationStack {
            ZStack {
                List {
                    // MARK: Header Section
                    Section {
                        VStack(spacing: 12) {
                            AsyncWineImage(
                                url: APIClient.shared.resolveImageURL(resolved.labelImageUrl),
                                width: 120,
                                height: 160
                            )

                            Text(resolved.name)
                                .font(.title2)
                                .fontWeight(.bold)
                                .multilineTextAlignment(.center)

                            if let producer = resolved.producer {
                                Text(producer)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }

                            HStack(spacing: 8) {
                                if let vintage = resolved.vintage {
                                    Text(String(vintage))
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }
                                TypeBadge(type: resolved.type)
                            }

                            StarRatingView(
                                rating: Binding(
                                    get: { rating },
                                    set: { newVal in
                                        rating = newVal
                                        Task {
                                            do {
                                                try await appState.updateRating(
                                                    userRefId: resolved.id,
                                                    rating: newVal
                                                )
                                            } catch {
                                                actionError = error
                                            }
                                        }
                                    }
                                ),
                                displayOnly: false
                            )

                            if let country = resolved.country {
                                HStack(spacing: 4) {
                                    Image(systemName: "mappin.circle")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Text([resolved.region, country]
                                        .compactMap { $0 }
                                        .joined(separator: ", "))
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .listRowBackground(Color.clear)
                        .listRowInsets(EdgeInsets())
                    }

                    // MARK: Tasting Notes Section
                    Section("Tasting Notes") {
                        VStack(alignment: .leading, spacing: 6) {
                            if isEditingNotes {
                                TextEditor(text: $tastingNotes)
                                    .frame(minHeight: 100)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 6)
                                            .stroke(Color.accentColor.opacity(0.4), lineWidth: 1)
                                    )

                                Button("Save") {
                                    isEditingNotes = false
                                    Task {
                                        do {
                                            try await appState.updateTastingNotes(
                                                userRefId: resolved.id,
                                                notes: tastingNotes
                                            )
                                        } catch {
                                            actionError = error
                                        }
                                    }
                                }
                                .buttonStyle(.borderedProminent)
                                .controlSize(.small)
                            } else {
                                Text(tastingNotes.isEmpty ? "Tap to add tasting notes…" : tastingNotes)
                                    .foregroundColor(tastingNotes.isEmpty ? .secondary : .primary)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .contentShape(Rectangle())
                                    .onTapGesture {
                                        isEditingNotes = true
                                    }
                            }
                        }
                    }

                    // MARK: Bottles Section
                    Section {
                        Toggle("Show consumed", isOn: $showingConsumed)
                            .font(.subheadline)
                            .toggleStyle(.switch)
                    }

                    if !activeInstances.isEmpty {
                        Section("Bottles") {
                            ForEach(activeInstances) { instance in
                                BottleRow(instance: instance, actionError: $actionError)
                            }
                        }
                    }

                    // MARK: Other Vintages Section
                    if !otherVintages.isEmpty {
                        Section("Other Vintages") {
                            ForEach(otherVintages, id: \.vintage) { group in
                                OtherVintageRow(
                                    vintage: group.vintage,
                                    instances: group.instances,
                                    onTap: { resolved, instances in
                                        selectedOtherVintage = resolved
                                        selectedOtherInstances = instances
                                    }
                                )
                            }
                        }
                    }
                }
                .listStyle(.insetGrouped)

                if isWorking {
                    LoadingOverlay()
                }
            }
            .navigationTitle("Wine Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
            .errorAlert(error: $actionError)
            .sheet(item: $selectedOtherVintage) { wine in
                WineDetailSheet(resolved: wine, instances: selectedOtherInstances)
            }
        }
    }
}

// MARK: - BottleRow

private struct BottleRow: View {
    @EnvironmentObject var appState: AppState
    let instance: WineInstance
    @Binding var actionError: Error?

    @State private var isWorking = false
    @State private var showConsumeConfirm = false

    private var location: InstanceLocation? {
        appState.locationForInstance(instance.id)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Location
            HStack {
                Image(systemName: location != nil ? "archivebox" : "tray")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(location?.displayString ?? "Unshelved")
                    .font(.subheadline)
                    .foregroundColor(location != nil ? .primary : .secondary)
            }

            // Price + Drink By
            HStack(spacing: 16) {
                if let price = instance.price {
                    Label(String(format: "$%.2f", price), systemImage: "dollarsign")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                if let year = drinkByYear(from: instance.drinkByDate) {
                    Label("Drink by \(year)", systemImage: "calendar")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            if instance.consumed {
                Text("Consumed")
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color.red.opacity(0.1))
                    .clipShape(Capsule())
            } else {
                // Actions row
                HStack(spacing: 12) {
                    // Coravin toggle
                    Button {
                        guard !isWorking else { return }
                        Task {
                            isWorking = true
                            do {
                                try await appState.coravinWine(instanceId: instance.id)
                            } catch {
                                actionError = error
                            }
                            isWorking = false
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: instance.coravined ? "drop.fill" : "drop")
                                .font(.caption)
                            Text(instance.coravined ? "Coravined" : "Coravin")
                                .font(.caption)
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(instance.coravined ? Color.purple.opacity(0.15) : Color(.systemGray5))
                        .foregroundColor(instance.coravined ? .purple : .secondary)
                        .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                    .disabled(isWorking)

                    Spacer()

                    // Consume button
                    Button(role: .destructive) {
                        showConsumeConfirm = true
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "trash")
                                .font(.caption)
                            Text("Consume")
                                .font(.caption)
                        }
                    }
                    .disabled(isWorking)
                    .confirmationDialog(
                        "Mark this bottle as consumed?",
                        isPresented: $showConsumeConfirm,
                        titleVisibility: .visible
                    ) {
                        Button("Consume", role: .destructive) {
                            Task {
                                isWorking = true
                                do {
                                    try await appState.consumeWine(instanceId: instance.id)
                                } catch {
                                    actionError = error
                                }
                                isWorking = false
                            }
                        }
                        Button("Cancel", role: .cancel) {}
                    }
                }
            }
        }
        .overlay {
            if isWorking {
                Color(.systemBackground).opacity(0.5)
                ProgressView()
            }
        }
    }
}

// MARK: - OtherVintageRow

private struct OtherVintageRow: View {
    @EnvironmentObject var appState: AppState
    let vintage: Int?
    let instances: [WineInstance]
    let onTap: (ResolvedWine, [WineInstance]) -> Void

    private var resolved: ResolvedWine? {
        instances.first.flatMap { appState.resolveWine(for: $0) }
    }

    var body: some View {
        Button {
            if let resolved = resolved {
                onTap(resolved, instances)
            }
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(vintage.map(String.init) ?? "NV")
                        .font(.headline)
                    Text("\(instances.count) bottle\(instances.count == 1 ? "" : "s")")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .buttonStyle(.plain)
    }
}
