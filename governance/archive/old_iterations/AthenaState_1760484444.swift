import Combine
import Foundation

@MainActor
final class AthenaState: ObservableObject {
    @Published var lastAlert: CriticalAlert?
    @Published var lastCase: TribunalCase?
    @Published var lastEmergency: SystemEmergency?

    func trigger(_ alert: CriticalAlert) {
        self.lastAlert = alert
        NotificationCenter.default.post(name: .ShowCriticalAlert, object: alert)
    }

    func trigger(_ tribunal: TribunalCase) {
        self.lastCase = tribunal
        NotificationCenter.default.post(name: .ShowTribunalDecision, object: tribunal)
    }

    func trigger(_ emergency: SystemEmergency) {
        self.lastEmergency = emergency
        NotificationCenter.default.post(name: .ShowSystemEmergency, object: emergency)
    }
}
