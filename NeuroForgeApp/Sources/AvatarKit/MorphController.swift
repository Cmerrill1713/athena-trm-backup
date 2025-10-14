//
//  MorphController.swift
//  AvatarKit - Shared morph logic and state management
//

import Foundation

/// Central controller for avatar morphing logic - shared across platforms
public final class MorphController: ObservableObject {

    // MARK: - Public Properties

    @Published public private(set) var currentStatus: AvatarStatus
    @Published public private(set) var isMorphing = false

    /// Current morph mode based on awareness and hysteresis
    public var currentMode: AvatarMode {
        currentStatus.state
    }

    /// Whether morphing is currently available on this platform
    public var morphingAvailable: Bool {
        MorphFeature.available
    }

    /// Whether morphing is actively enabled
    public var morphingEnabled: Bool {
        MorphFeature.enabled
    }

    // MARK: - Private Properties

    private let baseURL: URL
    private var lastAwarenessLevel: Double = 0.0
    private var morphQueue = DispatchQueue(label: "com.athena.morphcontroller", qos: .userInitiated)

    // MARK: - Initialization

    public init(baseURL: URL = URL(string: "http://localhost:8035")!) {
        self.baseURL = baseURL
        self.currentStatus = AvatarStatus()
    }

    // MARK: - Public Methods

    /// Update awareness level and potentially trigger morphing
    public func updateAwareness(_ level: Double) {
        lastAwarenessLevel = level

        // Only auto-morph if feature is active
        guard MorphFeature.active else { return }

        morphQueue.async { [weak self] in
            self?.evaluateMorphing(awarenessLevel: level)
        }
    }

    /// Manually request a morph to specific mode
    public func requestMorph(to targetMode: AvatarMode) async throws -> Bool {
        guard targetMode != currentMode else { return true }

        // Check if morphing is available
        if targetMode != .ghost && !MorphFeature.active {
            throw MorphError.featureDisabled
        }

        await MainActor.run { isMorphing = true }
        defer { Task { @MainActor in isMorphing = false } }

        do {
            let success = try await performMorph(to: targetMode)
            if success {
                await MainActor.run {
                    currentStatus = AvatarStatus(
                        state: targetMode,
                        identity: currentStatus.identity,
                        awarenessLevel: lastAwarenessLevel,
                        lastUpdated: Date(),
                        healthy: true
                    )
                }
            }
            return success
        } catch {
            await MainActor.run {
                currentStatus.healthy = false
            }
            throw error
        }
    }

    /// Refresh avatar status from backend
    public func refreshStatus() async throws {
        let statusURL = baseURL.appendingPathComponent("v1/avatar/status")
        let (data, response) = try await URLSession.shared.data(from: statusURL)

        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw MorphError.networkError
        }

        let backendStatus = try JSONDecoder().decode(AvatarStatus.self, from: data)

        await MainActor.run {
            currentStatus = backendStatus
        }
    }

    // MARK: - Private Methods

    private func evaluateMorphing(awarenessLevel: Double) {
        let shouldMorph = MorphHysteresis.shouldMorph(from: currentMode, awarenessLevel: awarenessLevel)

        guard shouldMorph else { return }

        let targetMode: AvatarMode = awarenessLevel >= MorphHysteresis.morphAbove ? .photoreal : .ghost

        Task {
            do {
                _ = try await requestMorph(to: targetMode)
            } catch {
                // Log error but don't throw - auto-morphing should be resilient
                print("Auto-morph failed: \(error.localizedDescription)")
            }
        }
    }

    private func performMorph(to targetMode: AvatarMode) async throws -> Bool {
        let morphURL = baseURL.appendingPathComponent("v1/avatar/switch")
        var request = URLRequest(url: morphURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let morphRequest = AvatarMorphRequest(to: targetMode)
        request.httpBody = try JSONEncoder().encode(morphRequest)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw MorphError.networkError
        }

        if (200..<300).contains(httpResponse.statusCode) {
            let morphResponse = try JSONDecoder().decode(AvatarMorphResponse.self, from: data)
            return morphResponse.success
        } else if httpResponse.statusCode == 429 {
            throw MorphError.rateLimited
        } else {
            throw MorphError.serverError(httpResponse.statusCode)
        }
    }
}

// MARK: - Errors

public enum MorphError: LocalizedError {
    case featureDisabled
    case networkError
    case rateLimited
    case serverError(Int)

    public var errorDescription: String? {
        switch self {
        case .featureDisabled:
            return "Morphing feature is disabled"
        case .networkError:
            return "Network connection failed"
        case .rateLimited:
            return "Too many morph requests - please wait"
        case .serverError(let code):
            return "Server error: HTTP \(code)"
        }
    }
}
