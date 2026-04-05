import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        TabView {
            CellarsView()
                .tabItem {
                    Label("Cellars", systemImage: "cabinet")
                }

            WineListView()
                .tabItem {
                    Label("My Wines", systemImage: "wineglass")
                }

            SearchView()
                .tabItem {
                    Label("Add Wine", systemImage: "plus.circle")
                }
        }
    }
}
