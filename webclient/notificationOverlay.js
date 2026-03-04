// Notification Overlay Module
// A reusable notification that slides up from the bottom of the screen.

class NotificationOverlay {
    constructor() {
        this.container = document.getElementById('notification-overlay');
        this.messageEl = document.getElementById('notification-message');
        this.imageEl = document.getElementById('notification-image');
        this.dismissTimer = null;

        // Click to dismiss
        if (this.container) {
            this.container.addEventListener('click', () => this.hide());
        }
    }

    show(message, { durationMs = 3000, imageUrl = null } = {}) {
        if (!this.container || !this.messageEl) return;

        // Clear any existing timer
        if (this.dismissTimer) {
            clearTimeout(this.dismissTimer);
            this.dismissTimer = null;
        }

        this.messageEl.textContent = message;

        // Set image if provided
        if (this.imageEl) {
            if (imageUrl) {
                this.imageEl.style.backgroundImage = `url(${imageUrl})`;
                this.imageEl.classList.add('has-image');
            } else {
                this.imageEl.style.backgroundImage = '';
                this.imageEl.classList.remove('has-image');
            }
        }

        this.container.classList.remove('hidden');

        // Trigger reflow so the transition plays from the starting position
        this.container.offsetHeight;
        this.container.classList.add('visible');

        // Auto-dismiss after duration (0 = stay until manually dismissed)
        if (durationMs > 0) {
            this.dismissTimer = setTimeout(() => this.hide(), durationMs);
        }
    }

    hide() {
        if (!this.container) return;

        if (this.dismissTimer) {
            clearTimeout(this.dismissTimer);
            this.dismissTimer = null;
        }

        this.container.classList.remove('visible');

        // After the slide-out transition completes, hide entirely
        setTimeout(() => {
            if (!this.container.classList.contains('visible')) {
                this.container.classList.add('hidden');
            }
        }, 300);
    }
}

let notificationInstance = null;

export function getNotificationOverlay() {
    if (!notificationInstance) {
        notificationInstance = new NotificationOverlay();
    }
    return notificationInstance;
}
