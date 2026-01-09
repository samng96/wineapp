// Debug Panel Module
class DebugPanel {
    constructor() {
        this.isMinimized = true; // Start minimized by default
        this.maxMessages = 100;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.interceptConsole();
        // Set initial minimized state
        this.setMinimizedState();
    }

    setMinimizedState() {
        const panel = document.getElementById('debug-panel');
        const app = document.getElementById('app');
        const content = document.getElementById('debug-content');
        const toggleBtn = document.getElementById('debug-toggle-btn');

        if (panel && content && toggleBtn) {
            if (this.isMinimized) {
                panel.classList.add('minimized');
                toggleBtn.textContent = '+';
                toggleBtn.title = 'Expand';
            } else {
                panel.classList.remove('minimized');
                toggleBtn.textContent = '−';
                toggleBtn.title = 'Minimize';
            }
            // Set app width based on minimized state
            if (app) {
                setTimeout(() => {
                    if (this.isMinimized) {
                        app.style.width = 'calc(100% - 50px)';
                    } else {
                        app.style.width = 'calc(100% - 400px)';
                    }
                }, 0);
            }
        }
    }

    setupEventListeners() {
        const toggleBtn = document.getElementById('debug-toggle-btn');
        const clearBtn = document.getElementById('debug-clear-btn');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clear());
        }
    }

    interceptConsole() {
        // Store original console methods
        const originalLog = console.log;
        const originalError = console.error;
        const originalWarn = console.warn;
        const originalInfo = console.info;

        // Override console.log
        console.log = (...args) => {
            originalLog.apply(console, args);
            this.addMessage('log', args);
        };

        // Override console.error
        console.error = (...args) => {
            originalError.apply(console, args);
            this.addMessage('error', args);
        };

        // Override console.warn
        console.warn = (...args) => {
            originalWarn.apply(console, args);
            this.addMessage('warn', args);
        };

        // Override console.info
        console.info = (...args) => {
            originalInfo.apply(console, args);
            this.addMessage('info', args);
        };
        
        // Test that interception is working
        console.log('Debug panel console interception active');
    }

    addMessage(type, args) {
        const content = document.getElementById('debug-content');
        if (!content) {
            console.warn('Debug content element not found!');
            return;
        }

        // Format the message
        const message = args.map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg, null, 2);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');

        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `debug-message debug-${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        messageEl.innerHTML = `
            <span class="debug-timestamp">[${timestamp}]</span>
            <span class="debug-type">[${type.toUpperCase()}]</span>
            <span class="debug-text">${this.escapeHtml(message)}</span>
        `;

        // Add to top of content
        content.insertBefore(messageEl, content.firstChild);

        // Limit number of messages
        const messages = content.querySelectorAll('.debug-message');
        if (messages.length > this.maxMessages) {
            messages[messages.length - 1].remove();
        }

        // Auto-scroll to top
        content.scrollTop = 0;
    }

    clear() {
        const content = document.getElementById('debug-content');
        if (content) {
            content.innerHTML = '';
        }
    }

    toggle() {
        this.isMinimized = !this.isMinimized;
        const panel = document.getElementById('debug-panel');
        const app = document.getElementById('app');
        const content = document.getElementById('debug-content');
        const toggleBtn = document.getElementById('debug-toggle-btn');

        if (panel && content && toggleBtn) {
            // Use setTimeout to ensure CSS transition completes before measuring
            if (this.isMinimized) {
                panel.classList.add('minimized');
                toggleBtn.textContent = '+';
                toggleBtn.title = 'Expand';
                // Adjust app width when minimized (debug panel is 50px)
                setTimeout(() => {
                    if (app) {
                        app.style.width = 'calc(100% - 50px)';
                    }
                }, 0);
            } else {
                panel.classList.remove('minimized');
                toggleBtn.textContent = '−';
                toggleBtn.title = 'Minimize';
                // Adjust app width when expanded (debug panel is 400px)
                setTimeout(() => {
                    if (app) {
                        app.style.width = 'calc(100% - 400px)';
                    }
                }, 0);
            }
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Public method to log custom events
    logEvent(eventName, data = {}) {
        console.log(`[EVENT] ${eventName}`, data);
    }
}

// Initialize debug panel when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded - initializing debug panel...');
    try {
        window.debugPanel = new DebugPanel();
        console.log('✅ Debug panel initialized successfully');
        // Test that interception is working
        console.log('Testing debug panel - this message should appear in the panel');
        
        // Initial state is set by setMinimizedState() in constructor
    } catch (error) {
        console.error('❌ Error initializing debug panel:', error);
    }
});
