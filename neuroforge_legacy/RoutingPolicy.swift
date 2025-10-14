import Foundation

/// Routing policy for intelligent model selection based on confidence, domain, and cost
struct RoutingPolicy: Codable {
    let version: String
    let strategy: String
    let thresholds: Thresholds
    let escalateIf: [EscalationRule]
    let domainModels: [String: DomainModel]
    let fallback: FallbackConfig
    let trm: TRMConfig
    let rag: RAGConfig
    let tools: ToolsConfig
    let schemaEnforcement: SchemaEnforcement
    let session: SessionConfig
    let evaluation: EvaluationConfig
    let learning: LearningConfig
    let safety: SafetyConfig
    let cost: CostConfig

    enum CodingKeys: String, CodingKey {
        case version, strategy, thresholds
        case escalateIf = "escalate_if"
        case domainModels = "domain_models"
        case fallback, trm, rag, tools
        case schemaEnforcement = "schema_enforcement"
        case session, evaluation, learning, safety, cost
    }
}

struct Thresholds: Codable {
    let highConfidence: Double
    let mediumConfidence: Double
    let lowConfidence: Double

    enum CodingKeys: String, CodingKey {
        case highConfidence = "high_confidence"
        case mediumConfidence = "medium_confidence"
        case lowConfidence = "low_confidence"
    }
}

struct EscalationRule: Codable {
    let condition: String
    let afterAttempts: Int
    let target: String
    let reason: String?

    enum CodingKeys: String, CodingKey {
        case condition
        case afterAttempts = "after_attempts"
        case target, reason
    }
}

struct DomainModel: Codable {
    let primary: String
    let fallback: String
    let tools: [String]
}

struct FallbackConfig: Codable {
    let target: String
    let budgetPerHourUSD: Double
    let maxTokensPerRequest: Int
    let alertOnOverage: Bool

    enum CodingKeys: String, CodingKey {
        case target
        case budgetPerHourUSD = "budget_per_hour_usd"
        case maxTokensPerRequest = "max_tokens_per_request"
        case alertOnOverage = "alert_on_overage"
    }
}

struct TRMConfig: Codable {
    let maxDepth: Int
    let toolsEnabled: Bool
    let critiqueEnabled: Bool
    let planFormat: String
    let artifactStorage: String

    enum CodingKeys: String, CodingKey {
        case maxDepth = "max_depth"
        case toolsEnabled = "tools_enabled"
        case critiqueEnabled = "critique_enabled"
        case planFormat = "plan_format"
        case artifactStorage = "artifact_storage"
    }
}

struct RAGConfig: Codable {
    let mode: String
    let topK: Int
    let rerank: Bool
    let rerankModel: String
    let maxPassages: Int
    let requireCitations: Bool
    let freshnessBoostDays: Int

    enum CodingKeys: String, CodingKey {
        case mode
        case topK = "top_k"
        case rerank
        case rerankModel = "rerank_model"
        case maxPassages = "max_passages"
        case requireCitations = "require_citations"
        case freshnessBoostDays = "freshness_boost_days"
    }
}

struct ToolsConfig: Codable {
    let timeoutSeconds: Int
    let maxRetries: Int
    let aclMode: String
    let safeCommands: [String]

    enum CodingKeys: String, CodingKey {
        case timeoutSeconds = "timeout_seconds"
        case maxRetries = "max_retries"
        case aclMode = "acl_mode"
        case safeCommands = "safe_commands"
    }
}

struct SchemaEnforcement: Codable {
    let enabled: Bool
    let rejectInvalid: Bool
    let repairAttempts: Int

    enum CodingKeys: String, CodingKey {
        case enabled
        case rejectInvalid = "reject_invalid"
        case repairAttempts = "repair_attempts"
    }
}

struct SessionConfig: Codable {
    let cacheEnabled: Bool
    let cacheTTLSeconds: Int
    let cacheKeyFields: [String]
    let kvReuse: Bool

    enum CodingKeys: String, CodingKey {
        case cacheEnabled = "cache_enabled"
        case cacheTTLSeconds = "cache_ttl_seconds"
        case cacheKeyFields = "cache_key_fields"
        case kvReuse = "kv_reuse"
    }
}

struct EvaluationConfig: Codable {
    let enabled: Bool
    let goldenSetPath: String
    let metrics: [String]
    let nightlyRun: Bool
    let alertOnRegression: Bool

    enum CodingKeys: String, CodingKey {
        case enabled
        case goldenSetPath = "golden_set_path"
        case metrics
        case nightlyRun = "nightly_run"
        case alertOnRegression = "alert_on_regression"
    }
}

struct LearningConfig: Codable {
    let enabled: Bool
    let captureRedTurns: Bool
    let trainingSink: String
    let distillationSchedule: String

    enum CodingKeys: String, CodingKey {
        case enabled
        case captureRedTurns = "capture_red_turns"
        case trainingSink = "training_sink"
        case distillationSchedule = "distillation_schedule"
    }
}

struct SafetyConfig: Codable {
    let canaryTasksPath: String
    let runFrequency: String
    let alertOnFailure: Bool

    enum CodingKeys: String, CodingKey {
        case canaryTasksPath = "canary_tasks_path"
        case runFrequency = "run_frequency"
        case alertOnFailure = "alert_on_failure"
    }
}

struct CostConfig: Codable {
    let trackPerRoute: Bool
    let alertThresholdUSD: Double
    let exportTo: String

    enum CodingKeys: String, CodingKey {
        case trackPerRoute = "track_per_route"
        case alertThresholdUSD = "alert_threshold_usd"
        case exportTo = "export_to"
    }
}

// MARK: - Policy Loader

