import SwiftUI

struct PromptSidebar: View {
    @ObservedObject var store: PromptStore
    let onInsert: (String) -> Void

    @State private var showEditor = false
    @State private var selected: PromptTemplate? = nil
    @State private var varValues: [String: String] = [:]
    @State private var showVarsSheet = false

    var body: some View {
        VStack(spacing: 8) {
            // Search + Add button
            HStack {
                TextField("Search templates…", text: $store.query)
                    .textFieldStyle(.roundedBorder)
                    .accessibilityIdentifier("prompt_search")

                Button {
                    selected = .init(title: "New Template", category: "Custom", body: "", tags: [])
                    showEditor = true
                } label: {
                    Image(systemName: "plus")
                }
                .help("New template")
            }
            .padding(.horizontal, 8)
            .padding(.top, 8)

            // Template list
            List(store.filtered, id: \.id, selection: $selected) { t in
                VStack(alignment: .leading, spacing: 2) {
                    Text(t.title).font(.headline)
                    HStack(spacing: 6) {
                        Text(t.category).foregroundStyle(.secondary)
                        if !t.tags.isEmpty {
                            Text(t.tags.joined(separator: ", ")).foregroundStyle(.tertiary)
                        }
                    }
                    .font(.caption)
                }
                .contentShape(Rectangle())
                .onTapGesture(count: 2) { prepareInsert(t) }
                .accessibilityIdentifier("prompt_item_\(t.title)")
            }
            .listStyle(.inset)
            .accessibilityIdentifier("prompt_list")

            // Actions
            HStack {
                Button("Insert (↩︎)") {
                    if let t = selected { prepareInsert(t) }
                }
                .keyboardShortcut(.return)
                .disabled(selected == nil)

                Spacer()

                Button("Edit") {
                    showEditor = true
                }
                .disabled(selected == nil)

                Button(role: .destructive) {
                    if let id = selected?.id {
                        store.remove(id)
                        selected = nil
                    }
                } label: {
                    Image(systemName: "trash")
                }
                .disabled(selected == nil)
            }
            .padding(8)
        }
        .frame(minWidth: 280, idealWidth: 320)
        .sheet(isPresented: $showVarsSheet) {
            VariableFillSheet(keys: selected?.variableKeys ?? [], values: $varValues) {
                if let t = selected {
                    onInsert(t.filled(with: varValues))
                }
                varValues.removeAll()
                showVarsSheet = false
            }
        }
        .sheet(isPresented: $showEditor) {
            if let t = selected {
                PromptEditor(template: t) { updated in
                    store.upsert(updated)
                    selected = updated
                    showEditor = false
                }
            }
        }
        .onAppear {
            if store.all.isEmpty { store.load() }
        }
        .accessibilityIdentifier("prompt_sidebar")
    }

    private func prepareInsert(_ t: PromptTemplate) {
        selected = t
        let keys = t.variableKeys
        if keys.isEmpty {
            onInsert(t.body)
        } else {
            varValues = Dictionary(uniqueKeysWithValues: keys.map { ($0, "") })
            showVarsSheet = true
        }
    }
}

// MARK: - Variable Fill Sheet

private struct VariableFillSheet: View {
    let keys: [String]
    @Binding var values: [String: String]
    let onDone: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Fill Variables").font(.title2).bold()

            ForEach(keys, id: \.self) { k in
                HStack {
                    Text(k)
                        .frame(width: 140, alignment: .trailing)
                        .foregroundStyle(.secondary)

                    TextField("Enter \(k)…", text: Binding(
                        get: { values[k] ?? "" },
                        set: { values[k] = $0 }
                    ))
                    .textFieldStyle(.roundedBorder)
                }
            }

            HStack {
                Spacer()
                Button("Insert") { onDone() }
                    .keyboardShortcut(.return)
            }
        }
        .padding(24)
        .frame(width: 520)
    }
}

// MARK: - Prompt Editor

private struct PromptEditor: View {
    @State var template: PromptTemplate
    let onSave: (PromptTemplate) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Template").font(.title2).bold()

            TextField("Title", text: $template.title)
                .textFieldStyle(.roundedBorder)

            TextField("Category", text: $template.category)
                .textFieldStyle(.roundedBorder)

            TextField("Tags (comma-separated)", text: Binding(
                get: { template.tags.joined(separator: ", ") },
                set: { template.tags = $0.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) } }
            ))
            .textFieldStyle(.roundedBorder)

            TextEditor(text: $template.body)
                .font(.system(.body, design: .monospaced))
                .frame(minHeight: 180)
                .overlay(RoundedRectangle(cornerRadius: 6).strokeBorder(.quaternary))

            HStack {
                Spacer()
                Button("Save") { onSave(template) }
                    .keyboardShortcut(.return)
            }
        }
        .padding(24)
        .frame(width: 640)
    }
}
