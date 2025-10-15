import Foundation

/// Authentication interceptor for mobile avatar API requests
final class AuthInterceptor: NSObject, URLSessionDelegate {

    private let tokenManager = TokenManager.shared

    /// Attach auth headers to avatar requests
    func intercept(request: URLRequest) async throws -> URLRequest {
        var interceptedRequest = request

        // Only intercept avatar endpoints
        guard request.url?.path.hasPrefix("/v1/avatar") == true ||
              request.url?.path.contains("avatar") == true else {
            return request
        }

        // Get valid token
        let token = try await tokenManager.getValidToken()

        // Add authorization header
        interceptedRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        // Add mobile platform identifier
        interceptedRequest.setValue("ios", forHTTPHeaderField: "X-Platform")
        interceptedRequest.setValue(UIDevice.current.systemVersion, forHTTPHeaderField: "X-Platform-Version")

        // Add device ID for rollout cohort tracking
        if let deviceId = await getDeviceId() {
            interceptedRequest.setValue(deviceId, forHTTPHeaderField: "X-Device-ID")
        }

        return interceptedRequest
    }

    private func getDeviceId() async -> String? {
        // Use identifierForVendor for consistent device ID
        return await UIDevice.current.identifierForVendor?.uuidString
    }
}

/// Token manager for mobile authentication
final class TokenManager {

    static let shared = TokenManager()

    private let tokenKey = "athena_mobile_token"
    private let refreshTokenKey = "athena_mobile_refresh_token"
    private let tokenExpiryKey = "athena_mobile_token_expiry"

    private var currentToken: String?
    private var refreshToken: String?
    private var tokenExpiry: Date?

    private let queue = DispatchQueue(label: "com.athena.tokenmanager")

    /// Get a valid (non-expired) token, refreshing if needed
    func getValidToken() async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            queue.async {
                // Check if we have a valid cached token
                if let token = self.currentToken,
                   let expiry = self.tokenExpiry,
                   expiry > Date().addingTimeInterval(300) { // 5 min buffer
                    continuation.resume(returning: token)
                    return
                }

                // Need to refresh or get new token
                Task {
                    do {
                        let newToken = try await self.refreshOrGetNewToken()
                        continuation.resume(returning: newToken)
                    } catch {
                        continuation.resume(throwing: error)
                    }
                }
            }
        }
    }

    private func refreshOrGetNewToken() async throws -> String {
        // Try refresh token first
        if let refreshToken = getStoredRefreshToken() {
            do {
                return try await refreshAccessToken(refreshToken)
            } catch {
                // Refresh failed, fall back to new token
                print("Token refresh failed, getting new token")
            }
        }

        // Get new token
        return try await getNewToken()
    }

    private func getNewToken() async throws -> String {
        // This would typically authenticate with your auth service
        // For now, we'll use a placeholder implementation

        let authURL = URL(string: "https://auth.yourdomain.com/oauth/token")!
        var request = URLRequest(url: authURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // This is where you'd implement device authentication
        // For example: using device certificates, biometric auth, etc.
        let authPayload = [
            "grant_type": "device_auth",
            "device_id": UIDevice.current.identifierForVendor?.uuidString ?? "unknown",
            "scope": "avatar:read avatar:write"
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: authPayload)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw AuthError.invalidResponse
        }

        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)

        // Store tokens
        storeTokens(accessToken: tokenResponse.accessToken,
                   refreshToken: tokenResponse.refreshToken,
                   expiry: Date().addingTimeInterval(TimeInterval(tokenResponse.expiresIn)))

        return tokenResponse.accessToken
    }

    private func refreshAccessToken(_ refreshToken: String) async throws -> String {
        let authURL = URL(string: "https://auth.yourdomain.com/oauth/token")!
        var request = URLRequest(url: authURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let refreshPayload = [
            "grant_type": "refresh_token",
            "refresh_token": refreshToken
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: refreshPayload)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw AuthError.refreshFailed
        }

        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)

        // Store new tokens
        storeTokens(accessToken: tokenResponse.accessToken,
                   refreshToken: tokenResponse.refreshToken,
                   expiry: Date().addingTimeInterval(TimeInterval(tokenResponse.expiresIn)))

        return tokenResponse.accessToken
    }

    private func storeTokens(accessToken: String, refreshToken: String, expiry: Date) {
        UserDefaults.standard.set(accessToken, forKey: tokenKey)
        UserDefaults.standard.set(refreshToken, forKey: refreshTokenKey)
        UserDefaults.standard.set(expiry, forKey: tokenExpiryKey)

        currentToken = accessToken
        self.refreshToken = refreshToken
        tokenExpiry = expiry
    }

    private func getStoredRefreshToken() -> String? {
        UserDefaults.standard.string(forKey: refreshTokenKey)
    }

    /// Clear all stored tokens (logout)
    func clearTokens() {
        UserDefaults.standard.removeObject(forKey: tokenKey)
        UserDefaults.standard.removeObject(forKey: refreshTokenKey)
        UserDefaults.standard.removeObject(forKey: tokenExpiryKey)

        currentToken = nil
        refreshToken = nil
        tokenExpiry = nil
    }
}

/// Token response from auth service
struct TokenResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
    }
}

/// Auth-related errors
enum AuthError: LocalizedError {
    case invalidResponse
    case refreshFailed
    case noToken

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Invalid authentication response"
        case .refreshFailed:
            return "Failed to refresh access token"
        case .noToken:
            return "No valid access token available"
        }
    }
}
