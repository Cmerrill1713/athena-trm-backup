import Foundation

enum APIError: LocalizedError {
    case badStatus(Int, Data)
    case decode
    case offline
    case other(Error)

    var errorDescription: String? {
        switch self {
        case .badStatus(let c, _): return "Server returned \(c)"
        case .decode: return "Failed to decode response"
        case .offline: return "Backend unavailable"
        case .other(let e): return e.localizedDescription
        }
    }
}
