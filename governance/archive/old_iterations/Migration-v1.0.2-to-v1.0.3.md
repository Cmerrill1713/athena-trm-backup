# Migration Guide: v1.0.2 → v1.0.3 (Morph Activation)

## Overview
v1.0.3 introduces platform separation and morph reactivation. The main changes are architectural - splitting avatar functionality into shared and iOS-only modules.

## Breaking Changes

### Import Changes
```swift
// Before
import AvatarTypes
import AvatarNotificationService

// After
import AvatarKit          // Shared types and logic
import AvatarMobileKit    // iOS-only features (when needed)
```

### Type Consolidation
```swift
// Before: Potential conflicts
struct AvatarStatus { ... }     // In morph system
struct ServiceStatus { ... }    // In monitoring

// After: Namespaced and aliased
extension AvatarKit {
    struct AvatarStatus { ... }
}
typealias SystemServiceStatus = ServiceStatus  // For monitoring
```

### Feature Toggles
```swift
// Before: Compile-time flags
#if GHOST_ONLY
// ghost-only code
#endif

// After: Runtime toggles
if MorphFeature.enabled {
    // morph code
} else {
    // ghost-only fallback
}
```

## Platform-Specific Changes

### macOS (Desktop)
- ✅ Builds without iOS dependencies
- ✅ Ghost mode only (morph disabled by default)
- ✅ No UIKit imports allowed
- ✅ Full compatibility maintained

### iOS (Mobile)
- ✅ Full morph capabilities
- ✅ Local notifications with haptics
- ✅ Authentication and metrics
- ✅ LAN connectivity validation

## Migration Steps

### 1. Update Imports
For files using avatar functionality:

```swift
// Add to imports
import AvatarKit

// Add iOS-only imports with guards
#if os(iOS)
import AvatarMobileKit
#endif
```

### 2. Update Type References
```swift
// Before
let status: AvatarStatus

// After
let status: AvatarKit.AvatarStatus
// or use typealias if preferred
```

### 3. Feature Flag Migration
Replace compile-time flags with runtime checks:

```swift
// Before
#if GHOST_ONLY
    // ghost code
#else
    // morph code
#endif

// After
if MorphFeature.enabled {
    // morph code
} else {
    // ghost code
}
```

### 4. Platform-Specific Code
Move iOS-only code to appropriate locations:

```swift
// Before: Mixed in shared files
func showNotification() {
    #if os(iOS)
    UNUserNotificationCenter.current().add(request)
    #endif
}

// After: In AvatarMobileKit
extension AvatarNotificationService {
    func showNotification() {
        UNUserNotificationCenter.current().add(request)
    }
}
```

## Testing Checklist

### macOS Tests
- [ ] Builds without errors
- [ ] No UIKit import warnings
- [ ] Ghost mode works correctly
- [ ] Feature toggles respect environment

### iOS Tests
- [ ] Full build succeeds
- [ ] Morph functionality works
- [ ] Notifications trigger
- [ ] Authentication flows work

### Integration Tests
- [ ] Cross-platform compatibility
- [ ] Feature flag behavior
- [ ] Type consolidation works

## Rollout Strategy

### Phase 1: Internal Testing
1. Deploy to internal test devices
2. Verify platform separation works
3. Test morph reactivation flow

### Phase 2: Beta Release
1. Enable for 10% of external users
2. Monitor for platform-specific crashes
3. Validate morph success rates

### Phase 3: Full Release
1. Gradual rollout: 25% → 50% → 100%
2. Monitor established metrics
3. Emergency rollback available

## Troubleshooting

### Build Errors
- **UIKit not found**: Import AvatarMobileKit and guard with `#if os(iOS)`
- **Type conflicts**: Use fully qualified names or type aliases
- **Missing features**: Check platform availability with `Platform.isIOS`

### Runtime Issues
- **Morph not working**: Check `MORPH_ENABLED=true` environment variable
- **Notifications missing**: Verify iOS entitlements and permissions
- **Auth failures**: Check token refresh and backend connectivity

## Support
- CI will enforce platform boundaries
- SwiftLint will catch UIKit creep
- Tests validate cross-platform compatibility

## Rollback Plan
If issues arise, v1.0.2 remains stable with:
- `MORPH_ENABLED=false` (default)
- Emergency rollback via `make avatar-rollback-force`
- Feature flags can disable morph system

