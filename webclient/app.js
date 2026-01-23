// Main application entry point
import { Cellar } from './models/Cellar.js';
import { WineReference } from './models/WineReference.js';
import { WineInstance } from './models/WineInstance.js';
import { CellarManager } from './cellarManager.js';
import { WineManager } from './wineManager.js';
import { AddWineManager } from './addWineManager.js';
import { WineReferenceFormManager } from './wineReferenceFormManager.js';
import { WineSearchManager } from './wineSearchManager.js';

class WineApp {
    constructor() {
        this.currentView = 'home';
        try {
            this.init();
        } catch (error) {
            console.error('Error in WineApp.init():', error);
            // Don't throw - let the object be created even if init fails
        }
    }

    init() {
        this.setupNavigation();
        this.setupMenu();
        this.setupSearch();
        this.initCellarManager();
        this.initWineManager();
        this.initAddWineManager();
        this.initWineReferenceFormManager();
        this.initWineSearchManager();
        this.initWineDetailView();
        this.showView('home');
    }
    
    initWineDetailView() {
        try {
            import('./wineDetailView.js').then(({ getWineDetailView }) => {
                getWineDetailView(); // Initialize the singleton
            }).catch(error => {
                console.error('Error initializing wine detail view:', error);
            });
        } catch (error) {
            console.error('Error loading wine detail view module:', error);
        }
    }

    initCellarManager() {
        try {
            window.cellarManager = new CellarManager();
        } catch (error) {
            console.error('Error initializing CellarManager:', error);
        }
    }

    initWineManager() {
        try {
            window.wineManager = new WineManager();
        } catch (error) {
            console.error('Error initializing WineManager:', error);
        }
    }

    initAddWineManager() {
        try {
            window.addWineManager = new AddWineManager();
        } catch (error) {
            console.error('Error initializing AddWineManager:', error);
        }
    }

    initWineReferenceFormManager() {
        try {
            window.wineReferenceFormManager = new WineReferenceFormManager();
        } catch (error) {
            console.error('Error initializing WineReferenceFormManager:', error);
        }
    }

    initWineSearchManager() {
        try {
            window.wineSearchManager = new WineSearchManager();
        } catch (error) {
            console.error('Error initializing WineSearchManager:', error);
        }
    }

    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn[data-view]');
        
        if (navButtons.length === 0) {
            console.error('No navigation buttons found!');
            return;
        }
        
        navButtons.forEach((btn) => {
            const viewName = btn.getAttribute('data-view');
            const self = this;
            
            const clickHandler = function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Close wine detail modal if open
                const wineDetailModal = document.getElementById('wine-detail-modal');
                if (wineDetailModal && !wineDetailModal.classList.contains('hidden')) {
                    // Dynamically import and close the modal
                    import('./wineDetailView.js').then(({ getWineDetailView }) => {
                        const wineDetailView = getWineDetailView();
                        wineDetailView.hide();
                    }).catch(error => {
                        console.error('Error closing wine detail view:', error);
                    });
                }
                
                self.showView(viewName);
            };
            
            btn.addEventListener('click', clickHandler);
        });
    }

    setupMenu() {
        const menuBtn = document.getElementById('menu-btn');
        const menuOverlay = document.getElementById('menu-overlay');
        const closeMenuBtn = document.getElementById('close-menu-btn');
        const menuItems = document.querySelectorAll('.menu-item');

        menuBtn.addEventListener('click', () => {
            menuOverlay.classList.remove('hidden');
        });

        closeMenuBtn.addEventListener('click', () => {
            menuOverlay.classList.add('hidden');
        });

        menuOverlay.addEventListener('click', (e) => {
            if (e.target === menuOverlay) {
                menuOverlay.classList.add('hidden');
            }
        });

        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const action = e.currentTarget.getAttribute('data-action');
                menuOverlay.classList.add('hidden');
                
                if (action === 'settings') {
                    alert('Settings feature coming soon!');
                } else if (action === 'profile') {
                    alert('User Profile feature coming soon!');
                }
            });
        });
    }

    setupSearch() {
        const navSearchInput = document.getElementById('nav-search-input');
        const navSearchBtn = document.getElementById('nav-search-btn');
        const searchInput = document.getElementById('search-input');

        // Remove the focus handler that changes pages
        // navSearchInput.addEventListener('focus', () => {
        //     this.showView('search');
        //     searchInput.focus();
        // });

        // Handle Enter key on nav search input
        navSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performNavSearch();
            }
        });

        // Handle search button click
        if (navSearchBtn) {
            navSearchBtn.addEventListener('click', () => {
                this.performNavSearch();
            });
        }

        // Keep input syncing for search view (if it exists)
        if (searchInput) {
            navSearchInput.addEventListener('input', (e) => {
                searchInput.value = e.target.value;
            });

            searchInput.addEventListener('input', (e) => {
                navSearchInput.value = e.target.value;
                this.performSearch(e.target.value);
            });
        }
    }

    performNavSearch() {
        const navSearchInput = document.getElementById('nav-search-input');
        const searchTerm = navSearchInput.value.trim();
        
        // Navigate to wines page with search term
        this.showView('wines', { searchTerm: searchTerm });
    }

    showView(viewName, options = {}) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        // Show selected view
        const viewId = `${viewName}-view`;
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
            this.currentView = viewName;
        } else {
            console.error(`View "${viewName}" not found!`);
        }

        // Update nav button states (only for main navigation views)
        if (viewName !== 'cellar-detail') {
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-view') === viewName) {
                    btn.classList.add('active');
                }
            });
        }

        // Reload cellar data when viewing cellar page
        if (viewName === 'cellar' && window.cellarManager) {
            window.cellarManager.loadCellars();
        }

        // Load wines when viewing wines page
        if (viewName === 'wines' && window.wineManager) {
            window.wineManager.loadWines(options.searchTerm);
        }

        // Show/hide camera when viewing photo page
        if (viewName === 'photo' && window.addWineManager) {
            window.addWineManager.show();
        } else if (window.addWineManager) {
            window.addWineManager.hide();
        }

        // Show/hide wine reference form
        if (viewName === 'wine-reference-form' && window.wineReferenceFormManager) {
            window.wineReferenceFormManager.show(options);
        } else if (window.wineReferenceFormManager) {
            window.wineReferenceFormManager.hide();
        }

        // Show/hide wine search
        if (viewName === 'wine-search' && window.wineSearchManager) {
            window.wineSearchManager.show();
        } else if (window.wineSearchManager) {
            window.wineSearchManager.hide();
        }
    }

    performSearch(searchTerm) {
        // TODO: Implement search functionality
        console.log('Searching for:', searchTerm);
    }
}

// Initialize app function
function initApp() {
    try {
        if (typeof WineApp === 'undefined') {
            console.error('WineApp is not defined!');
            return;
        }
        
        const appInstance = new WineApp();
        window.app = appInstance;
        
        // Make showView globally accessible
        window.showView = (viewName) => {
            if (window.app && typeof window.app.showView === 'function') {
                return window.app.showView(viewName);
            }
        };
    } catch (error) {
        console.error('Error initializing WineApp:', error);
        alert('Error initializing app. Please check the console for details.');
    }
}

// Make initApp globally accessible
window.initApp = initApp;

// Initialize app when DOM is loaded (or immediately if already loaded)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
