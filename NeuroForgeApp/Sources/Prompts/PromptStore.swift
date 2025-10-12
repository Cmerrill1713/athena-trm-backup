import Foundation
import os

@MainActor
final class PromptStore: ObservableObject {
    @Published var all: [PromptTemplate] = []
    @Published var query: String = ""

    private let log = Logger(subsystem: "com.neuroforge.app", category: "prompts")

    private var url: URL {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("NeuroForge", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("prompts.json")
    }

    func load() {
        do {
            let data = try Data(contentsOf: url)
            all = try JSONDecoder().decode([PromptTemplate].self, from: data)
        } catch {
            log.debug("No prompts or decode error; seeding defaults. \(error.localizedDescription)")
            seedDefaults()
            save()
        }
    }

    func save() {
        do {
            let data = try JSONEncoder().encode(all)
            try data.write(to: url, options: .atomic)
        } catch {
            log.error("Failed to save prompts: \(error.localizedDescription)")
        }
    }

    func upsert(_ t: PromptTemplate) {
        if let i = all.firstIndex(where: { $0.id == t.id }) {
            all[i] = t
        } else {
            all.append(t)
        }
        save()
    }

    func remove(_ id: UUID) {
        all.removeAll { $0.id == id }
        save()
    }

    var filtered: [PromptTemplate] {
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !q.isEmpty else {
            return all.sorted { $0.title < $1.title }
        }
        return all.filter { $0.title.lowercased().contains(q) ||
                            $0.category.lowercased().contains(q) ||
                            $0.tags.joined(separator: ",").lowercased().contains(q) }
                  .sorted { $0.title < $1.title }
    }

    private func seedDefaults() {
        all = [
            .init(title: "Bug Report", category: "Debug",
                  body: "Describe the bug:\nSteps to reproduce:\nExpected vs actual:\nLogs:\n",
                  tags: ["debug", "qa"]),
            .init(title: "Code Review", category: "Coding",
                  body: "Review this diff for correctness, readability, and risks:\n{{diff}}\n",
                  tags: ["code"]),
            .init(title: "RAG Query", category: "Knowledge",
                  body: "Use the knowledge base to answer:\n{{question}}\nInclude citations.",
                  tags: ["rag"]),
            .init(title: "Scout-Plan-Build", category: "Agentic",
                  body: "Use the scout-plan-build pattern to:\n{{task}}\n\nScout for files, plan the changes, then build and test.",
                  tags: ["agentic", "workflow"]),
            .init(title: "Vision Analysis", category: "Vision",
                  body: "Analyze this image and extract:\n1. Main subject\n2. Key details\n3. Actionable insights\n\nContext: {{context}}",
                  tags: ["vision", "image"])
        ]
    }
}
