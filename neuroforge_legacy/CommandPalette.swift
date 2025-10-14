import SwiftUI

struct CommandPalette: View {
    @Binding var isPresented: Bool
    @State private var searchText = ""
    @State private var selectedAction: Action? = nil
    
    let actions: [Action] = [
        Action(title: "Check Service Health", icon: "heart.fill", action: .checkHealth),
        Action(title: "Query RAG", icon: "brain.head.profile", action: .queryRAG),
        Action(title: "Describe Image", icon: "eye.fill", action: .describeImage),
        Action(title: "Validate Platform", icon: "checkmark.shield.fill", action: .validatePlatform),
        Action(title: "View Operations", icon: "gearshape.fill", action: .viewOperations)
    ]
    
    var filteredActions: [Action] {
        if searchText.isEmpty {
            return actions
        } else {
            return actions.filter { $0.title.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                
                TextField("Search commands...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .onSubmit {
                        if let first = filteredActions.first {
                            selectedAction = first
                        }
                    }
                
                Button("Cancel") {
                    isPresented = false
                }
                .keyboardShortcut(.escape)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Actions list
            List(filteredActions, id: \.title) { action in
                ActionRow(action: action)
                    .onTapGesture {
                        selectedAction = action
                        performAction(action.action)
                    }
            }
            .listStyle(PlainListStyle())
        }
        .frame(width: 400, height: 300)
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(8)
        .shadow(radius: 10)
        .onAppear {
            searchText = ""
        }
    }
    
    private func performAction(_ action: ActionType) {
        switch action {
        case .checkHealth:
            NotificationCenter.default.post(name: .checkServiceHealth, object: nil)
        case .queryRAG:
            NotificationCenter.default.post(name: .queryRAG, object: nil)
        case .describeImage:
            NotificationCenter.default.post(name: .describeImage, object: nil)
        case .validatePlatform:
            NotificationCenter.default.post(name: .validatePlatform, object: nil)
        case .viewOperations:
            NotificationCenter.default.post(name: .viewOperations, object: nil)
        }
        
        isPresented = false
    }
}

struct ActionRow: View {
    let action: Action
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: action.icon)
                .foregroundColor(.blue)
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(action.title)
                    .font(.system(size: 14, weight: .medium))
                
                Text(actionDescription)
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
    }
    
    private var actionDescription: String {
        switch action.action {
        case .checkHealth:
            return "Check status of all services"
        case .queryRAG:
            return "Search knowledge base"
        case .describeImage:
            return "Analyze image content"
        case .validatePlatform:
            return "Run platform validation"
        case .viewOperations:
            return "Open operations window"
        }
    }
}

struct Action {
    let title: String
    let icon: String
    let action: ActionType
}

enum ActionType {
    case checkHealth
    case queryRAG
    case describeImage
    case validatePlatform
    case viewOperations
}

// Notification names
extension Notification.Name {
    static let checkServiceHealth = Notification.Name("checkServiceHealth")
    static let queryRAG = Notification.Name("queryRAG")
    static let describeImage = Notification.Name("describeImage")
    static let validatePlatform = Notification.Name("validatePlatform")
    static let viewOperations = Notification.Name("viewOperations")
}

#Preview {
    CommandPalette(isPresented: .constant(true))
}
