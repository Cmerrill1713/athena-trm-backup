package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Collector handles metrics collection
type Collector struct {
	routeRequests       *prometheus.CounterVec
	cloudAttempts       prometheus.Counter
	routeLatency        *prometheus.HistogramVec
	backendHealth       *prometheus.GaugeVec
	governanceDecisions *prometheus.CounterVec
}

// NewCollector creates a new metrics collector
func NewCollector() *Collector {
	return &Collector{
		routeRequests: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "athena_router_route_requests_total",
				Help: "Total number of routing requests",
			},
			[]string{"backend", "domain", "status"},
		),
		cloudAttempts: promauto.NewCounter(
			prometheus.CounterOpts{
				Name: "athena_router_cloud_attempts_total",
				Help: "Number of times cloud routing was attempted (should be 0)",
			},
		),
		routeLatency: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "athena_router_route_latency_ms",
				Help:    "Routing decision latency in milliseconds",
				Buckets: []float64{1, 5, 10, 25, 50, 100, 250, 500, 1000},
			},
			[]string{"backend"},
		),
		backendHealth: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "athena_router_backend_health",
				Help: "Health status of backends (1=healthy, 0=unhealthy)",
			},
			[]string{"backend"},
		),
		governanceDecisions: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "athena_router_governance_decisions_total",
				Help: "Total governance decisions",
			},
			[]string{"action", "result"},
		),
	}
}

// RecordRoute records a routing request
func (c *Collector) RecordRoute(backend, domain, status string) {
	c.routeRequests.WithLabelValues(backend, domain, status).Inc()
}

// RecordCloudAttempt records an attempt to use cloud routing
func (c *Collector) RecordCloudAttempt() {
	c.cloudAttempts.Inc()
}

// RecordLatency records routing latency
func (c *Collector) RecordLatency(backend string, latencyMS float64) {
	c.routeLatency.WithLabelValues(backend).Observe(latencyMS)
}

// SetBackendHealth sets the health status of a backend
func (c *Collector) SetBackendHealth(backend string, healthy bool) {
	value := 0.0
	if healthy {
		value = 1.0
	}
	c.backendHealth.WithLabelValues(backend).Set(value)
}

// RecordGovernanceDecision records a governance decision
func (c *Collector) RecordGovernanceDecision(action, result string) {
	c.governanceDecisions.WithLabelValues(action, result).Inc()
}
