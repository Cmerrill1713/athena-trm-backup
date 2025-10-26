/**
 * Athena User Profiles System
 * Family member profiles with preferences, kid mode, and guest mode
 */

// Profile definitions
const PROFILES = {
    christian: {
        id: 'christian',
        name: 'Christian',
        role: 'parent',
        avatar: '👨‍💻',
        preferences: {
            voice_enabled: true,
            tts_voice: 'af_sky',
            theme: 'dark',
            show_citations: true,
            enable_web_search: true,
            enable_code_tools: true,
            temperature: 0.7
        },
        permissions: {
            admin: true,
            manage_tasks: true,
            manage_calendar: true,
            web_access: true,
            code_access: true
        }
    },
    wife: {
        id: 'wife',
        name: 'Wife',
        role: 'parent',
        avatar: '👩',
        preferences: {
            voice_enabled: true,
            tts_voice: 'af_bella',
            theme: 'light',
            show_citations: false,
            enable_web_search: true,
            enable_code_tools: false,
            temperature: 0.8
        },
        permissions: {
            admin: true,
            manage_tasks: true,
            manage_calendar: true,
            web_access: true,
            code_access: false
        }
    },
    kid1: {
        id: 'kid1',
        name: 'Kid 1',
        role: 'child',
        avatar: '🧒',
        preferences: {
            voice_enabled: true,
            tts_voice: 'af_sky',
            theme: 'light',
            show_citations: false,
            enable_web_search: true,  // Filtered
            enable_code_tools: false,
            temperature: 0.9
        },
        permissions: {
            admin: false,
            manage_tasks: true,  // Own tasks only
            manage_calendar: false,
            web_access: 'filtered',  // Safe search only
            code_access: false,
            content_filter: true,
            homework_mode: true
        }
    },
    kid2: {
        id: 'kid2',
        name: 'Kid 2',
        role: 'child',
        avatar: '👧',
        preferences: {
            voice_enabled: true,
            tts_voice: 'af_bella',
            theme: 'light',
            show_citations: false,
            enable_web_search: true,  // Filtered
            enable_code_tools: false,
            temperature: 0.9
        },
        permissions: {
            admin: false,
            manage_tasks: true,
            manage_calendar: false,
            web_access: 'filtered',
            code_access: false,
            content_filter: true,
            homework_mode: true
        }
    },
    guest: {
        id: 'guest',
        name: 'Guest',
        role: 'guest',
        avatar: '🌐',
        preferences: {
            voice_enabled: false,
            tts_voice: 'af_sky',
            theme: 'light',
            show_citations: true,
            enable_web_search: true,
            enable_code_tools: false,
            temperature: 0.7
        },
        permissions: {
            admin: false,
            manage_tasks: false,
            manage_calendar: false,
            web_access: true,
            code_access: false,
            session_expires: 3600  // 1 hour
        }
    }
};

// Current profile state
let currentProfile = null;

// Initialize profiles system
function initProfiles() {
    // Load last used profile from localStorage
    const lastProfile = localStorage.getItem('athena_current_profile') || 'christian';
    switchProfile(lastProfile);
    
    // Render profile selector
    renderProfileSelector();
    
    console.log('👥 Profiles system initialized');
}

// Switch to a different profile
function switchProfile(profileId) {
    if (!PROFILES[profileId]) {
        console.error(`Profile ${profileId} not found`);
        return;
    }
    
    currentProfile = PROFILES[profileId];
    localStorage.setItem('athena_current_profile', profileId);
    
    // Apply profile preferences
    applyProfilePreferences(currentProfile);
    
    // Update UI
    updateProfileUI(currentProfile);
    
    // Send profile change to backend
    fetch(`${API_BASE}/users/set_active`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: profileId})
    }).catch(console.error);
    
    console.log(`Switched to profile: ${currentProfile.name}`);
}

// Apply profile preferences to UI
function applyProfilePreferences(profile) {
    const prefs = profile.preferences;
    
    // Apply theme
    if (prefs.theme === 'light') {
        document.body.classList.add('light-theme');
    } else {
        document.body.classList.remove('light-theme');
    }
    
    // Show/hide features based on permissions
    const perms = profile.permissions;
    
    // Code tools
    const codeToolBtn = document.querySelector('.tool-btn[onclick*="code"]');
    if (codeToolBtn) {
        codeToolBtn.style.display = perms.code_access ? 'inline-block' : 'none';
    }
    
    // Web search filter for kids
    if (perms.web_access === 'filtered') {
        // Enable safe search mode
        window.ATHENA_SAFE_SEARCH = true;
    } else {
        window.ATHENA_SAFE_SEARCH = false;
    }
    
    // Content filter for kids
    if (perms.content_filter) {
        window.ATHENA_CONTENT_FILTER = true;
    } else {
        window.ATHENA_CONTENT_FILTER = false;
    }
    
    // Homework mode
    if (perms.homework_mode) {
        window.ATHENA_HOMEWORK_MODE = true;
    } else {
        window.ATHENA_HOMEWORK_MODE = false;
    }
}

// Update profile UI indicators
function updateProfileUI(profile) {
    // Update profile badge
    const profileBadge = document.getElementById('profileBadge');
    if (profileBadge) {
        profileBadge.innerHTML = `${profile.avatar} ${profile.name}`;
    }
    
    // Update greeting
    const greeting = profile.role === 'child' 
        ? `Hey ${profile.name}! Need help with homework? 📚`
        : `Hi ${profile.name}! How can I help?`;
    
    // Show in placeholder or welcome message
    const input = document.getElementById('input');
    if (input && !input.value) {
        input.placeholder = greeting;
    }
}

// Render profile selector dropdown
function renderProfileSelector() {
    const container = document.getElementById('profileSelector');
    if (!container) return;
    
    let html = '<select id="profileSelect" onchange="switchProfile(this.value)">';
    
    for (const [id, profile] of Object.entries(PROFILES)) {
        const selected = currentProfile && currentProfile.id === id ? 'selected' : '';
        html += `<option value="${id}" ${selected}>${profile.avatar} ${profile.name}</option>`;
    }
    
    html += '</select>';
    container.innerHTML = html;
}

// Get current profile
function getCurrentProfile() {
    return currentProfile || PROFILES.christian;
}

// Check permission
function hasPermission(permission) {
    const profile = getCurrentProfile();
    return profile.permissions[permission] === true || profile.permissions[permission] === 'filtered';
}

// Get profile preference
function getPreference(key, defaultValue = null) {
    const profile = getCurrentProfile();
    return profile.preferences[key] ?? defaultValue;
}

// Export for use in main app
window.ProfileSystem = {
    init: initProfiles,
    switch: switchProfile,
    getCurrent: getCurrentProfile,
    hasPermission: hasPermission,
    getPreference: getPreference,
    PROFILES: PROFILES
};