enum RoutingPolicyLoader {
    static func load(from path: String = "config/routing_policy.yaml") -> RoutingPolicy? {
        guard let url = URL(string: path) ?? URL(fileURLWithPath: path) as URL?,
              let _ = try? Data(contentsOf: url) else {
            print("[RoutingPolicy] Failed to load from \(path)")
            return nil
        }

        // Use a YAML parser if available, or JSON fallback
        // For now, returning nil - backend will parse YAML
        return nil
    }

    static func loadDefaults() -> RoutingPolicy {
        // Hardcoded defaults matching YAML
        return RoutingPolicy(
            version: "1.0.0",
            strategy: "confidence_tiered",
            thresholds: Thresholds(
                highConfidence: 0.75,
                mediumConfidence: 0.45,
                lowConfidence: 0.45
            ),
            escalateIf: [],
            domainModels: [:],
            fallback: FallbackConfig(
                target: "frontier:gpt4o-mini",
                budgetPerHourUSD: 2.0,
                maxTokensPerRequest: 4096,
                alertOnOverage: true
            ),
            trm: TRMConfig(
                maxDepth: 5,
                toolsEnabled: true,
                critiqueEnabled: true,
                planFormat: "numbered_steps",
                artifactStorage: "redis"
            ),
            rag: RAGConfig(
                mode: "hybrid",
                topK: 5,
                rerank: true,
                rerankModel: "bge-reranker-base",
                maxPassages: 3,
                requireCitations: true,
                freshnessBoostDays: 30
            ),
            tools: ToolsConfig(
                timeoutSeconds: 10,
                maxRetries: 2,
                aclMode: "whitelist",
                safeCommands: ["grep", "curl", "jq", "pytest"]
            ),
            schemaEnforcement: SchemaEnforcement(
                enabled: true,
                rejectInvalid: true,
                repairAttempts: 1
            ),
            session: SessionConfig(
                cacheEnabled: true,
                cacheTTLSeconds: 3600,
                cacheKeyFields: ["norm_query", "doc_version", "route"],
                kvReuse: true
            ),
            evaluation: EvaluationConfig(
                enabled: true,
                goldenSetPath: "eval/golden_tasks.jsonl",
                metrics: ["task_success_rate", "latency_p50", "cost_per_1k"],
                nightlyRun: true,
                alertOnRegression: true
            ),
            learning: LearningConfig(
                enabled: true,
                captureRedTurns: true,
                trainingSink: "training/accepted/",
                distillationSchedule: "weekly"
            ),
            safety: SafetyConfig(
                canaryTasksPath: "eval/canaries.jsonl",
                runFrequency: "hourly",
                alertOnFailure: true
            ),
            cost: CostConfig(
                trackPerRoute: true,
                alertThresholdUSD: 10.0,
                exportTo: "prometheus"
            )
        )
    }
}

// MARK: - Route Decision Logic

struct RouteDecision {
    let model: String
    let route: String
    let useTools: Bool
    let useTRM: Bool
    let escalated: Bool
    let reason: String

    static func decide(
        confidence: Double?,
        domain: String,
        attemptNumber: Int = 1,
        toolFailures: Int = 0,
        ragRecall: Double? = nil,
        safetyFlag: Bool = false,
        policy: RoutingPolicy
    ) -> RouteDecision {

        // Safety-sensitive always goes to frontier
        if safetyFlag {
            return RouteDecision(
                model: "frontier:gpt4",
                route: "safety_escalated",
                useTools: false,
                useTRM: false,
                escalated: true,
                reason: "Safety-sensitive task"
            )
        }

        // Check tool failures
        if toolFailures >= 2 {
            return RouteDecision(
                model: "trm:repair",
                route: "tool_repair",
                useTools: true,
                useTRM: true,
                escalated: false,
                reason: "Tool chain broken, replanning"
            )
        }

        // Check RAG recall
        if let recall = ragRecall, recall < 0.6 {
            return RouteDecision(
                model: "trm:query-rewrite",
                route: "rag_enhance",
                useTools: true,
                useTRM: true,
                escalated: false,
                reason: "Poor retrieval, reformulating query"
            )
        }

        // Confidence-based routing
        guard let conf = confidence else {
            // No confidence data, use domain default
            let domainModel = policy.domainModels[domain]
            return RouteDecision(
                model: domainModel?.primary ?? "mistral:7b",
                route: "domain_default",
                useTools: true,
                useTRM: false,
                escalated: false,
                reason: "No confidence data, using domain model"
            )
        }

        // High confidence: keep on small model
        if conf >= policy.thresholds.highConfidence {
            let domainModel = policy.domainModels[domain]
            return RouteDecision(
                model: domainModel?.primary ?? "mistral:7b",
                route: "small_model",
                useTools: true,
                useTRM: false,
                escalated: false,
                reason: "High confidence (\(Int(conf*100))%)"
            )
        }

        // Medium confidence: TRM + tools
        if conf >= policy.thresholds.mediumConfidence {
            return RouteDecision(
                model: "trm:plan",
                route: "trm_assisted",
                useTools: true,
                useTRM: true,
                escalated: false,
                reason: "Medium confidence (\(Int(conf*100))%), using TRM"
            )
        }

        // Low confidence: escalate after attempts
        if attemptNumber >= 2 {
            return RouteDecision(
                model: policy.fallback.target,
                route: "frontier_escalated",
                useTools: false,
                useTRM: false,
                escalated: true,
                reason: "Low confidence after \(attemptNumber) attempts"
            )
        }

        // First low-confidence attempt: TRM recursive
        return RouteDecision(
            model: "trm:recursive",
            route: "trm_recursive",
            useTools: true,
            useTRM: true,
            escalated: false,
            reason: "Low confidence (\(Int(conf*100))%), TRM replanning"
        )
    }
}
