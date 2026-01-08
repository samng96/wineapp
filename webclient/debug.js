// Debug Panel Module
class DebugPanel {
    constructor() {
        this.isMinimized = false;
        this.maxMessages = 100;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.interceptConsole();
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
        const content = document.getElementById('debug-content');
        const toggleBtn = document.getElementById('debug-toggle-btn');
        const mainContent = document.getElementById('main-content');

        if (panel && content && toggleBtn && mainContent) {
            if (this.isMinimized) {
                panel.classList.add('minimized');
                toggleBtn.textContent = '+';
                toggleBtn.title = 'Expand';
            } else {
                panel.classList.remove('minimized');
                toggleBtn.textContent = '−';
                toggleBtn.title = 'Minimize';
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
    } catch (error) {
        console.error('❌ Error initializing debug panel:', error);
    }
});
