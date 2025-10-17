package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// Config represents the complete router configuration
type Config struct {
	Version           string                      `yaml:"version"`
	Policy            string                      `yaml:"policy"`
	Backends          []Backend                   `yaml:"backends"`
	DomainPreferences map[string]DomainPreference `yaml:"domain_preferences"`
	Governance        GovernanceConfig            `yaml:"governance"`
	Metrics           MetricsConfig               `yaml:"metrics"`
	Logging           LoggingConfig               `yaml:"logging"`
	Limits            LimitsConfig                `yaml:"limits"`
	Performance       PerformanceConfig           `yaml:"performance"`
	Features          FeaturesConfig              `yaml:"features"`
}

type Backend struct {
	Name               string            `yaml:"name"`
	Priority           int               `yaml:"priority"`
	Endpoint           string            `yaml:"endpoint"`
	CostPerToken       float64           `yaml:"cost_per_token"`
	LatencyP95BudgetMS int               `yaml:"latency_p95_budget_ms"`
	Governance         BackendGovernance `yaml:"governance"`
	HealthCheck        HealthCheckConfig `yaml:"health_check"`
	Enabled            *bool             `yaml:"enabled,omitempty"`
	Models             []Model           `yaml:"models"`
}

type Model struct {
	Name         string   `yaml:"name"`
	Domains      []string `yaml:"domains"`
	Capabilities []string `yaml:"capabilities"`
	TOSUrl       string   `yaml:"tos_url,omitempty"`
}

type BackendGovernance struct {
	FreezeOnViolation bool    `yaml:"freeze_on_violation"`
	RequiresApproval  bool    `yaml:"requires_approval"`
	TOSCheck          bool    `yaml:"tos_check,omitempty"`
	BudgetCapMonthly  float64 `yaml:"budget_cap_monthly,omitempty"`
}

type HealthCheckConfig struct {
	IntervalSeconds int `yaml:"interval_seconds"`
	TimeoutSeconds  int `yaml:"timeout_seconds"`
}

type DomainPreference struct {
	PreferredBackends []string `yaml:"preferred_backends"`
	PreferredModels   []string `yaml:"preferred_models"`
	FallbackAllowed   bool     `yaml:"fallback_allowed"`
}

type GovernanceConfig struct {
	OrchestratorURL          string         `yaml:"orchestrator_url"`
	FreezeTriggers           FreezeTriggers `yaml:"freeze_triggers"`
	UnfreezeAfterSeconds     int            `yaml:"unfreeze_after_seconds"`
	UnfreezeRequiresApproval bool           `yaml:"unfreeze_requires_approval"`
	LogEveryDecision         bool           `yaml:"log_every_decision"`
	DecisionAnnotations      bool           `yaml:"decision_annotations"`
}

type FreezeTriggers struct {
	ViolationRateDelta float64 `yaml:"violation_rate_delta"`
	ECEThreshold       float64 `yaml:"ece_threshold"`
	CostBudgetExceeded bool    `yaml:"cost_budget_exceeded"`
}

type MetricsConfig struct {
	Enabled    bool     `yaml:"enabled"`
	Port       int      `yaml:"port"`
	Counters   []string `yaml:"counters"`
	Histograms []string `yaml:"histograms"`
	Gauges     []string `yaml:"gauges"`
}

type LoggingConfig struct {
	Level  string   `yaml:"level"`
	Format string   `yaml:"format"`
	Fields []string `yaml:"fields"`
}

type LimitsConfig struct {
	MaxConcurrentRequests int `yaml:"max_concurrent_requests"`
	RequestTimeoutSeconds int `yaml:"request_timeout_seconds"`
	MaxTokensPerRequest   int `yaml:"max_tokens_per_request"`
	RateLimitPerUser      int `yaml:"rate_limit_per_user"`
}

type PerformanceConfig struct {
	ConnectionPoolSize      int `yaml:"connection_pool_size"`
	KeepAliveTimeoutSeconds int `yaml:"keep_alive_timeout_seconds"`
	RetryAttempts           int `yaml:"retry_attempts"`
	RetryBackoffMS          int `yaml:"retry_backoff_ms"`
}

type FeaturesConfig struct {
	ABTesting           bool `yaml:"ab_testing"`
	CostOptimization    bool `yaml:"cost_optimization"`
	LatencyOptimization bool `yaml:"latency_optimization"`
	CacheResponses      bool `yaml:"cache_responses"`
	EmbeddingCache      bool `yaml:"embedding_cache"`
	ShadowMode          bool `yaml:"shadow_mode"`
}

// LoadConfig loads configuration from YAML file
func LoadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	// Set defaults for optional fields
	for i := range cfg.Backends {
		if cfg.Backends[i].Enabled == nil {
			enabled := true
			cfg.Backends[i].Enabled = &enabled
		}
	}

	return &cfg, nil
}

// IsBackendEnabled checks if a backend is enabled
func (c *Config) IsBackendEnabled(name string) bool {
	for _, b := range c.Backends {
		if b.Name == name && b.Enabled != nil {
			return *b.Enabled
		}
	}
	return false
}

// GetBackend returns a backend by name
func (c *Config) GetBackend(name string) *Backend {
	for i := range c.Backends {
		if c.Backends[i].Name == name {
			return &c.Backends[i]
		}
	}
	return nil
}
