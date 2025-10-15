import SwiftUI
import Foundation

final class ReportStore: ObservableObject {
    static let shared = ReportStore()
    @Published var reports: [String: ReportModel] = [:] // keyed by report_id
    private var seen: [(id: String, at: Date)] = []
    private let horizon: TimeInterval = 60 // ignore duplicates seen within 60s

    private init() {}

    func recentlySaw(_ id: String) -> Bool {
        let now = Date()
        // prune old entries
        seen = seen.filter { now.timeIntervalSince($0.at) < horizon }
        if seen.contains(where: { $0.id == id }) { 
            print("🔇 Recently saw report_id: \(id) - ignoring duplicate")
            return true 
        }
        seen.append((id, now))
        print("✅ New report_id: \(id)")
        return false
    }
    
    func addOrUpdateReport(_ model: ReportModel) {
        reports[model.id] = model
        print("📊 Stored report: \(model.id) - \(model.title)")
    }
    
    func getReport(_ id: String) -> ReportModel? {
        return reports[id]
    }
    
    func getLatestReport() -> ReportModel? {
        return reports.values.sorted { $0.ts > $1.ts }.first
    }
}

struct ReportModel: Identifiable {
    let id: String                 // report_id
    var title: String
    var summary: String
    var body: String
    var ts: Date
    
    init(id: String, title: String, summary: String, body: String, ts: Date) {
        self.id = id
        self.title = title
        self.summary = summary
        self.body = body
        self.ts = ts
    }
}
