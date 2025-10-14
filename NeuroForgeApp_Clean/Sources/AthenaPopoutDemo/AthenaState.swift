import Foundation
import Combine

@MainActor
final class AthenaState: ObservableObject {
    @Published var lastAlert: CriticalAlert?
    @Published var lastCase: TribunalCase?
    @Published var lastEmergency: SystemEmergency?

    func trigger(_ alert: CriticalAlert) {
        lastAlert = alert
        NotificationCenter.default.post(name: .ShowCriticalAlert, object: alert)
    }
    
    func trigger(_ tribunal: TribunalCase) {
        lastCase = tribunal
        NotificationCenter.default.post(name: .ShowTribunalDecision, object: tribunal)
    }
    
    func trigger(_ emergency: SystemEmergency) {
        lastEmergency = emergency
        NotificationCenter.default.post(name: .ShowSystemEmergency, object: emergency)
    }
}

