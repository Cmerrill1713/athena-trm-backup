package health

import (
	"context"
	"net/http"
	"sync"
	"time"

	"github.com/athena/router/pkg/config"
	"go.uber.org/zap"
)

// Status represents the health status of a backend
type Status struct {
	Name      string    `json:"name"`
	Healthy   bool      `json:"healthy"`
	LastCheck time.Time `json:"last_check"`
	Latency   int64     `json:"latency_ms"`
}

// Checker monitors backend health
type Checker struct {
	cfg      *config.Config
	logger   *zap.Logger
	statuses map[string]*Status
	mu       sync.RWMutex
	client   *http.Client
}

// NewChecker creates a new health checker
func NewChecker(cfg *config.Config, logger *zap.Logger) *Checker {
	return &Checker{
		cfg:      cfg,
		logger:   logger,
		statuses: make(map[string]*Status),
		client: &http.Client{
			Timeout: 5 * time.Second,
		},
	}
}

// Start begins health checking in the background
func (h *Checker) Start(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	// Initial check
	h.checkAll()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			h.checkAll()
		}
	}
}

// checkAll checks health of all backends
func (h *Checker) checkAll() {
	for _, backend := range h.cfg.Backends {
		go h.checkBackend(backend)
	}
}

// checkBackend checks health of a single backend
func (h *Checker) checkBackend(backend config.Backend) {
	start := time.Now()

	// Simple health check - try to reach the endpoint
	req, err := http.NewRequest("GET", backend.Endpoint+"/health", nil)
	if err != nil {
		h.updateStatus(backend.Name, false, 0)
		return
	}

	resp, err := h.client.Do(req)
	if err != nil {
		h.updateStatus(backend.Name, false, 0)
		return
	}
	defer resp.Body.Close()

	latency := time.Since(start).Milliseconds()
	healthy := resp.StatusCode == http.StatusOK

	h.updateStatus(backend.Name, healthy, latency)
}

// updateStatus updates the health status for a backend
func (h *Checker) updateStatus(name string, healthy bool, latency int64) {
	h.mu.Lock()
	defer h.mu.Unlock()

	h.statuses[name] = &Status{
		Name:      name,
		Healthy:   healthy,
		LastCheck: time.Now(),
		Latency:   latency,
	}

	if !healthy {
		h.logger.Warn("Backend unhealthy", zap.String("backend", name))
	}
}

// IsHealthy checks if a backend is healthy
func (h *Checker) IsHealthy(name string) bool {
	h.mu.RLock()
	defer h.mu.RUnlock()

	status, exists := h.statuses[name]
	if !exists {
		return true // Assume healthy if not yet checked
	}

	return status.Healthy
}

// GetStatus returns the current health status of all backends
func (h *Checker) GetStatus() map[string]*Status {
	h.mu.RLock()
	defer h.mu.RUnlock()

	result := make(map[string]*Status)
	for k, v := range h.statuses {
		result[k] = v
	}

	return result
}
