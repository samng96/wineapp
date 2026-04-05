import SwiftUI

// MARK: - CellarsView

struct CellarsView: View {
    @EnvironmentObject var appState: AppState
    @State private var refreshError: Error? = nil

    var body: some View {
        NavigationStack {
            List(appState.cellars) { cellar in
                NavigationLink(destination: CellarDetailView(cellar: cellar)) {
                    CellarRow(cellar: cellar)
                }
            }
            .listStyle(.insetGrouped)
            .refreshable {
                do {
                    try await appState.refreshCellars()
                } catch {
                    refreshError = error
                }
            }
            .navigationTitle("My Cellars")
            .overlay {
                if appState.isLoading && appState.cellars.isEmpty {
                    LoadingOverlay()
                } else if !appState.isLoading && appState.cellars.isEmpty {
                    ContentUnavailableView(
                        "No Cellars",
                        systemImage: "archivebox",
                        description: Text("Add a cellar to get started.")
                    )
                }
            }
            .errorAlert(error: $refreshError)
        }
    }
}

// MARK: - CellarRow

private struct CellarRow: View {
    let cellar: Cellar

    private var shelfCount: Int { cellar.shelves.count }
    private var capacity: Int { cellar.capacity ?? cellar.shelves.reduce(0) { $0 + $1.positions } }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(cellar.name)
                .font(.headline)

            HStack(spacing: 4) {
                Text("\(shelfCount) \(shelfCount == 1 ? "shelf" : "shelves")")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                Text("·")
                    .foregroundColor(.secondary)
                Text("Capacity \(capacity)")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            if let temperature = cellar.temperature {
                HStack(spacing: 4) {
                    Image(systemName: "thermometer.medium")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("\(temperature)°F")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
