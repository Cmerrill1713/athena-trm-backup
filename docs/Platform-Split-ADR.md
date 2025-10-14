# Architecture Decision Record: Platform Split (AvatarKit / AvatarMobileKit)

## Status
Accepted - Implemented in v1.0.3

## Context
The NeuroForge avatar system needed to support both macOS (desktop) and iOS (mobile) platforms, but contained iOS-only dependencies (UIKit, notifications, haptics) that prevented clean macOS builds. This created technical debt and platform coupling.

## Problem
- UIKit imports in shared code broke macOS compilation
- iOS-specific features (notifications, haptics) leaked into desktop code
- No clear separation between platform capabilities
- CI couldn't enforce platform boundaries

## Decision
Split avatar functionality into two modules:

### AvatarKit (Shared)
- Cross-platform avatar types and logic
- Morph controller and state management
- Platform detection utilities
- Hysteresis and feature toggle logic

### AvatarMobileKit (iOS-only)
- iOS-specific implementations (UIKit, notifications)
- Mobile authentication and token management
- Haptic feedback controllers
- Mobile metrics collection

## Consequences

### Positive
- Clean platform separation - macOS builds without iOS dependencies
- CI enforcement of platform boundaries
- Clear API contracts between modules
- Easier testing and maintenance
- Platform-specific optimizations possible

### Negative
- Increased module complexity
- Import management across modules
- Potential duplication of platform-agnostic logic
- More complex build configurations

### Neutral
- Backward compatibility maintained through type aliases
- Feature detection handles capability differences
- Gradual migration path available

## Alternatives Considered

### Option 1: Runtime Platform Checks
- Use `#if os(iOS)` guards throughout shared code
- Pro: Simpler module structure
- Con: Platform coupling, harder to test, UIKit leaks

### Option 2: Protocol-Based Abstraction
- Define protocols in shared code, implement in platform-specific
- Pro: Clean abstraction, testable
- Con: More complex, over-engineering for current needs

### Option 3: Single Module with Optional Dependencies
- Weak linking of iOS frameworks
- Pro: Simpler distribution
- Con: Still allows UIKit creep, no CI enforcement

## Implementation
- Created AvatarKit/ and AvatarMobileKit/ directories
- Moved iOS-specific code to AvatarMobileKit
- Added SwiftLint rules to prevent platform creep
- Updated CI to test both platforms separately
- Maintained backward compatibility with type aliases

## Future Considerations
- Monitor for platform creep regressions
- Consider similar splits for other cross-platform features
- Evaluate protocol-based approach if complexity increases
