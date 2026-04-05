import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        TabView {
            WineListView()
                .tabItem {
                    Label("My Wines", systemImage: "wineglass")
                }

            CellarsView()
                .tabItem {
                    Label("Cellars", systemImage: "cabinet")
                }

            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
        }
    }
}
