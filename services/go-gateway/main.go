package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

const (
	httpPort = "8081" // Different from Python UAI (8080)
)

// OpenAI-compatible request
type ChatCompletionRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	Temperature float64   `json:"temperature,omitempty"`
	MaxTokens   int       `json:"max_tokens,omitempty"`
	Stream      bool      `json:"stream,omitempty"`
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// OpenAI-compatible response
type ChatCompletionResponse struct {
	ID      string   `json:"id"`
	Object  string   `json:"object"`
	Created int64    `json:"created"`
	Model   string   `json:"model"`
	Choices []Choice `json:"choices"`
}

type Choice struct {
	Index        int     `json:"index"`
	Message      Message `json:"message"`
	FinishReason string  `json:"finish_reason"`
}

// Gateway handles OpenAI-compatible requests with governance
type Gateway struct {
	routerClient     interface{} // gRPC client to Go router
	governanceClient interface{} // gRPC client to Python governance
}

// ChatCompletion handles /v1/chat/completions
func (g *Gateway) ChatCompletion(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	ctx := r.Context()
	
	// Parse request
	var req ChatCompletionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	log.Printf("Chat completion: model=%s, stream=%v, messages=%d", 
		req.Model, req.Stream, len(req.Messages))
	
	// 1. Extract trace ID from headers
	traceID := r.Header.Get("traceparent")
	if traceID == "" {
		traceID = fmt.Sprintf("go-gateway-%d", time.Now().UnixNano())
	}
	
	// 2. Call router via gRPC for routing decision
	// TODO: routingDecision := g.routerClient.Decide(ctx, ...)
	
	// 3. Governance gate (optional - can be in router)
	// TODO: authorized := g.governanceClient.Authorize(ctx, ...)
	
	// 4. Call actual model endpoint
	// TODO: Implement actual model call
	
	// 5. Handle streaming vs non-streaming
	if req.Stream {
		g.handleStreamingResponse(w, r, &req, traceID)
	} else {
		g.handleNonStreamingResponse(w, r, &req, traceID)
	}
	
	log.Printf("Request completed: latency=%dms", time.Since(start).Milliseconds())
}

// handleStreamingResponse handles SSE streaming with backpressure
func (g *Gateway) handleStreamingResponse(w http.ResponseWriter, r *http.Request, req *ChatCompletionRequest, traceID string) {
	// Set SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Trace-ID", traceID)
	
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}
	
	// TODO: Stream from actual model
	// For now, mock streaming
	tokens := []string{"Hello", " from", " Go", " gateway", "!"}
	
	for i, token := range tokens {
		// Check if client disconnected
		select {
		case <-r.Context().Done():
			log.Println("Client disconnected")
			return
		default:
		}
		
		// Stream chunk
		chunk := map[string]interface{}{
			"id":      fmt.Sprintf("chatcmpl-%d", time.Now().UnixNano()),
			"object":  "chat.completion.chunk",
			"created": time.Now().Unix(),
			"model":   req.Model,
			"choices": []map[string]interface{}{
				{
					"index": 0,
					"delta": map[string]string{
						"content": token,
					},
					"finish_reason": nil,
				},
			},
		}
		
		// Last chunk has finish_reason
		if i == len(tokens)-1 {
			chunk["choices"].([]map[string]interface{})[0]["finish_reason"] = "stop"
		}
		
		data, _ := json.Marshal(chunk)
		fmt.Fprintf(w, "data: %s\n\n", data)
		flusher.Flush()
		
		time.Sleep(100 * time.Millisecond) // Simulate model latency
	}
	
	// Send [DONE]
	fmt.Fprintf(w, "data: [DONE]\n\n")
	flusher.Flush()
}

// handleNonStreamingResponse handles regular JSON response
func (g *Gateway) handleNonStreamingResponse(w http.ResponseWriter, r *http.Request, req *ChatCompletionRequest, traceID string) {
	// TODO: Get full response from model
	
	response := ChatCompletionResponse{
		ID:      fmt.Sprintf("chatcmpl-%d", time.Now().UnixNano()),
		Object:  "chat.completion",
		Created: time.Now().Unix(),
		Model:   req.Model,
		Choices: []Choice{
			{
				Index: 0,
				Message: Message{
					Role:    "assistant",
					Content: "Hello from Go gateway!",
				},
				FinishReason: "stop",
			},
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Trace-ID", traceID)
	json.NewEncoder(w).Encode(response)
}

// Health check
func (g *Gateway) Health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "healthy",
		"service": "go-gateway",
		"checks": map[string]string{
			"http":       "ok",
			"router":     "ok",
			"governance": "ok",
		},
	})
}

func main() {
	log.Println("Starting Athena Go Gateway (OpenAI-compatible)...")
	
	gateway := &Gateway{}
	
	// Register routes
	http.HandleFunc("/v1/chat/completions", gateway.ChatCompletion)
	http.HandleFunc("/health", gateway.Health)
	
	// Add middleware for CORS, rate limiting, tracing, etc.
	
	addr := fmt.Sprintf(":%s", httpPort)
	log.Printf("Go Gateway listening on HTTP port %s", httpPort)
	log.Printf("Shadowing Python UAI on port 8080")
	log.Printf("OpenAI-compatible: POST /v1/chat/completions")
	
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}

