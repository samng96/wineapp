// Notification Overlay Module
// A reusable notification that slides up from the bottom of the screen.

class NotificationOverlay {
    constructor() {
        this.container = document.getElementById('notification-overlay');
        this.messageEl = document.getElementById('notification-message');
        this.imageEl = document.getElementById('notification-image');
        this.buttonsEl = document.getElementById('notification-buttons');
        this.yesBtn = document.getElementById('notification-yes-btn');
        this.noBtn = document.getElementById('notification-no-btn');
        this.dismissTimer = null;
        this.confirmResolve = null;

        // Click to dismiss (only when not in confirm mode)
        if (this.container) {
            this.container.addEventListener('click', (e) => {
                // Don't dismiss on click when buttons are showing, unless clicking a button
                if (this.confirmResolve) return;
                this.hide();
            });
        }

        // Yes/No button handlers
        if (this.yesBtn) {
            this.yesBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.resolveConfirm(true);
            });
        }
        if (this.noBtn) {
            this.noBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.resolveConfirm(false);
            });
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

        // Hide buttons
        if (this.buttonsEl) {
            this.buttonsEl.classList.add('hidden');
        }
        this.confirmResolve = null;

        this.container.classList.remove('visible');

        // After the slide-out transition completes, hide entirely
        setTimeout(() => {
            if (!this.container.classList.contains('visible')) {
                this.container.classList.add('hidden');
            }
        }, 300);
    }

    confirm(message, { imageUrl = null } = {}) {
        return new Promise((resolve) => {
            this.confirmResolve = resolve;

            // Show buttons
            if (this.buttonsEl) {
                this.buttonsEl.classList.remove('hidden');
            }

            // Show with no auto-dismiss (durationMs = 0)
            this.show(message, { durationMs: 0, imageUrl });
        });
    }

    resolveConfirm(value) {
        const resolve = this.confirmResolve;
        this.hide();
        if (resolve) {
            resolve(value);
        }
    }
}

let notificationInstance = null;

export function getNotificationOverlay() {
    if (!notificationInstance) {
        notificationInstance = new NotificationOverlay();
    }
    return notificationInstance;
}
