package router

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/athena/router/internal/governance"
	"github.com/athena/router/internal/health"
	"github.com/athena/router/internal/metrics"
	"github.com/athena/router/pkg/config"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// Service handles routing logic
type Service struct {
	cfg        *config.Config
	metrics    *metrics.Collector
	governance *governance.Client
	health     *health.Checker
	logger     *zap.Logger
	client     *http.Client
	frozen     map[string]bool
}

// NewService creates a new router service
func NewService(
	cfg *config.Config,
	metrics *metrics.Collector,
	governance *governance.Client,
	health *health.Checker,
	logger *zap.Logger,
) *Service {
	return &Service{
		cfg:        cfg,
		metrics:    metrics,
		governance: governance,
		health:     health,
		logger:     logger,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		frozen: make(map[string]bool),
	}
}

// RouteRequest represents an incoming routing request
type RouteRequest struct {
	Prompt string `json:"prompt"`
	Domain string `json:"domain,omitempty"`
	Model  string `json:"model,omitempty"`
}

// RouteResponse represents the routing decision
type RouteResponse struct {
	Route    string `json:"route"`
	Endpoint string `json:"endpoint"`
	Model    string `json:"model,omitempty"`
	Reason   string `json:"reason,omitempty"`
}

// Route handles routing decisions
func (s *Service) Route(c *gin.Context) {
	start := time.Now()

	var req RouteRequest
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// Select backend
	backend := s.selectBackend(req.Domain)
	if backend == nil {
		s.logger.Error("No available backend found")
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "No available backends"})
		return
	}

	// Record metrics
	latency := time.Since(start).Milliseconds()
	s.metrics.RecordRoute(backend.Name, req.Domain, "success")
	s.metrics.RecordLatency(backend.Name, float64(latency))

	// Log decision
	s.governance.LogDecision(map[string]interface{}{
		"backend": backend.Name,
		"domain":  req.Domain,
		"latency": latency,
	})

	c.JSON(http.StatusOK, RouteResponse{
		Route:    backend.Name,
		Endpoint: backend.Endpoint,
		Model:    s.selectModel(backend, req.Domain),
		Reason:   fmt.Sprintf("Selected %s based on priority and health", backend.Name),
	})
}

// Infer handles direct inference requests
func (s *Service) Infer(c *gin.Context) {
	var req RouteRequest
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// Route to backend
	backend := s.selectBackend(req.Domain)
	if backend == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "No available backends"})
		return
	}

	// Forward request
	resp, err := s.forwardRequest(backend, req)
	if err != nil {
		s.logger.Error("Failed to forward request", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Request failed"})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// ListModels returns available models
func (s *Service) ListModels(c *gin.Context) {
	models := make([]map[string]interface{}, 0)

	for _, backend := range s.cfg.Backends {
		if !s.cfg.IsBackendEnabled(backend.Name) || s.frozen[backend.Name] {
			continue
		}

		for _, model := range backend.Models {
			models = append(models, map[string]interface{}{
				"backend":      backend.Name,
				"model":        model.Name,
				"domains":      model.Domains,
				"capabilities": model.Capabilities,
			})
		}
	}

	c.JSON(http.StatusOK, gin.H{"models": models})
}

// FreezeBackend freezes a backend
func (s *Service) FreezeBackend(c *gin.Context) {
	backend := c.Param("backend")
	s.frozen[backend] = true
	s.logger.Warn("Backend frozen", zap.String("backend", backend))
	s.metrics.RecordGovernanceDecision("freeze", backend)
	c.JSON(http.StatusOK, gin.H{"status": "frozen", "backend": backend})
}

// UnfreezeBackend unfreezes a backend
func (s *Service) UnfreezeBackend(c *gin.Context) {
	backend := c.Param("backend")
	delete(s.frozen, backend)
	s.logger.Info("Backend unfrozen", zap.String("backend", backend))
	s.metrics.RecordGovernanceDecision("unfreeze", backend)
	c.JSON(http.StatusOK, gin.H{"status": "unfrozen", "backend": backend})
}

// ListFrozen returns frozen backends
func (s *Service) ListFrozen(c *gin.Context) {
	frozen := make([]string, 0)
	for backend := range s.frozen {
		frozen = append(frozen, backend)
	}
	c.JSON(http.StatusOK, gin.H{"frozen": frozen})
}

// selectBackend selects the best backend for a request
func (s *Service) selectBackend(domain string) *config.Backend {
	// Check domain preferences
	if pref, exists := s.cfg.DomainPreferences[domain]; exists {
		for _, backendName := range pref.PreferredBackends {
			backend := s.cfg.GetBackend(backendName)
			if backend != nil && s.isBackendAvailable(backend) {
				return backend
			}
		}
	}

	// Fall back to priority-based selection
	var best *config.Backend
	for i := range s.cfg.Backends {
		backend := &s.cfg.Backends[i]
		if s.isBackendAvailable(backend) {
			if best == nil || backend.Priority < best.Priority {
				best = backend
			}
		}
	}

	// Block cloud attempts
	if best != nil && best.Name == "cloud" {
		s.metrics.RecordCloudAttempt()
		s.logger.Warn("Cloud backend selected but blocked by policy")
		return nil
	}

	return best
}

// isBackendAvailable checks if a backend is available
func (s *Service) isBackendAvailable(backend *config.Backend) bool {
	if !s.cfg.IsBackendEnabled(backend.Name) {
		return false
	}
	if s.frozen[backend.Name] {
		return false
	}
	if !s.health.IsHealthy(backend.Name) {
		return false
	}
	return true
}

// selectModel selects the best model for a domain
func (s *Service) selectModel(backend *config.Backend, domain string) string {
	for _, model := range backend.Models {
		for _, d := range model.Domains {
			if d == domain || d == "*" {
				return model.Name
			}
		}
	}

	// Return first model if no match
	if len(backend.Models) > 0 {
		return backend.Models[0].Name
	}

	return ""
}

// forwardRequest forwards a request to a backend
func (s *Service) forwardRequest(backend *config.Backend, req RouteRequest) (map[string]interface{}, error) {
	data, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	resp, err := s.client.Post(backend.Endpoint+"/api/generate", "application/json", bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}

	return result, nil
}
