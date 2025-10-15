# 🗂️ Persistence Keys Reference

**Purpose**: Document all @AppStorage keys for team coordination  
**Location**: UserDefaults.standard  
**Scope**: Per-user settings

---

## 🔑 Operations Window

### `autoOpenOps`
- **Type**: Bool
- **Default**: `true`
- **Purpose**: Enable/disable automatic opening of Ops window
- **Triggers**: Low confidence or error detection
- **UI**: Settings → Auto-open Operations window

### `opsConfidenceThreshold`
- **Type**: Double
- **Default**: `0.35` (35%)
- **Range**: 0.0 - 0.8 (0% - 80%)
- **Purpose**: Minimum confidence before auto-opening Ops
- **UI**: Settings → Confidence threshold slider

---

## 🧠 Meta-Prompt Display

### `showMetaPanels`
- **Type**: Bool
- **Default**: `true`
- **Purpose**: Show/hide meta-prompt panels below messages
- **UI**: Settings → Show meta-prompt panels

### `metaVoiceSummary`
- **Type**: Bool
- **Default**: `true`
- **Purpose**: Speak meta summary before main response (voice mode)
- **UI**: In-app toggle (future)

---

## 🪟 Window State (Future)

### `ops.window.frame` *(Not yet implemented)*
- **Type**: String (NSRect encoded)
- **Default**: nil (use default size)
- **Purpose**: Restore Ops window position/size
- **Format**: `"{{x,y},{w,h}}"`

### `ops.window.isOpen` *(Not yet implemented)*
- **Type**: Bool
- **Default**: `false`
- **Purpose**: Restore Ops window open state on launch
- **UI**: Automatic

---

## 🔍 Provider/Routing

### `hasCompletedFirstRun`
- **Type**: Bool
- **Default**: `false`
- **Purpose**: Track first-run wizard completion
- **UI**: FirstRunWizardView

---

## 📋 Session State (Not Persisted)

### Auto-Open Guardrails
These are **not** saved to UserDefaults (reset per session):

- `lastAutoOpenAt: Date?` - Last auto-open timestamp
- `autoOpensThisSession: Int` - Count this session
- **Max**: 5 auto-opens per session
- **Debounce**: 5 seconds between opens

---

## 🔧 Access Patterns

### Reading
```swift
@AppStorage("autoOpenOps") private var autoOpenOps = true

// Reads from UserDefaults.standard
let enabled = UserDefaults.standard.bool(forKey: "autoOpenOps")
```

### Writing
```swift
// Via @AppStorage (automatic)
autoOpenOps = false  // Saves immediately

// Via UserDefaults
UserDefaults.standard.set(false, forKey: "autoOpenOps")
```

### Resetting
```swift
// Reset to defaults
UserDefaults.standard.removeObject(forKey: "autoOpenOps")
UserDefaults.standard.removeObject(forKey: "opsConfidenceThreshold")
UserDefaults.standard.removeObject(forKey: "showMetaPanels")

// Or in Settings UI: "Restore Defaults" button
```

---

## 🧪 Testing Keys

### Override for Testing
```swift
// In test setup
UserDefaults.standard.set(false, forKey: "autoOpenOps")
UserDefaults.standard.set(0.80, forKey: "opsConfidenceThreshold")
```

### Reset for Clean Tests
```swift
let keys = [
    "autoOpenOps",
    "opsConfidenceThreshold", 
    "showMetaPanels",
    "metaVoiceSummary",
    "hasCompletedFirstRun"
]
keys.forEach { UserDefaults.standard.removeObject(forKey: $0) }
```

---

## 📊 Key Registry

| Key | Type | Default | Scope | Persists |
|-----|------|---------|-------|----------|
| `autoOpenOps` | Bool | true | User | Yes |
| `opsConfidenceThreshold` | Double | 0.35 | User | Yes |
| `showMetaPanels` | Bool | true | User | Yes |
| `metaVoiceSummary` | Bool | true | User | Yes |
| `hasCompletedFirstRun` | Bool | false | User | Yes |
| `lastAutoOpenAt` | Date | nil | Session | **No** |
| `autoOpensThisSession` | Int | 0 | Session | **No** |

---

## 🔐 Security Notes

- **No sensitive data**: All keys are UI preferences
- **User-scoped**: Per macOS user account
- **Clearable**: Users can reset via Settings
- **No sync**: Does not sync via iCloud (by design)

---

## 🐛 Debugging

### View All Keys
```swift
// In debug console
po UserDefaults.standard.dictionaryRepresentation()
    .filter { $0.key.contains("Ops") || $0.key.contains("meta") }
```

### Monitor Changes
```swift
NotificationCenter.default.addObserver(
    forName: UserDefaults.didChangeNotification,
    object: nil,
    queue: .main
) { _ in
    print("UserDefaults changed")
}
```

---

## 📝 Migration (Future)

If keys change in future versions:

```swift
// Example: Rename key
if let oldValue = UserDefaults.standard.object(forKey: "oldKey") {
    UserDefaults.standard.set(oldValue, forKey: "newKey")
    UserDefaults.standard.removeObject(forKey: "oldKey")
}
```

---

## ✅ Checklist for New Keys

When adding new @AppStorage keys:

- [ ] Document in this file
- [ ] Set sensible default
- [ ] Add to Settings UI (if user-facing)
- [ ] Add to "Restore Defaults" logic
- [ ] Add to test reset helper
- [ ] Update CHANGELOG.md

---

**Maintained By**: Engineering team  
**Last Updated**: October 12, 2025  
**Version**: 0.9.6

