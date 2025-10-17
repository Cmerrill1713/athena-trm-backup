package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/athena/router/internal/governance"
	"github.com/athena/router/internal/health"
	"github.com/athena/router/internal/metrics"
	"github.com/athena/router/internal/router"
	"github.com/athena/router/pkg/config"
	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.uber.org/zap"
)

func main() {
	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	logger.Info("Starting Athena Model Router",
		zap.String("version", "1.0.0"),
		zap.String("policy", "local-first-no-surprises"),
	)

	// Load configuration
	cfg, err := config.LoadConfig("config/model_router.yaml")
	if err != nil {
		logger.Fatal("Failed to load configuration", zap.Error(err))
	}

	// Environment overrides
	applyEnvironmentOverrides(cfg, logger)

	// Initialize components
	metricsCollector := metrics.NewCollector()
	governanceClient := governance.NewClient(cfg.Governance.OrchestratorURL, logger)
	healthChecker := health.NewChecker(cfg, logger)
	routerService := router.NewService(cfg, metricsCollector, governanceClient, healthChecker, logger)

	// Start health checking
	go healthChecker.Start(context.Background())

	// Setup HTTP server
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(requestLogger(logger))

	// Health endpoint
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, healthChecker.GetStatus())
	})

	// Metrics endpoint (Prometheus)
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// Routing endpoints
	r.POST("/route", routerService.Route)
	r.POST("/infer", routerService.Infer)
	r.GET("/models", routerService.ListModels)

	// Governance integration
	r.POST("/freeze/:backend", routerService.FreezeBackend)
	r.POST("/unfreeze/:backend", routerService.UnfreezeBackend)
	r.GET("/frozen", routerService.ListFrozen)

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "9113"
	}

	srv := &http.Server{
		Addr:           ":" + port,
		Handler:        r,
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	// Graceful shutdown
	go func() {
		logger.Info("Router listening", zap.String("port", port))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Server failed", zap.Error(err))
		}
	}()

	// Wait for interrupt
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down router...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatal("Server forced shutdown", zap.Error(err))
	}

	logger.Info("Router stopped")
}

// Apply environment variable overrides
func applyEnvironmentOverrides(cfg *config.Config, logger *zap.Logger) {
	if os.Getenv("ATHENA_NO_CLOUD") == "1" {
		for i := range cfg.Backends {
			if cfg.Backends[i].Name == "cloud" {
				disabled := false
				cfg.Backends[i].Enabled = &disabled
				logger.Info("Cloud backend HARD BLOCKED by ATHENA_NO_CLOUD=1")
			}
		}
	}

	if os.Getenv("ATHENA_FAIL_CLOSED") == "1" {
		cfg.Policy = "fail-closed"
		logger.Info("FAIL CLOSED mode enabled - will reject if no local models available")
	}

	if endpoint := os.Getenv("OLLAMA_ENDPOINT"); endpoint != "" {
		for i := range cfg.Backends {
			if cfg.Backends[i].Name == "ollama" {
				cfg.Backends[i].Endpoint = endpoint
				logger.Info("Ollama endpoint overridden", zap.String("endpoint", endpoint))
			}
		}
	}

	if endpoint := os.Getenv("MLX_ENDPOINT"); endpoint != "" {
		for i := range cfg.Backends {
			if cfg.Backends[i].Name == "mlx" {
				cfg.Backends[i].Endpoint = endpoint
				logger.Info("MLX endpoint overridden", zap.String("endpoint", endpoint))
			}
		}
	}
}

// Request logger middleware
func requestLogger(logger *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path

		c.Next()

		duration := time.Since(start)
		logger.Info("request",
			zap.String("method", c.Request.Method),
			zap.String("path", path),
			zap.Int("status", c.Writer.Status()),
			zap.Duration("latency", duration),
		)
	}
}
