# 🍎 Pure Apple Native UI/UX Plan for NeuroForge

## 🎯 Apple-First Design Philosophy

Following Apple's Human Interface Guidelines (HIG) - no Microsoft, no cross-platform compromises. Pure macOS native design.

### **Apple System Colors (Native Only)**
```swift
struct AppleNativeColors {
    // Primary Apple System Colors
    static let systemBlue = Color(.systemBlue)           // Apple's signature blue
    static let systemGray = Color(.systemGray)           // Native gray
    static let systemGray2 = Color(.systemGray2)         // Lighter gray
    static let systemGray3 = Color(.systemGray3)         // Even lighter
    static let systemGray4 = Color(.systemGray4)         // Lightest gray
    static let systemGray5 = Color(.systemGray5)         // Almost white
    static let systemGray6 = Color(.systemGray6)         // White gray

    // Apple Semantic Colors
    static let label = Color(.labelColor)                // Primary text
    static let secondaryLabel = Color(.secondaryLabelColor)
    static let tertiaryLabel = Color(.tertiaryLabelColor)
    static let quaternaryLabel = Color(.quaternaryLabelColor)

    // Apple Background Colors
    static let controlBackground = Color(.controlBackgroundColor)
    static let textBackground = Color(.textBackgroundColor)
    static let windowBackground = Color(.windowBackgroundColor)
    static let underPageBackground = Color(.underPageBackgroundColor)

    // Apple Status Colors
    static let systemGreen = Color(.systemGreen)         // Success
    static let systemOrange = Color(.systemOrange)       // Warning
    static let systemRed = Color(.systemRed)             // Error
    static let systemYellow = Color(.systemYellow)       // Caution

    // Apple Accent (User's chosen accent color)
    static let accent = Color.accentColor               // Respects user preference
}
```

## 🍎 Apple Design Principles

