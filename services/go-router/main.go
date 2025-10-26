package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	// TODO: Import generated proto
	// pb "github.com/athena/proto/athena"
)

const (
	grpcPort = "9115" // Different from Python router (9113)
	httpPort = "9116" // HTTP gateway for REST clients
)

// Server implements Router service
type Server struct {
	// pb.UnimplementedRouterServer
	govClient interface{} // Governance gRPC client
	natsConn  interface{} // NATS connection for events
}

// Decide implements intelligent routing with governance gate
func (s *Server) Decide(ctx context.Context, req interface{}) (interface{}, error) {
	start := time.Now()

	log.Printf("Routing request: user=%s, intent=%s", "req.User", "req.Intent")

	// 1. Propose routing decision (cheap heuristics)
	decision := s.proposeRoute(req)

	// 2. Governance gate: Authorize before spending
	authorized, altDecision, reason := s.authorizeWithGovernance(ctx, req, decision)
	if !authorized {
		log.Printf("Governance denied: %s, using alternative: %v", reason, altDecision)
		decision = altDecision
	}

	// 3. Emit routing decision event to NATS
	s.publishEvent("athena.routing.decision.approved", map[string]interface{}{
		"user":       "req.User",
		"intent":     "req.Intent",
		"route":      decision.Route,
		"model":      decision.Model,
		"latency_ms": time.Since(start).Milliseconds(),
	})

	// 4. Return decision
	log.Printf("Routing decision: route=%s, model=%s, latency=%dms",
		decision.Route, decision.Model, time.Since(start).Milliseconds())

	return decision, nil
}

// proposeRoute uses fast heuristics to propose initial routing
func (s *Server) proposeRoute(req interface{}) *RoutingDecision {
	// TODO: Implement routing logic
	// - Check intent (rag, chat, trm, dev.assist)
	// - Check query complexity
	// - Check provider health
	// - Apply load balancing

	return &RoutingDecision{
		Route:    "llm",
		Model:    "qwen2.5:7b",
		Endpoint: "http://host.docker.internal:11434",
		Reason:   "general chat query",
	}
}

// authorizeWithGovernance calls Python governance service via gRPC
func (s *Server) authorizeWithGovernance(ctx context.Context, req interface{}, decision *RoutingDecision) (bool, *RoutingDecision, string) {
	// TODO: Call governance.Authorize via gRPC
	// For now, always authorize
	return true, decision, "approved"
}

// publishEvent emits event to NATS
func (s *Server) publishEvent(subject string, data map[string]interface{}) {
	// TODO: Publish to NATS
	log.Printf("Event: %s, data: %v", subject, data)
}

// Health implements health check
func (s *Server) Health(ctx context.Context, req interface{}) (interface{}, error) {
	return &HealthResponse{
		Status: "healthy",
		Checks: map[string]string{
			"grpc":       "ok",
			"governance": "ok",
			"nats":       "ok",
		},
	}, nil
}

type RoutingDecision struct {
	Route        string
	Model        string
	Endpoint     string
	CostEstimate float64
	Reason       string
}

type HealthResponse struct {
	Status string
	Checks map[string]string
}

func main() {
	log.Println("Starting Athena Go Router...")

	// Create gRPC server
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", grpcPort))
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer(
	// Add interceptors for tracing, metrics, etc.
	)

	// Register router service
	server := &Server{}
	// pb.RegisterRouterServer(grpcServer, server)

	// Register health service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("athena.Router", grpc_health_v1.HealthCheckResponse_SERVING)

	// TODO: Start HTTP gateway in parallel for REST clients

	log.Printf("Go Router listening on gRPC port %s", grpcPort)
	log.Printf("Shadowing Python router on port 9113")

	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
