# Xcode Build Hygiene Checklist

## Stop Swift Build Regressions

Run these checks once to eliminate duplicate symbols, focus issues, and preview conflicts:

---

## 1. Clean Duplicate Files

### In Xcode Navigator:
1. Select your target → **Build Phases** → **Compile Sources**
2. Look for duplicate filenames (e.g., two `ChatView.swift`)
3. Remove duplicates - keep only one source of truth
4. If you see files you deleted still listed, remove them

### Common Duplicates to Check:
- `ChatView.swift` (UI vs old version)
- `VoiceManager.swift` (multiple implementations)
- `main.swift` or other files with `@main`
- Model files (e.g., `AlertModel.swift` in multiple places)

---

## 2. Fix Multiple @main Entry Points

### Rule: Only ONE @main in entire app

Find all `@main` declarations:
```bash
grep -r "@main" NeuroForgeApp/
```

**Keep only one** - usually in `main.swift` or your primary App struct:
```swift
@main
struct AthenaApp: App {
    var body: some Scene {
        // ...
    }
}
```

**Delete `@main` from** all other files.

---

## 3. Check Target Membership

For each file in your project:

1. Select file in Navigator
2. Open **File Inspector** (right sidebar)
3. Under **Target Membership**:
   - ✅ Check your **app target** (e.g., NeuroForgeApp)
   - ❌ Uncheck **test targets** (unless it's a test file)
   - ❌ Uncheck **preview targets** (unless it's a preview helper)

---

## 4. Guard Preview Code

Wrap ALL `PreviewProvider` structs:

```swift
#if DEBUG && canImport(SwiftUI)
struct MyView_Previews: PreviewProvider {
    static var previews: some View {
        MyView()
    }
}
#endif
```

This prevents preview code from being compiled into release builds.

---

## 5. Fix VoiceManager Duplicates

### Problem: Multiple `VoiceManager` implementations cause symbol conflicts

### Solution: Protocol + Single Implementation

**Create one VoiceManager.swift:**
```swift
import AVFoundation

protocol VoiceService {
    func speak(_ text: String)
    func stop()
}

final class VoiceManager: VoiceService {
    private let synthesizer = AVSpeechSynthesizer()
    
    func speak(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        synthesizer.speak(utterance)
    }
    
    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
    }
}
```

**Use environment injection everywhere else:**
```swift
// Define environment key
private struct VoiceServiceKey: EnvironmentKey {
    static let defaultValue: VoiceService = VoiceManager()
}

extension EnvironmentValues {
    var voice: VoiceService {
        get { self[VoiceServiceKey.self] }
        set { self[VoiceServiceKey.self] = newValue }
    }
}

// Use in views
struct MyView: View {
    @Environment(\.voice) var voice
    
    var body: some View {
        Button("Speak") {
            voice.speak("Hello")
        }
    }
}
```

**For previews, inject a mock:**
```swift
#if DEBUG
struct MockVoiceService: VoiceService {
    func speak(_ text: String) { print("Mock: \(text)") }
    func stop() { }
}
#endif

#if DEBUG && canImport(SwiftUI)
struct MyView_Previews: PreviewProvider {
    static var previews: some View {
        MyView()
            .environment(\.voice, MockVoiceService())
    }
}
#endif
```

---

## 6. Remove Old Shims

If you have files named:
- `*Shim.swift`
- `*Temp.swift`
- `*Old.swift`
- `*Backup.swift`

**Delete them** or ensure they're not in **Compile Sources**.

---

## 7. Fix Import Conflicts

If you have custom types (e.g., `Alert`), ensure they don't conflict with SwiftUI:

```swift
// BAD: Conflicts with SwiftUI.Alert
struct Alert {
    var message: String
}

// GOOD: Use namespace or rename
struct AthenaAlert {
    var message: String
}

// Or use explicit module name
typealias SwiftUIAlert = SwiftUI.Alert
```

---

## 8. Verify Clean Build

After fixes:

```bash
# Clean build folder
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Build from command line
xcodebuild -scheme NeuroForgeApp -configuration Debug clean build
```

Should complete with **BUILD SUCCEEDED** and no duplicate symbol warnings.

---

## 9. Lock It In

Once clean:

```bash
git add .
git commit -m "fix: Xcode hygiene - remove duplicates, one @main, guard previews"
git push
```

---

## Quick Reference Commands

```bash
# Find duplicate @main
grep -r "@main" NeuroForgeApp/

# Find all PreviewProvider (should be guarded)
grep -r "PreviewProvider" NeuroForgeApp/

# Find files in Compile Sources
xcodebuild -showBuildSettings -scheme NeuroForgeApp | grep SOURCES_ROOT

# Clean derived data
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Build debug
bash scripts/xcode_build_debug.sh
```

---

## Checklist Summary

- [ ] Remove duplicate files from Compile Sources
- [ ] Only one `@main` in entire app
- [ ] Check Target Membership for all files
- [ ] Guard all PreviewProvider with `#if DEBUG`
- [ ] Single VoiceManager with protocol injection
- [ ] Remove old shim files
- [ ] Fix type name conflicts (Alert, etc.)
- [ ] Verify clean build succeeds
- [ ] Commit changes

