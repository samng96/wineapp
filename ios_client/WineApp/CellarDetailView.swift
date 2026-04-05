import SwiftUI

// MARK: - Display mode

enum CellarDisplayMode {
    case labels, vintage
}

// MARK: - CellarDetailView

struct CellarDetailView: View {
    @EnvironmentObject var appState: AppState
    let cellar: Cellar

    @State private var displayMode: CellarDisplayMode = .labels
    @State private var selectedResolved: ResolvedWine? = nil
    @State private var selectedInstances: [WineInstance] = []

    // Pinch zoom
    @State private var zoomScale: CGFloat = 1.0
    @State private var lastZoomScale: CGFloat = 1.0
    // Natural content size captured from layout
    @State private var naturalSize: CGSize = .zero

    var body: some View {
        ScrollView([.horizontal, .vertical], showsIndicators: true) {
            cellarContent
                // Capture natural size on first layout pass
                .background(
                    GeometryReader { geo in
                        Color.clear.onAppear {
                            if naturalSize == .zero {
                                naturalSize = geo.size
                            }
                        }
                    }
                )
                // Scale visually from top-leading, then set the layout frame to match
                .scaleEffect(zoomScale, anchor: .topLeading)
                .frame(
                    width:  naturalSize == .zero ? nil : naturalSize.width  * zoomScale,
                    height: naturalSize == .zero ? nil : naturalSize.height * zoomScale,
                    alignment: .topLeading
                )
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(cellar.name)
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    displayMode = displayMode == .labels ? .vintage : .labels
                } label: {
                    Label(
                        displayMode == .labels ? "Vintage" : "Labels",
                        systemImage: displayMode == .labels ? "tag" : "photo"
                    )
                    .font(.subheadline)
                }
            }
        }
        // Pinch-to-zoom gesture on the whole view
        .gesture(
            MagnificationGesture()
                .onChanged { value in
                    let proposed = lastZoomScale * value
                    zoomScale = min(max(proposed, 0.3), 4.0)
                }
                .onEnded { _ in
                    lastZoomScale = zoomScale
                }
        )
        .sheet(item: $selectedResolved) { resolved in
            WineDetailSheet(resolved: resolved, instances: selectedInstances)
        }
    }

    // MARK: - Cellar content (all shelves)

    private var cellarContent: some View {
        VStack(alignment: .center, spacing: 0) {
            ForEach(Array(cellar.shelves.enumerated()), id: \.offset) { idx, shelf in
                ShelfRow(
                    cellar: cellar,
                    shelfIndex: idx,
                    shelf: shelf,
                    displayMode: displayMode
                ) { instance in
                    guard let resolved = appState.resolveWine(for: instance) else { return }
                    selectedInstances = appState.instances.filter { $0.referenceId == instance.referenceId }
                    selectedResolved = resolved
                }
            }
        }
        .padding(20)
    }
}

// MARK: - ShelfRow

private struct ShelfRow: View {
    @EnvironmentObject var appState: AppState
    let cellar: Cellar
    let shelfIndex: Int
    let shelf: Cellar.ShelfConfig
    let displayMode: CellarDisplayMode
    let onTap: (WineInstance) -> Void

    private let bottleSize: CGFloat = 80

    private var shelfData: [String: [String?]] {
        cellar.winePositions[String(shelfIndex)] ?? [:]
    }

    var body: some View {
        VStack(alignment: .center, spacing: 12) {
            if shelf.isDouble {
                staggeredRow
            } else {
                singleRow
            }
            shelfBar
        }
        .padding(.vertical, 12)
    }

    // MARK: Single-sided shelf — one horizontal row

    private var singleRow: some View {
        let raw      = shelfData["single"] ?? []
        let padded   = padded(raw, to: shelf.positions)

        return HStack(spacing: 0) {
            ForEach(0..<shelf.positions, id: \.self) { pos in
                BottleCircle(
                    instanceId: padded[pos],
                    displayMode: displayMode,
                    size: bottleSize,
                    onTap: onTap
                )
                .frame(width: bottleSize, height: bottleSize)
            }
        }
    }

    // MARK: Double-sided shelf — staggered back (top) + front (bottom)
    //
    // Back row is offset 40 pt to the right so circles nest between front circles.
    // VStack gives correct height; the 40 pt leading spacer gives the horizontal offset.

    private var staggeredRow: some View {
        let rawFront  = shelfData["front"] ?? []
        let rawBack   = shelfData["back"]  ?? []
        let front     = padded(rawFront, to: shelf.positions)
        let back      = padded(rawBack,  to: shelf.positions)
        let halfBottle = bottleSize / 2

        return VStack(alignment: .leading, spacing: 0) {
            // Back row — top, shifted right by half a bottle
            HStack(spacing: 0) {
                Color.clear.frame(width: halfBottle, height: bottleSize)
                ForEach(0..<shelf.positions, id: \.self) { pos in
                    BottleCircle(
                        instanceId: back[pos],
                        displayMode: displayMode,
                        size: bottleSize,
                        onTap: onTap
                    )
                    .frame(width: bottleSize, height: bottleSize)
                }
            }

            // Front row — bottom, starts flush left
            HStack(spacing: 0) {
                ForEach(0..<shelf.positions, id: \.self) { pos in
                    BottleCircle(
                        instanceId: front[pos],
                        displayMode: displayMode,
                        size: bottleSize,
                        onTap: onTap
                    )
                    .frame(width: bottleSize, height: bottleSize)
                }
            }
        }
    }

