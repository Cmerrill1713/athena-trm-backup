package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	// Router metrics
	routerRequests = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "athena_router_requests_total",
			Help: "Total number of routing requests",
		},
		[]string{"status", "model", "domain"},
	)

	routerLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "athena_router_latency_ms",
			Help:    "Routing latency in milliseconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"model", "domain"},
	)

	routerConfidence = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "athena_routing_confidence",
			Help: "Current routing confidence score",
		},
		[]string{"model", "domain"},
	)

	// Fallback metrics
	fallbacksTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "athena_fallbacks_total",
			Help: "Total number of routing fallbacks",
		},
		[]string{"from_backend", "to_backend"},
	)

	// Local inference metrics
	localSuccess = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "athena_router_local_success_total",
			Help: "Total successful local model inferences",
		},
		[]string{"backend"},
	)

	// Cloud usage tracking (should be 0)
	cloudAttempts = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "athena_router_cloud_attempts_total",
			Help: "Total cloud model access attempts",
		},
	)

	cloudBlocked = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "athena_router_cloud_blocked_total",
			Help: "Total cloud model access blocked by policy",
		},
	)
)

func init() {
	// Register all metrics
	prometheus.MustRegister(routerRequests)
	prometheus.MustRegister(routerLatency)
	prometheus.MustRegister(routerConfidence)
	prometheus.MustRegister(fallbacksTotal)
	prometheus.MustRegister(localSuccess)
	prometheus.MustRegister(cloudAttempts)
	prometheus.MustRegister(cloudBlocked)
}

func main() {
	port := os.Getenv("EXPORTER_PORT")
	if port == "" {
		port = "9091"
	}

	// Health endpoint
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "OK")
	})

	// Metrics endpoint
	http.Handle("/metrics", promhttp.Handler())

	// Simulation endpoint for testing
	http.HandleFunc("/simulate", func(w http.ResponseWriter, r *http.Request) {
		simulateMetrics()
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "Metrics simulated")
	})

	log.Printf("Starting router metrics exporter on :%s", port)
	log.Printf("Health: http://localhost:%s/health", port)
	log.Printf("Metrics: http://localhost:%s/metrics", port)
	log.Printf("Simulate: http://localhost:%s/simulate", port)

	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func simulateMetrics() {
	// Simulate some realistic metrics for testing
	models := []string{"codellama-34b", "gpt-3.5-turbo", "claude-3-haiku"}
	domains := []string{"code", "general", "math"}
	statuses := []string{"success", "error"}

	for i := 0; i < 10; i++ {
		model := models[i%len(models)]
		domain := domains[i%len(domains)]
		status := statuses[i%3] // Mostly success

		routerRequests.WithLabelValues(status, model, domain).Inc()

		if status == "success" {
			latency := 10.0 + float64(i)*2.0 // 10-28ms
			routerLatency.WithLabelValues(model, domain).Observe(latency)

			confidence := 0.7 + float64(i)*0.05 // 0.7-1.15 (will cap)
			if confidence > 1.0 {
				confidence = 1.0
			}
			routerConfidence.WithLabelValues(model, domain).Set(confidence)

			// Simulate local success
			localSuccess.WithLabelValues("mlx").Inc()
		}

		// Occasional fallback
		if i%7 == 0 {
			fallbacksTotal.WithLabelValues("contrastive", "knn").Inc()
		}
	}

	// Simulate cloud blocking (should be 0 in production)
	if os.Getenv("ATHENA_NO_CLOUD") == "1" {
		cloudAttempts.Inc()
		cloudBlocked.Inc()
	}

	log.Println("Simulated router metrics")
}
