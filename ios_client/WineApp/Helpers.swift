import SwiftUI

// MARK: - AsyncWineImage

struct AsyncWineImage: View {
    let url: URL?
    let width: CGFloat
    let height: CGFloat

    var body: some View {
        AsyncImage(url: url) { phase in
            switch phase {
            case .success(let image):
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            case .failure, .empty:
                ZStack {
                    Color(.systemGray5)
                    Image(systemName: "wineglass")
                        .font(.system(size: min(width, height) * 0.4))
                        .foregroundColor(.secondary)
                }
            @unknown default:
                ZStack {
                    Color(.systemGray5)
                    Image(systemName: "wineglass")
                        .font(.system(size: min(width, height) * 0.4))
                        .foregroundColor(.secondary)
                }
            }
        }
        .frame(width: width, height: height)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

// MARK: - WineTypeColor

func WineTypeColor(type: String) -> Color {
    switch type {
    case "Red":       return Color(red: 0.6, green: 0, blue: 0)
    case "White":     return .orange
    case "Rosé":      return .pink
    case "Sparkling": return .blue
    default:          return .gray
    }
}

// MARK: - StarRatingView

struct StarRatingView: View {
    var rating: Binding<Int>?
    var displayOnly: Bool

    private var currentRating: Int {
        rating?.wrappedValue ?? 0
    }

    var body: some View {
        HStack(spacing: 2) {
            ForEach(1...5, id: \.self) { star in
                Image(systemName: star <= currentRating ? "star.fill" : "star")
                    .foregroundColor(star <= currentRating ? .yellow : .gray)
                    .font(.system(size: displayOnly ? 12 : 20))
                    .onTapGesture {
                        guard !displayOnly, let binding = rating else { return }
                        if binding.wrappedValue == star {
                            binding.wrappedValue = 0
                        } else {
                            binding.wrappedValue = star
                        }
                    }
            }
        }
    }
}

// MARK: - drinkByYear

func drinkByYear(from dateString: String?) -> String? {
    guard let dateString = dateString, !dateString.isEmpty else { return nil }
    // Expect ISO-8601 date strings like "2028-01-01" or "2028-01-01T00:00:00Z"
    let components = dateString.split(separator: "-")
    if let yearStr = components.first, yearStr.count == 4 {
        return String(yearStr)
    }
    return nil
}

// MARK: - View+errorAlert

extension View {
    func errorAlert(error: Binding<Error?>) -> some View {
        alert(
            "Error",
            isPresented: Binding(
                get: { error.wrappedValue != nil },
                set: { if !$0 { error.wrappedValue = nil } }
            )
        ) {
            Button("OK") { error.wrappedValue = nil }
        } message: {
            Text(error.wrappedValue?.localizedDescription ?? "An unknown error occurred.")
        }
    }
}

// MARK: - LoadingOverlay

struct LoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.35)
                .ignoresSafeArea()
            VStack(spacing: 12) {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    .scaleEffect(1.4)
                Text("Loading…")
                    .foregroundColor(.white)
                    .font(.subheadline)
            }
            .padding(28)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill(Color(.systemGray2).opacity(0.85))
            )
        }
    }
}
