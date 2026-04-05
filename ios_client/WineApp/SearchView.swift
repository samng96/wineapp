import SwiftUI

// MARK: - SearchView

struct SearchView: View {
    @EnvironmentObject var appState: AppState

    @State private var query: String = ""
    @State private var results: [VivinoResult] = []
    @State private var isSearching = false
    @State private var searchError: Error? = nil
    @State private var selectedResult: VivinoResult? = nil
    @State private var hasSearched = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Search bar row
                HStack(spacing: 8) {
                    TextField("Search Vivino…", text: $query)
                        .textFieldStyle(.roundedBorder)
                        .submitLabel(.search)
                        .onSubmit { performSearch() }
                        .autocorrectionDisabled()

                    Button {
                        performSearch()
                    } label: {
                        if isSearching {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle())
                                .frame(width: 36, height: 36)
                        } else {
                            Image(systemName: "magnifyingglass")
                                .font(.body)
                                .frame(width: 36, height: 36)
                                .foregroundColor(.white)
                                .background(Color.accentColor)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                    }
                    .disabled(query.trimmingCharacters(in: .whitespaces).isEmpty || isSearching)
                }
                .padding(.horizontal)
                .padding(.vertical, 10)
                .background(Color(.systemGroupedBackground))

                ZStack {
                    if isSearching {
                        VStack {
                            Spacer()
                            ProgressView("Searching…")
                            Spacer()
                        }
                    } else if results.isEmpty && hasSearched {
                        ContentUnavailableView(
                            "No Results",
                            systemImage: "wineglass",
                            description: Text("Try a different search term.")
                        )
                    } else if results.isEmpty {
                        VStack {
                            Spacer()
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 48))
                                .foregroundColor(.secondary)
                                .padding(.bottom, 8)
                            Text("Search for wines to add to your collection.")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal)
                            Spacer()
                        }
                    } else {
                        List(results) { result in
                            VivinoResultRow(result: result)
                                .contentShape(Rectangle())
                                .onTapGesture {
                                    selectedResult = result
                                }
                                .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                        }
                        .listStyle(.insetGrouped)
                    }
                }
            }
            .navigationTitle("Add Wine")
            .errorAlert(error: $searchError)
            .sheet(item: $selectedResult) { result in
                SearchDetailSheet(result: result)
            }
        }
    }

    private func performSearch() {
        let trimmed = query.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }

        isSearching = true
        results = []
        hasSearched = false

        Task {
            do {
                let fetched: [VivinoResult] = try await APIClient.shared.get(
                    API.vivinoSearch(query: trimmed, limit: 10)
                )
                results = fetched
                hasSearched = true
            } catch {
                searchError = error
                hasSearched = true
            }
            isSearching = false
        }
    }
}

// MARK: - VivinoResultRow

struct VivinoResultRow: View {
    let result: VivinoResult

    var body: some View {
        HStack(spacing: 12) {
            AsyncWineImage(
                url: APIClient.shared.resolveImageURL(result.labelImageUrl),
                width: 40,
                height: 56
            )

            VStack(alignment: .leading, spacing: 4) {
                Text(result.name)
                    .font(.headline)
                    .lineLimit(2)

                HStack(spacing: 4) {
                    if let producer = result.producer {
                        Text(producer)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    if let vintage = result.vintage {
                        Text("·")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(String(vintage))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                HStack(spacing: 6) {
                    if let type = result.type {
                        TypeBadge(type: type)
                    }

                    if let rating = result.rating {
                        HStack(spacing: 2) {
                            Image(systemName: "star.fill")
                                .font(.caption2)
                                .foregroundColor(.yellow)
                            Text(String(format: "%.1f", rating))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }

            Spacer()

            Image(systemName: "plus.circle")
                .font(.title3)
                .foregroundColor(.accentColor)
        }
        .padding(.vertical, 4)
    }
}
