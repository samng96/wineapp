import SwiftUI

// MARK: - SearchDetailSheet

struct SearchDetailSheet: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.dismiss) private var dismiss

    let result: VivinoResult

    @State private var vintage: Int
    @State private var priceText: String = ""
    @State private var quantity: Int = 1
    @State private var drinkByDate: String?
    @State private var isAdding = false
    @State private var addError: Error? = nil

    // Computed drink-by year for display
    private var drinkByDisplayYear: String? {
        if let year = drinkByYear(from: drinkByDate) {
            return year
        }
        if let offset = result.drinkByYearsOffset {
            let year = Calendar.current.component(.year, from: Date()) + offset
            return String(year)
        }
        return nil
    }

    private var parsedPrice: Double? {
        let trimmed = priceText.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return nil }
        return Double(trimmed)
    }

    init(result: VivinoResult) {
        self.result = result
        let currentYear = Calendar.current.component(.year, from: Date())
        _vintage = State(initialValue: result.vintage ?? currentYear)
        _drinkByDate = State(initialValue: result.drinkByDate)
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Form {
                    // MARK: Wine Info Header
                    Section {
                        VStack(spacing: 10) {
                            AsyncWineImage(
                                url: APIClient.shared.resolveImageURL(result.labelImageUrl),
                                width: 100,
                                height: 140
                            )

                            Text(result.name)
                                .font(.title3)
                                .fontWeight(.bold)
                                .multilineTextAlignment(.center)

                            if let producer = result.producer {
                                Text(producer)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }

                            if let type = result.type {
                                TypeBadge(type: type)
                            }

                            if let rating = result.rating {
                                HStack(spacing: 4) {
                                    Image(systemName: "star.fill")
                                        .foregroundColor(.yellow)
                                        .font(.caption)
                                    Text(String(format: "%.1f", rating))
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Text("on Vivino")
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

                    // MARK: Vintage
                    Section("Vintage") {
                        Stepper(
                            value: $vintage,
                            in: 1900...Calendar.current.component(.year, from: Date()) + 5
                        ) {
                            HStack {
                                Text("Year")
                                Spacer()
                                Text(String(vintage))
                                    .foregroundColor(.secondary)
                                    .monospacedDigit()
                            }
                        }
                    }

                    // MARK: Price
                    Section("Price") {
                        HStack {
                            Text("$")
                                .foregroundColor(.secondary)
                            TextField("Optional", text: $priceText)
                                .keyboardType(.decimalPad)
                        }
                    }

                    // MARK: Quantity
                    Section("Quantity") {
                        Stepper(value: $quantity, in: 1...24) {
                            HStack {
                                Text("Bottles")
                                Spacer()
                                Text("\(quantity)")
                                    .foregroundColor(.secondary)
                                    .monospacedDigit()
                            }
                        }
                    }

                    // MARK: Drink By
                    Section("Drink By") {
                        HStack {
                            Text("Year")
                            Spacer()
                            if let year = drinkByDisplayYear {
                                Text(year)
                                    .foregroundColor(.secondary)
                                    .monospacedDigit()
                            } else {
                                Text("Not set")
                                    .foregroundColor(.secondary)
                            }

                            if drinkByDate != nil {
                                Button {
                                    drinkByDate = nil
                                } label: {
                                    Image(systemName: "xmark.circle.fill")
                                        .foregroundColor(.secondary)
                                }
                                .buttonStyle(.plain)
                            }
                        }

                        if let offset = result.drinkByYearsOffset, drinkByDate == nil {
                            let baseYear = Calendar.current.component(.year, from: Date())
                            Text("Estimated from current year + \(offset) years (\(baseYear + offset))")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    // MARK: Error
                    if let error = addError {
                        Section {
                            HStack(spacing: 8) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundColor(.red)
                                Text(error.localizedDescription)
                                    .font(.caption)
                                    .foregroundColor(.red)
                            }
                        }
                    }
                }

                if isAdding {
                    LoadingOverlay()
                }
            }
            .navigationTitle("Add to Collection")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        addToCollection()
                    } label: {
                        if isAdding {
                            ProgressView()
                        } else {
                            Text("Add")
                                .fontWeight(.semibold)
                        }
                    }
                    .disabled(isAdding)
                }
            }
        }
    }

    // MARK: - Add Action

    private func addToCollection() {
        isAdding = true
        addError = nil

        // Resolve drink-by date: prefer explicit drinkByDate, else compute from offset
        let resolvedDrinkBy: String?
        if let explicit = drinkByDate {
            resolvedDrinkBy = explicit
        } else if let offset = result.drinkByYearsOffset {
            let year = Calendar.current.component(.year, from: Date()) + offset
            resolvedDrinkBy = "\(year)-01-01"
        } else {
            resolvedDrinkBy = nil
        }

        Task {
            do {
                try await appState.addToCollection(
                    result: result,
                    vintage: vintage,
                    price: parsedPrice,
                    quantity: quantity,
                    drinkByDate: resolvedDrinkBy
                )
                dismiss()
            } catch {
                addError = error
            }
            isAdding = false
        }
    }
}
