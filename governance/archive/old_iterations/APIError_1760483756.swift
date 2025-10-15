import Foundation

/// API-specific errors mapped from HTTP status codes
public enum APIError: Error, LocalizedError {
    case validation422(message: String?)
    case service503
    case server5xx(code: Int)
    case decoding(Error)
    case transport(Error)
    case invalidResponse

    public var errorDescription: String? {
        switch self {
        case let .validation422(msg):
            msg ?? "Validation error - please check your input"
        case .service503:
            "Service temporarily unavailable - please try again"
        case let .server5xx(code):
            "Server error (\(code)) - please try again later"
        case let .decoding(error):
            "Response decoding failed: \(error.localizedDescription)"
        case let .transport(error):
            "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            "Invalid response from server"
        }
    }

    public var severity: ErrorSeverity {
        switch self {
        case .validation422:
            .info
        case .service503:
            .warning
        case .server5xx, .transport, .invalidResponse:
            .error
        case .decoding:
            .warning
        }
    }
}

public enum ErrorSeverity {
    case info, warning, error
}
