import SwiftUI

// MARK: - CellarDetailView

struct CellarDetailView: View {
    @EnvironmentObject var appState: AppState
    let cellar: Cellar

    var body: some View {
        List {
            ForEach(Array(cellar.shelves.enumerated()), id: \.offset) { index, shelf in
                ShelfRow(
                    cellar: cellar,
                    shelfIndex: index,
                    shelf: shelf,
                    occupiedCount: bottlesOnShelf(shelfIndex: index)
                )
            }
        }
        .listStyle(.insetGrouped)
        .navigationTitle(cellar.name)
        .navigationBarTitleDisplayMode(.large)
        .overlay {
            if cellar.shelves.isEmpty {
                ContentUnavailableView(
                    "No Shelves",
                    systemImage: "tray.2",
                    description: Text("This cellar has no shelves configured.")
                )
            }
        }
    }

    // MARK: Count bottles placed on a given shelf

    private func bottlesOnShelf(shelfIndex: Int) -> Int {
        appState.instances.filter { instance in
            guard let location = appState.locationForInstance(instance.id) else { return false }
            return location.cellar.id == cellar.id && location.shelfIndex == shelfIndex
        }.count
    }
}

// MARK: - ShelfRow

private struct ShelfRow: View {
    let cellar: Cellar
    let shelfIndex: Int
    let shelf: Cellar.ShelfConfig
    let occupiedCount: Int

    private var totalPositions: Int {
        shelf.isDouble ? shelf.positions * 2 : shelf.positions
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Shelf \(shelfIndex + 1)")
                    .font(.headline)

                if shelf.isDouble {
                    Text("(double)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color(.systemGray5))
                        .clipShape(Capsule())
                }
            }

            HStack(spacing: 4) {
                // Progress bar
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 3)
                            .fill(Color(.systemGray5))

                        RoundedRectangle(cornerRadius: 3)
                            .fill(occupancyColor)
                            .frame(width: totalPositions > 0
                                ? geo.size.width * CGFloat(occupiedCount) / CGFloat(totalPositions)
                                : 0
                            )
                    }
                }
                .frame(height: 6)

                Text("\(occupiedCount) / \(totalPositions)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(minWidth: 44, alignment: .trailing)
            }
        }
        .padding(.vertical, 6)
    }

    private var occupancyColor: Color {
        guard totalPositions > 0 else { return .gray }
        let ratio = Double(occupiedCount) / Double(totalPositions)
        if ratio >= 0.9 { return .red }
        if ratio >= 0.7 { return .orange }
        return .green
    }
}