### **1. Native macOS Components Only**
- **SF Symbols** for all icons (no custom icons)
- **Native button styles** (.bordered, .borderedProminent)
- **System fonts** (San Francisco family)
- **Native color system** (adapts to user's settings)
- **Vibrancy effects** where appropriate

### **2. Apple Messages Inspiration**
```swift
struct AppleMessagesStyle {
    // Bubble styling like native Messages
    static let userBubble = Color(.systemBlue)
    static let otherBubble = Color(.controlBackgroundColor)
    static let bubbleCornerRadius: CGFloat = 18
    static let bubbleShadow = Color.black.opacity(0.1)

    // Typography like Messages
    static let messageFont = Font.system(size: 15, weight: .regular)
    static let timestampFont = Font.system(size: 12, weight: .regular)
    static let nameFont = Font.system(size: 14, weight: .medium)
}
```

### **3. Pure Apple Layout Patterns**
- **Sidebar + Detail** (like Finder, Mail)
- **Toolbar with SF Symbols** (like Safari, Xcode)
- **Native split view** when needed
- **Standard macOS spacing** (8pt grid system)

## 🎨 Apple-Native Component Designs

### **1. Apple-Style MessageBubble**
```swift
struct AppleMessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.isUser {
                Spacer()
            }

            VStack(alignment: message.isUser ? .trailing : .leading, spacing: 4) {
                Text(message.text)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(message.isUser ? .white : .label)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 18)
                            .fill(message.isUser ?
                                AppleNativeColors.systemBlue :
                                AppleNativeColors.controlBackground
                            )
                            .shadow(
                                color: AppleMessagesStyle.bubbleShadow,
                                radius: 1,
                                x: 0,
                                y: 1
                            )
                    )

                Text(formatTime(message.timestamp))
                    .font(.system(size: 12, weight: .regular))
                    .foregroundColor(.secondaryLabel)
            }
            .frame(maxWidth: 280, alignment: message.isUser ? .trailing : .leading)

            if !message.isUser {
                Spacer()
            }
        }
    }
}
```

### **2. Apple-Style Sidebar (Like Mail.app)**
```swift
struct AppleSidebar: View {
    var body: some View {
        VStack(spacing: 0) {
            // Native toolbar
            HStack {
                Text("NeuroForge")
                    .font(.title2.weight(.semibold))
                    .foregroundColor(.label)

                Spacer()

                Button(action: {}) {
                    Image(systemName: "plus")
                        .font(.system(size: 16, weight: .medium))
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
            .padding()

            Divider()

            // Native search field
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondaryLabel)
                    .font(.system(size: 14))

                TextField("Search", text: .constant(""))
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(AppleNativeColors.textBackground)
            )
            .padding(.horizontal)
            .padding(.bottom, 8)

            // Contact list with native styling
            List(contacts) { contact in
                AppleContactRow(contact: contact)
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
            }
            .listStyle(.sidebar)
        }
        .frame(width: 280)
        .background(AppleNativeColors.windowBackground)
    }
}
```

### **3. Apple-Style Contact Row**
```swift
struct AppleContactRow: View {
    let contact: Contact

    var body: some View {
        HStack(spacing: 12) {
            // Native avatar styling
            ZStack {
                Circle()
                    .fill(AppleNativeColors.systemGray5)
                    .frame(width: 44, height: 44)

                Image(systemName: contact.avatar)
                    .font(.system(size: 20, weight: .medium))
                    .foregroundColor(AppleNativeColors.systemBlue)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(contact.name)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.label)

                HStack(spacing: 4) {
                    Circle()
                        .fill(contact.isOnline ?
                            AppleNativeColors.systemGreen :
                            AppleNativeColors.systemGray4
                        )
                        .frame(width: 6, height: 6)

                    Text(contact.isOnline ? "Online" : "Away")
                        .font(.system(size: 12, weight: .regular))
                        .foregroundColor(.secondaryLabel)
                }
            }

            Spacer()

            if contact.messageCount > 0 {
                Text("\(contact.messageCount)")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        Capsule()
                            .fill(AppleNativeColors.systemBlue)
                    )
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.clear)
        )
        .contentShape(Rectangle())
    }
}
```

### **4. Apple-Style Chat Input**
```swift
struct AppleChatInput: View {
    @Binding var text: String

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            // Native attachment button
            Button(action: {}) {
                Image(systemName: "paperclip")
                    .font(.system(size: 16, weight: .medium))
            }
            .buttonStyle(.bordered)
            .controlSize(.small)

            // Native text input
            HStack(alignment: .bottom, spacing: 8) {
                TextEditor(text: $text)
                    .font(.system(size: 15, weight: .regular))
                    .frame(minHeight: 20, maxHeight: 100)
                    .scrollContentBackground(.hidden)
                    .background(Color.clear)

                // Native send button
                Button(action: sendMessage) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                }
                .buttonStyle(.plain)
                .disabled(text.isEmpty)
                .foregroundColor(text.isEmpty ?
                    AppleNativeColors.systemGray4 :
                    AppleNativeColors.systemBlue
                )
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(AppleNativeColors.textBackground)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(AppleNativeColors.systemGray4, lineWidth: 1)
                    )
            )

            // Native mic button
            Button(action: {}) {
                Image(systemName: "mic")
                    .font(.system(size: 16, weight: .medium))
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(AppleNativeColors.windowBackground)
    }
}
```

## 🍎 Apple-Native Features

### **1. SF Symbols Throughout**
```swift
// All icons use SF Symbols
Image(systemName: "message.fill")          // Chat
Image(systemName: "person.circle")         // User
Image(systemName: "brain.head.profile")    // AI
Image(systemName: "gear")                  // Settings
Image(systemName: "magnifyingglass")       // Search
Image(systemName: "plus")                  // Add
Image(systemName: "paperclip")             // Attach
Image(systemName: "mic")                   // Voice
Image(systemName: "camera")                // Photo
```

### **2. Native Button Styles**
```swift
// Apple's native button styles
Button("Send") { }
    .buttonStyle(.borderedProminent)       // Primary actions

Button("Cancel") { }
    .buttonStyle(.bordered)                // Secondary actions

Button("Delete") { }
    .buttonStyle(.plain)                   // Destructive actions
```

### **3. Native Typography Scale**
```swift
struct AppleTypography {
    static let largeTitle = Font.largeTitle
    static let title = Font.title
    static let title2 = Font.title2
    static let title3 = Font.title3
    static let headline = Font.headline
    static let body = Font.body
    static let callout = Font.callout
    static let subheadline = Font.subheadline
    static let footnote = Font.footnote
    static let caption = Font.caption
    static let caption2 = Font.caption2
}
```

### **4. Native Spacing System**
```swift
struct AppleSpacing {
    static let xs: CGFloat = 4    // 4pt
    static let sm: CGFloat = 8    // 8pt
    static let md: CGFloat = 16   // 16pt
    static let lg: CGFloat = 24   // 24pt
    static let xl: CGFloat = 32   // 32pt
}
```

## 🍎 Apple-Native Window Configuration

### **Updated main.swift**
```swift
var body: some Scene {
    WindowGroup {
        productionInterface
            .environmentObject(errorCenter)
            // ... overlays ...
    }
    .defaultSize(width: 1000, height: 700)
    .windowStyle(.automatic)                    // Native macOS window
    .windowToolbarStyle(.unified)               // Unified toolbar
    .windowResizability(.contentSize)           // Native resizing
    .commands {
        // Native menu commands
        CommandGroup(replacing: .appInfo) {
            Button("About NeuroForge") {
                // Native about dialog
            }
        }

        CommandGroup(after: .appInfo) {
            Button("Preferences...") {
                // Native preferences window
            }
            .keyboardShortcut(",", modifiers: [.command])
        }
    }
}
```

## 🎯 Result: Pure Apple Experience

This design will give you:
- **100% Apple native** - No cross-platform compromises
- **HIG compliant** - Follows all Apple guidelines
- **System integration** - Respects user's color preferences
- **Native performance** - Uses system components
- **Familiar UX** - Behaves like other Mac apps

The app will feel like it was built by Apple themselves! 🍎✨