    // MARK: Shelf label bar

    private var shelfBar: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(.systemBackground))
                .overlay(
                    RoundedRectangle(cornerRadius: 2)
                        .stroke(Color(.systemGray3), lineWidth: 1)
                )
            Text("Shelf \(shelfIndex + 1)")
                .font(.system(size: 11, weight: .semibold))
                .tracking(0.5)
                .textCase(.uppercase)
                .foregroundColor(.secondary)
        }
        .frame(height: 20)
    }

    // MARK: Helpers

    private func padded(_ arr: [String?], to count: Int) -> [String?] {
        var result = arr
        while result.count < count { result.append(nil) }
        return result
    }
}

// MARK: - BottleCircle

private struct BottleCircle: View {
    @EnvironmentObject var appState: AppState
    let instanceId: String?
    let displayMode: CellarDisplayMode
    let size: CGFloat
    let onTap: (WineInstance) -> Void

    private var instance: WineInstance? {
        guard let id = instanceId else { return nil }
        return appState.instances.first { $0.id == id }
    }

    private var resolved: ResolvedWine? {
        instance.flatMap { appState.resolveWine(for: $0) }
    }

    var body: some View {
        if let resolved, let instance {
            filledBottle(resolved: resolved, instance: instance)
                .onTapGesture { onTap(instance) }
        } else {
            emptyBottle
        }
    }

    // MARK: Filled — label image or vintage-colored circle

    @ViewBuilder
    private func filledBottle(resolved: ResolvedWine, instance: WineInstance) -> some View {
        if displayMode == .labels,
           let url = APIClient.shared.resolveImageURL(resolved.labelImageUrl) {
            AsyncImage(url: url) { phase in
                switch phase {
                case .success(let img):
                    img.resizable().aspectRatio(contentMode: .fill)
                default:
                    vintageCircle(resolved: resolved)
                }
            }
            .frame(width: size, height: size)
            .clipShape(Circle())
            .overlay(Circle().stroke(Color(.systemGray3), lineWidth: 1.5))
        } else {
            vintageCircle(resolved: resolved)
        }
    }

    @ViewBuilder
    private func vintageCircle(resolved: ResolvedWine) -> some View {
        ZStack {
            Circle().fill(fillColor(resolved.type))
            Circle().stroke(borderColor(resolved.type), lineWidth: 2)
            if let v = resolved.vintage {
                Text(String(v))
                    .font(.system(size: size * 0.17, weight: .semibold))
                    .foregroundColor(textColor(resolved.type))
                    .minimumScaleFactor(0.5)
                    .lineLimit(1)
            }
        }
        .frame(width: size, height: size)
    }

    // MARK: Empty circle

    private var emptyBottle: some View {
        ZStack {
            Circle().fill(Color(.systemGray6))
            Circle().stroke(Color(.systemGray4), lineWidth: 1)
        }
        .frame(width: size, height: size)
    }

    // MARK: Wine-type colors (matches web CSS)

    private func fillColor(_ type: String) -> Color {
        switch type.lowercased() {
        case let t where t.contains("red"):       return Color(red: 0.60, green: 0.00, blue: 0.07) // #990011
        case let t where t.contains("white"):     return Color(red: 1.00, green: 0.97, blue: 0.86) // #FFF8DC
        case let t where t.contains("ros"):       return Color(red: 1.00, green: 0.89, blue: 0.88) // #FFE4E1
        case let t where t.contains("sparkling"): return Color(red: 0.94, green: 0.97, blue: 1.00) // #F0F8FF
        default:                                  return Color(.systemGray5)
        }
    }

    private func borderColor(_ type: String) -> Color {
        switch type.lowercased() {
        case let t where t.contains("red"):       return Color(red: 0.35, green: 0.15, blue: 0.17)
        case let t where t.contains("white"):     return Color(.systemGray3)
        case let t where t.contains("ros"):       return Color(red: 1.00, green: 0.70, blue: 0.70)
        case let t where t.contains("sparkling"): return Color(red: 0.70, green: 0.85, blue: 1.00)
        default:                                  return Color(.systemGray3)
        }
    }

    private func textColor(_ type: String) -> Color {
        switch type.lowercased() {
        case let t where t.contains("red"): return .white
        case let t where t.contains("ros"): return Color(red: 0.60, green: 0.00, blue: 0.07)
        default:                            return Color(.label)
        }
    }
}
