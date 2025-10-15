import SwiftUI

struct LoginView: View {
    @StateObject private var profileManager = ProfileManager()
    @State private var showingAddProfile = false
    @State private var selectedProfileIndex = 0
    @Binding var isLoggedIn: Bool
    @Binding var selectedProfile: UserProfile?
    
    var body: some View {
        VStack(spacing: 32) {
            // Header - clean and modern
            VStack(spacing: 20) {
                // Modern gradient logo
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 80, height: 80)
                    
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 32, weight: .medium))
                        .foregroundColor(.white)
                }
                
                VStack(spacing: 12) {
                    Text("Athena")
                        .font(.system(size: 36, weight: .bold, design: .rounded))
                        .foregroundColor(AppleColors.label)
                    
                    Text("Select or create a profile")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(AppleColors.secondaryLabel)
                }
            }
            .padding(.top, 40)
            
            Spacer()
            
            // Profiles list with vertical slider (macOS compatible)
            HStack(spacing: 16) {
                // Profile cards with vertical navigation
                VStack(spacing: 12) {
                    ForEach(Array(profileManager.profiles.enumerated()), id: \.element.id) { index, profile in
                        ProfileCard(profile: profile) {
                            profileManager.selectProfile(profile)
                            selectedProfile = profile
                            isLoggedIn = true
                        } onDelete: {
                            if profileManager.profiles.count > 1 {
                                profileManager.deleteProfile(profile)
                                if selectedProfileIndex >= profileManager.profiles.count {
                                    selectedProfileIndex = max(0, profileManager.profiles.count - 1)
                                }
                            }
                        }
                        .frame(width: 420)
                        .opacity(selectedProfileIndex == index ? 1.0 : 0.7)
                        .scaleEffect(selectedProfileIndex == index ? 1.0 : 0.95)
                        .animation(.easeInOut(duration: 0.3), value: selectedProfileIndex)
                    }
                }
                .frame(height: 300)
                .clipped()
                .gesture(
                    DragGesture()
                        .onEnded { value in
                            if value.translation.height > 50 && selectedProfileIndex > 0 {
                                withAnimation(.easeInOut(duration: 0.3)) {
                                    selectedProfileIndex -= 1
                                }
                            } else if value.translation.height < -50 && selectedProfileIndex < profileManager.profiles.count - 1 {
                                withAnimation(.easeInOut(duration: 0.3)) {
                                    selectedProfileIndex += 1
                                }
                            }
                        }
                )
                
                // Navigation dots (vertical, only show if more than 1 profile)
                if profileManager.profiles.count > 1 {
                    VStack(spacing: 8) {
                        ForEach(0..<profileManager.profiles.count, id: \.self) { index in
                            Circle()
                                .fill(selectedProfileIndex == index ? AppleColors.systemBlue : AppleColors.systemGray4)
                                .frame(width: 8, height: 8)
                                .scaleEffect(selectedProfileIndex == index ? 1.2 : 1.0)
                                .animation(.easeInOut(duration: 0.2), value: selectedProfileIndex)
                                .onTapGesture {
                                    withAnimation(.easeInOut(duration: 0.3)) {
                                        selectedProfileIndex = index
                                    }
                                }
                        }
                    }
                }
            }
            .frame(maxHeight: 300)
            
            Spacer()
            
            // Add profile button - modern design
            Button(action: { showingAddProfile = true }) {
                HStack(spacing: 12) {
                    Image(systemName: "plus")
                        .font(.system(size: 16, weight: .semibold))
                    Text("Add New Profile")
                        .font(.system(size: 16, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(
                    LinearGradient(
                        colors: [AppleColors.systemBlue, AppleColors.systemGray],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .foregroundColor(.white)
                .cornerRadius(16)
                .shadow(color: AppleColors.systemBlue.opacity(0.3), radius: 8, x: 0, y: 4)
            }
            .buttonStyle(.plain)
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .frame(width: 500, height: 600)
        .sheet(isPresented: $showingAddProfile) {
            AddProfileView(profileManager: profileManager)
        }
    }
}

struct ProfileCard: View {
    let profile: UserProfile
    let onSelect: () -> Void
    let onDelete: () -> Void
    
    @State private var isHovering = false
    
    var body: some View {
        HStack(spacing: 16) {
            // Avatar - show photo if available, otherwise SF Symbol
            Group {
                if let imageData = profile.profileImageData,
                   let nsImage = NSImage(data: imageData) {
                    Image(nsImage: nsImage)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 60, height: 60)
                        .clipShape(Circle())
                } else {
                    Image(systemName: profile.avatar)
                        .font(.system(size: 40, weight: .medium))
                        .foregroundColor(.white)
                        .frame(width: 60, height: 60)
                        .background(
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .shadow(color: AppleColors.systemBlue.opacity(0.3), radius: 4, x: 0, y: 2)
                        )
                }
            }
            
            // Profile info
            VStack(alignment: .leading, spacing: 4) {
                Text(profile.name)
                    .font(.headline)
                
                HStack(spacing: 12) {
                    Label("\(profile.messageCount)", systemImage: "message.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("Last used: \(formatDate(profile.lastUsed))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            // Delete button (only show on hover if more than 1 profile)
            if isHovering {
                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .foregroundColor(.red)
                }
                .buttonStyle(.plain)
                .help("Delete profile")
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(isHovering ? AppleColors.systemBlue.opacity(0.05) : AppleColors.controlBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(AppleColors.systemGray4.opacity(0.3), lineWidth: 1)
                )
                .shadow(color: AppleColors.systemBlue.opacity(0.1), radius: 2, x: 0, y: 1)
        )
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovering = hovering
            }
        }
        .onTapGesture {
            onSelect()
        }
        .help("Select \(profile.name)")
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct AddProfileView: View {
    @ObservedObject var profileManager: ProfileManager
    @Environment(\.dismiss) var dismiss
    
    @State private var profileName = ""
    @State private var selectedAvatar = "person.circle.fill"
    @State private var profileImageData: Data?
    @State private var showingImagePicker = false
    
    let avatarOptions = [
        "person.circle.fill",
        "person.crop.circle.fill",
        "person.crop.square.fill",
        "sparkles",
        "brain.head.profile",
        "star.circle.fill",
        "heart.circle.fill",
        "bolt.circle.fill",
        "flame.fill",
        "leaf.circle.fill",
        "pawprint.circle.fill",
        "globe.americas.fill"
    ]
    
    var body: some View {
        VStack(spacing: 24) {
            Text("Create New Profile")
                .font(.title2)
                .fontWeight(.semibold)
            
            // Profile picture or avatar preview
            VStack(spacing: 12) {
                if let imageData = profileImageData,
                   let nsImage = NSImage(data: imageData) {
                    Image(nsImage: nsImage)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 100, height: 100)
                        .clipShape(Circle())
                        .overlay(Circle().stroke(AppleColors.systemBlue, lineWidth: 3))
                } else {
                    Image(systemName: selectedAvatar)
                        .font(.system(size: 50, weight: .medium))
                        .foregroundColor(.white)
                        .frame(width: 100, height: 100)
                        .background(
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .shadow(color: AppleColors.systemBlue.opacity(0.3), radius: 6, x: 0, y: 3)
                        )
                }
                
                Button(action: { showingImagePicker = true }) {
                    HStack(spacing: 4) {
                        Image(systemName: "photo")
                        Text(profileImageData == nil ? "Add Photo" : "Change Photo")
                    }
                    .font(.caption)
                    .foregroundColor(AppleColors.systemBlue)
                }
                .buttonStyle(.plain)
            }
            
            // Avatar selection
            VStack(alignment: .leading, spacing: 8) {
                Text("Choose Avatar")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 50))], spacing: 12) {
                    ForEach(avatarOptions, id: \.self) { avatar in
                        Button(action: { selectedAvatar = avatar }) {
                            Image(systemName: avatar)
                                .font(.system(size: 28))
                                .foregroundColor(selectedAvatar == avatar ? .white : AppleColors.systemBlue)
                                .frame(width: 50, height: 50)
                                .background(
                                    Circle()
                                        .fill(selectedAvatar == avatar ? 
                                            LinearGradient(
                                                colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            ) :
                                            LinearGradient(
                                                colors: [AppleColors.systemGray5, AppleColors.systemGray6],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .shadow(color: selectedAvatar == avatar ? AppleColors.systemBlue.opacity(0.4) : Color.clear, radius: 3, x: 0, y: 1)
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            
            // Name input
            VStack(alignment: .leading, spacing: 8) {
                Text("Profile Name")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                TextField("Enter name...", text: $profileName)
                    .textFieldStyle(.roundedBorder)
                    .font(.body)
            }
            
            Spacer()
            
            // Buttons
            HStack(spacing: 12) {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.escape)
                
                Button("Create Profile") {
                    if !profileName.isEmpty {
                        profileManager.createProfile(name: profileName, avatar: selectedAvatar, profileImageData: profileImageData)
                        dismiss()
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(profileName.isEmpty)
                .keyboardShortcut(.return)
            }
        }
        .padding(30)
        .frame(width: 400, height: 550)
        .sheet(isPresented: $showingImagePicker) {
            ProfileImagePicker(isPresented: $showingImagePicker) { imageData in
                profileImageData = imageData
            }
        }
    }
}

// Profile Image Picker with proper scaling
struct ProfileImagePicker: NSViewRepresentable {
    @Binding var isPresented: Bool
    var onImagePicked: (Data) -> Void
    
    func makeNSView(context: Context) -> NSView {
        return NSView()
    }
    
    func updateNSView(_ nsView: NSView, context: Context) {
        DispatchQueue.main.async {
            if isPresented {
                presentImagePicker()
                isPresented = false
            }
        }
    }
    
    private func presentImagePicker() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.jpeg, .png, .heic, .gif]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.message = "Choose a profile picture"
        
        if panel.runModal() == .OK, let url = panel.url {
            do {
                let imageData = try Data(contentsOf: url)
                if let nsImage = NSImage(data: imageData) {
                    // Scale image to 200x200 for profile use
                    let scaledData = scaleImageData(nsImage, maxSize: 200)
                    onImagePicked(scaledData)
                }
            } catch {
                print("Error loading image: \(error.localizedDescription)")
            }
        }
    }
    
    private func scaleImageData(_ image: NSImage, maxSize: CGFloat) -> Data {
        let size = image.size
        let aspectRatio = size.width / size.height
        
        var newSize: NSSize
        if size.width > size.height {
            newSize = NSSize(width: maxSize, height: maxSize / aspectRatio)
        } else {
            newSize = NSSize(width: maxSize * aspectRatio, height: maxSize)
        }
        
        let scaledImage = NSImage(size: newSize)
        scaledImage.lockFocus()
        image.draw(in: NSRect(origin: .zero, size: newSize))
        scaledImage.unlockFocus()
        
        // Convert to JPEG data (compressed)
        if let tiffData = scaledImage.tiffRepresentation,
           let bitmapImage = NSBitmapImageRep(data: tiffData),
           let jpegData = bitmapImage.representation(using: .jpeg, properties: [.compressionFactor: 0.8]) {
            return jpegData
        }
        
        // Fallback to original data
        return image.tiffRepresentation ?? Data()
    }
}

#Preview {
    LoginView(isLoggedIn: .constant(false), selectedProfile: .constant(nil))
}

