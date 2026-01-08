// Main application entry point
import { Cellar } from './models/Cellar.js';
import { WineReference } from './models/WineReference.js';
import { WineInstance } from './models/WineInstance.js';

class WineApp {
    constructor() {
        this.currentView = 'home';
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupMenu();
        this.setupSearch();
        this.showView('home');
    }

    setupNavigation() {
        // Bottom nav buttons
        const navButtons = document.querySelectorAll('.nav-btn[data-view]');
        navButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.currentTarget.getAttribute('data-view');
                if (view === 'photo') {
                    // TODO: Implement photo/add wines functionality
                    alert('Add Wines feature coming soon!');
                    return;
                }
                this.showView(view);
            });
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

        // Navigate to search view when typing in nav search
        navSearchInput.addEventListener('focus', () => {
            this.showView('search');
            searchInput.focus();
        });

        // Sync search inputs
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
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
            this.currentView = viewName;
        }

        // Update nav button states
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-view') === viewName) {
                btn.classList.add('active');
            }
        });
    }

    performSearch(searchTerm) {
        // TODO: Implement search functionality
        console.log('Searching for:', searchTerm);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WineApp();
});
