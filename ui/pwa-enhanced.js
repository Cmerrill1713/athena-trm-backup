/**
 * Athena PWA Enhancements
 * Advanced PWA features: install prompt, offline support, background sync
 */

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        
        this.initPWA();
    }
    
    initPWA() {
        // Listen for install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
            console.log('📱 PWA install prompt ready');
        });
        
        // Check if already installed
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallButton();
            console.log('✅ PWA installed!');
        });
        
        // Listen for online/offline
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateOnlineStatus();
            console.log('🌐 Back online');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateOnlineStatus();
            console.log('📡 Offline mode');
        });
        
        // Check if running as PWA
        if (window.matchMedia('(display-mode: standalone)').matches || 
            window.navigator.standalone === true) {
            this.isInstalled = true;
            console.log('✅ Running as installed PWA');
        }
        
        // Register service worker if not already
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js').then(reg => {
                console.log('✅ Service Worker registered');
                
                // Check for updates
                reg.addEventListener('updatefound', () => {
                    const newWorker = reg.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
            }).catch(err => {
                console.error('Service Worker registration failed:', err);
            });
        }
    }
    
    showInstallButton() {
        let btn = document.getElementById('pwaInstallBtn');
        if (!btn) {
            btn = document.createElement('button');
            btn.id = 'pwaInstallBtn';
            btn.className = 'pwa-install-btn';
            btn.innerHTML = '📱 Install Athena App';
            btn.onclick = () => this.promptInstall();
            
            // Add to header or toolbar
            const header = document.querySelector('header') || document.querySelector('.header');
            if (header) {
                header.appendChild(btn);
            }
        }
        btn.style.display = 'inline-block';
    }
    
    hideInstallButton() {
        const btn = document.getElementById('pwaInstallBtn');
        if (btn) {
            btn.style.display = 'none';
        }
    }
    
    async promptInstall() {
        if (!this.deferredPrompt) {
            console.log('Install prompt not available');
            return;
        }
        
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            console.log('✅ User accepted install');
        } else {
            console.log('❌ User dismissed install');
        }
        
        this.deferredPrompt = null;
    }
    
    updateOnlineStatus() {
        const statusIndicator = document.getElementById('onlineStatus');
        if (statusIndicator) {
            if (this.isOnline) {
                statusIndicator.innerHTML = '🌐 Online';
                statusIndicator.className = 'status-online';
            } else {
                statusIndicator.innerHTML = '📡 Offline';
                statusIndicator.className = 'status-offline';
            }
        }
        
        // Show/hide online-only features
        document.querySelectorAll('.online-only').forEach(el => {
            el.style.display = this.isOnline ? 'inline-block' : 'none';
        });
        
        // Show offline notice
        if (!this.isOnline) {
            this.showOfflineNotice();
        }
    }
    
    showOfflineNotice() {
        const notice = document.createElement('div');
        notice.className = 'offline-notice';
        notice.innerHTML = `
            📡 <strong>Offline Mode</strong><br>
            Some features may be limited. Athena still works locally!
        `;
        notice.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            background: #ff9800;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notice);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notice.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notice.remove(), 300);
        }, 5000);
    }
    
    showUpdateNotification() {
        const notice = document.createElement('div');
        notice.className = 'update-notice';
        notice.innerHTML = `
            🔄 <strong>Update Available</strong><br>
            <button onclick="location.reload()" style="margin-top:10px; padding:8px 16px; background:white; color:#4a9eff; border:none; border-radius:4px; cursor:pointer;">
                Reload to Update
            </button>
        `;
        notice.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #4a9eff;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
        `;
        
        document.body.appendChild(notice);
    }
    
    // Request persistent storage (for large corpus)
    async requestPersistentStorage() {
        if (navigator.storage && navigator.storage.persist) {
            const isPersisted = await navigator.storage.persist();
            if (isPersisted) {
                console.log('✅ Persistent storage granted');
            } else {
                console.log('⚠️ Persistent storage denied');
            }
        }
    }
    
    // Check storage quota
    async checkStorageQuota() {
        if (navigator.storage && navigator.storage.estimate) {
            const estimate = await navigator.storage.estimate();
            const percentUsed = (estimate.usage / estimate.quota * 100).toFixed(2);
            
            console.log(`💾 Storage: ${(estimate.usage / 1024 / 1024).toFixed(2)}MB / ${(estimate.quota / 1024 / 1024).toFixed(2)}MB (${percentUsed}%)`);
            
            if (percentUsed > 80) {
                this.showStorageWarning(percentUsed);
            }
            
            return estimate;
        }
    }
    
    showStorageWarning(percentUsed) {
        const notice = document.createElement('div');
        notice.innerHTML = `
            ⚠️ <strong>Storage Warning</strong><br>
            ${percentUsed}% storage used. Clear old data?
        `;
        notice.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            background: #ff9800;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
        `;
        
        document.body.appendChild(notice);
        setTimeout(() => notice.remove(), 10000);
    }
}

// Initialize PWA manager
window.addEventListener('load', () => {
    window.pwaManager = new PWAManager();
    window.pwaManager.requestPersistentStorage();
    window.pwaManager.checkStorageQuota();
});

// Share API integration (if available)
async function shareConversation() {
    const messages = Array.from(document.querySelectorAll('.message')).map(msg => {
        const role = msg.classList.contains('user') ? 'You' : 'Athena';
        const content = msg.querySelector('.message-content').textContent;
        return `${role}: ${content}`;
    }).join('\n\n');
    
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'Athena Conversation',
                text: messages
            });
            console.log('✅ Conversation shared');
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Share failed:', error);
            }
        }
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(messages).then(() => {
            alert('Conversation copied to clipboard!');
        });
    }
}

window.shareConversation = shareConversation;

