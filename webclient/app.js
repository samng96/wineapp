// Main application entry point
import { Cellar } from './models/Cellar.js';
import { WineReference } from './models/WineReference.js';
import { WineInstance } from './models/WineInstance.js';
import { CellarManager } from './cellarManager.js';

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
        this.showView('home');
    }

    initCellarManager() {
        try {
            window.cellarManager = new CellarManager();
        } catch (error) {
            console.error('Error initializing CellarManager:', error);
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
                
                if (viewName === 'photo') {
                    alert('Add Wines feature coming soon!');
                    return;
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
        const searchInput = document.getElementById('search-input');

        navSearchInput.addEventListener('focus', () => {
            this.showView('search');
            searchInput.focus();
        });

        navSearchInput.addEventListener('input', (e) => {
            searchInput.value = e.target.value;
            this.performSearch(e.target.value);
        });

        searchInput.addEventListener('input', (e) => {
            navSearchInput.value = e.target.value;
            this.performSearch(e.target.value);
        });
    }

    showView(viewName) {
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
