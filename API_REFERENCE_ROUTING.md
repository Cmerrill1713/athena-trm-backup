# Athena Local Model Router API Reference

**Complete API documentation for the Athena Local AI Model Routing System**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Core Endpoints](#core-endpoints)
- [Advanced Features](#advanced-features)
- [Monitoring](#monitoring)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## 🎯 Overview

The Athena Router provides intelligent routing between **locally-hosted AI models** based on domain embeddings, cost optimization, and performance metrics. It selects the best local model instance for each query while optimizing for privacy, local compute costs, and performance.

**Base URL:** `http://localhost:9113` (configurable via `ROUTER_HOST` and `ROUTER_PORT`)

**Content Type:** `application/json` for all requests

**Architecture:** Local model orchestration - routing decisions happen locally, inference runs on local model instances via Ollama/MLX

---

## 🔄 Ollama Integration Endpoints

### GET /ollama/models

Get available Ollama models with Athena router mappings.

**Response:**

```json
{
  "ollama_available": true,
  "models": {
    "qwen3-coder:30b": {
      "athena_model_id": "codellama-34b",
      "size": "18 GB",
      "modified": "2025-10-16T...",
      "digest": "abc123..."
    }
  },
  "model_count": 10,
  "athena_mappings": {
    "codellama-34b": "qwen3-coder:30b",
    "gpt-4-turbo": "qwen2.5:14b"
  }
}
```

### POST /ollama/generate

Generate text using Ollama model directly (bypasses routing).

**Request:**

```json
{
  "model": "qwen3-coder:30b",
  "prompt": "Write a Python function to sort a list",
  "options": {
    "temperature": 0.7,
    "num_predict": 100
  }
}
```

**Response:**

```json
{
  "model": "qwen3-coder:30b",
  "response": "def sort_list(arr):\n    return sorted(arr)",
  "done": true,
  "inference_time": 2.34,
  "tokens_per_second": 45.67
}
```

### POST /infer

**Route query to best local model AND execute inference** (combines routing + generation).

**Request:**

```json
{
  "query": "Write a Python function to calculate fibonacci",
  "domain": "code",
  "metadata": {
    "temperature": 0.1
  }
}
```

**Response:**

```json
{
  "routing": {
    "model": "codellama-34b",
    "confidence": 0.85,
    "domain": "code",
    "latency_ms": 0.012,
    "metadata": {
      "strategy": "domain_match"
    }
  },
  "inference": {
    "model": "qwen3-coder:30b",
    "response": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "done": true,
    "inference_time": 3.45,
    "tokens_per_second": 52.1
  },
  "ollama_model": "qwen3-coder:30b",
  "athena_model": "codellama-34b",
  "prompt": "Write a Python function to calculate fibonacci",
  "total_time": 3.462
}
```

---

## 🔐 Authentication

All endpoints except `/health` and `/metrics` require Bearer token authentication.

### Header Format

```
Authorization: Bearer <token>
```

### Environment Configuration

```bash
export ATHENA_ROUTER_TOKEN="your-secret-token"
```

### Development Mode

If `ATHENA_ROUTER_TOKEN` is not set, authentication is disabled for development.

---

## 📊 Rate Limiting

- **Default Limit:** 1000 requests per minute per IP
- **Configuration:** `ATHENA_ROUTER_RATE_LIMIT` environment variable
- **Response:** HTTP 429 with `Retry-After` header

---

## 🎯 Core Endpoints

### GET /health

Returns system health and configuration status.

**Response:**

```json
{
  "status": "healthy",
  "service": "athena-router",
  "models_loaded": 4,
  "fallback_threshold": 0.7,
  "authentication": true,
  "rate_limit_rpm": 1000,
  "ssl_enabled": false
}
```

### POST /route

Route a query to the most appropriate **local model instance**.

**Request:**

```json
{
  "query": "Write a Python function to sort an array",
  "domain": "code",
  "metadata": {
    "user_id": "user123",
    "priority": "high"
  }
}
```

**Response:**

```json
{
  "model": "codellama-34b",
  "confidence": 0.85,
  "domain": "code",
  "latency_ms": 0.012,
  "metadata": {
    "cost": 0.002,
    "quality_score": 0.85,
    "strategy": "domain_match"
  }
}
```

**Parameters:**

- `query` (string, required): The text query to route to a local model
- `domain` (string, optional): Domain hint ("general", "code", "math")
- `metadata` (object, optional): Additional context for routing decisions

### GET /models

List all available **local model instances** and their profiles.

**Response:**

```json
{
  "models": [
    {
      "model_id": "codellama-34b",
      "domain": "code",
      "quality_score": 0.85,
      "cost": 0.002,
      "latency_p50_ms": 1200,
      "latency_p95_ms": 1800,
      "is_approximate": false,
      "confidence": 0.9,
      "metadata": {
        "description": "Local CodeLlama 34B model instance",
        "provider": "Meta",
        "context_window": 16384,
        "local_endpoint": "localhost:8001"
      }
    },
    {
      "model_id": "gpt-4-turbo",
      "domain": "general",
      "quality_score": 0.95,
      "cost": 0.01,
      "latency_p50_ms": 800,
      "latency_p95_ms": 1200,
      "is_approximate": false,
      "confidence": 0.9,
      "metadata": {
        "description": "Local GPT-4-turbo model instance",
        "provider": "OpenAI",
        "context_window": 128000,
        "local_endpoint": "localhost:8002"
      }
    }
  ]
}
```

### POST /reload

Reload model profiles from disk without restarting.

**Response:**

```json
{
  "status": "reloaded",
  "models_loaded": 4
}
```

---

## 🚀 Advanced Features

### A/B Testing

#### POST /ab-test

Create a new A/B test.

**Request:**

```json
{
  "test_id": "perf-test-001",
  "strategy": "basic_vs_contrastive"
}
```

**Strategies:**

- `basic_vs_contrastive`: Compare basic vs contrastive routing
- `cost_vs_quality`: Compare cost vs quality optimization
- `latency_vs_accuracy`: Compare speed vs accuracy

**Response:**

```json
{
  "status": "created",
  "test_id": "perf-test-001",
  "strategy": "basic_vs_contrastive",
  "variants": ["basic", "contrastive"]
}
```

#### GET /ab-test/{test_id}

Get A/B test status and metrics.

**Response:**

```json
{
  "test_id": "perf-test-001",
  "strategy": "basic_vs_contrastive",
  "status": "active",
  "variants": [
    {
      "name": "basic",
      "traffic_percentage": 0.5,
      "requests": 1250,
      "success_rate": 0.987,
      "avg_latency_ms": 15.2,
      "avg_confidence": 0.82,
      "avg_cost": 0.0032
    },
    {
      "name": "contrastive",
      "traffic_percentage": 0.5,
      "requests": 1248,
      "success_rate": 0.992,
      "avg_latency_ms": 18.7,
      "avg_confidence": 0.88,
      "avg_cost": 0.0041
    }
  ],
  "should_complete": true
}
```

#### POST /ab-test/{test_id}/complete

Complete an A/B test and declare winner.

**Response:**

```json
{
  "status": "completed",
  "winner": "contrastive",
  "metrics": {
    "requests": 1248,
    "success_rate": 0.992,
    "avg_latency_ms": 18.7
  }
}
```

### Feature Flags

#### GET /features

List all feature flags.

**Response:**

```json
{
  "flags": {
    "contrastive_routing": {
      "enabled": true,
      "description": "Use contrastive domain embeddings",
      "rollout_percentage": 100.0
    },
    "ab_testing": {
      "enabled": false,
      "description": "Enable A/B testing framework",
      "rollout_percentage": 0.0
    }
  },
  "count": 5
}
```

#### GET /features/{flag_name}

Get a specific feature flag.

**Response:**

```json
{
  "name": "contrastive_routing",
  "enabled": true,
  "value": null,
  "description": "Use contrastive domain embeddings",
  "rollout_percentage": 100.0
}
```

#### POST /features/{flag_name}

Update a feature flag.

**Request:**

```json
{
  "enabled": true,
  "value": "experimental",
  "description": "Updated description",
  "rollout_percentage": 75.0
}
```

**Response:**

```json
{
  "status": "updated",
  "flag": "contrastive_routing",
  "enabled": true,
  "rollout_percentage": 75.0
}
```

### Cost Optimization

#### GET /cost-report

Get cost optimization analytics.

**Response:**

```json
{
  "total_cost": 0.0,
  "request_count": 0,
  "avg_cost_per_request": 0.0,
  "cost_by_model": {},
  "cost_by_domain": {},
  "top_cost_models": [],
  "budget_status": {
    "over_budget": false,
    "budget_configured": false
  }
}
```

#### GET /usage-report

Get usage analytics.

**Response:**

```json
{
  "total_requests": 2500,
  "hourly_distribution": {
    "16384": 450,
    "16385": 380
  },
  "model_distribution": {
    "codellama-34b": 1200,
    "gpt-4-turbo": 800,
    "gpt-3.5-turbo": 500
  },
  "domain_distribution": {
    "code": 1200,
    "general": 1000,
    "math": 300
  },
  "error_rates": {
    "codellama-34b": 0.008,
    "gpt-4-turbo": 0.005
  },
  "top_models": [
    ["codellama-34b", 1200],
    ["gpt-4-turbo", 800],
    ["gpt-3.5-turbo", 500]
  ],
  "top_domains": [
    ["code", 1200],
    ["general", 1000],
    ["math", 300]
  ]
}
```

#### POST /cost-weights

Update cost optimization weights.

**Request:**

```json
{
  "cost": 0.7,
  "quality": 0.2,
  "latency": 0.1
}
```

**Response:**

```json
{
  "status": "updated",
  "weights": {
    "cost": 0.7,
    "quality": 0.2,
    "latency": 0.1
  }
}
```

---

## 📊 Monitoring

### GET /metrics

Prometheus metrics endpoint.

**Response:** Prometheus exposition format

```
# HELP athena_router_requests_total Total routing requests
# TYPE athena_router_requests_total counter
athena_router_requests_total{model="codellama-34b",domain="code"} 1250

# HELP athena_router_latency_ms Routing latency in milliseconds
# TYPE athena_router_latency_ms histogram
athena_router_latency_ms_bucket{model="codellama-34b",le="1"} 1200
...
```

### Key Metrics

| Metric                         | Type      | Description              |
| ------------------------------ | --------- | ------------------------ |
| `athena_router_requests_total` | Counter   | Total routing requests   |
| `athena_router_latency_ms`     | Histogram | Request latency          |
| `athena_routing_confidence`    | Gauge     | Routing confidence score |
| `athena_fallbacks_total`       | Counter   | Fallback routing events  |
| `athena_router_errors_total`   | Counter   | Routing errors           |

---

## ❌ Error Handling

### HTTP Status Codes

| Code | Meaning               | Description             |
| ---- | --------------------- | ----------------------- |
| 200  | OK                    | Success                 |
| 400  | Bad Request           | Invalid request data    |
| 401  | Unauthorized          | Authentication required |
| 403  | Forbidden             | Authentication failed   |
| 404  | Not Found             | Resource not found      |
| 429  | Too Many Requests     | Rate limit exceeded     |
| 500  | Internal Server Error | Server error            |

### Error Response Format

```json
{
  "error": "Authentication required",
  "message": "Provide Bearer token in Authorization header"
}
```

### Rate Limit Response

```json
{
  "error": "Rate limit exceeded",
  "message": "Maximum 1000 requests per minute",
  "retry_after": 60
}
```

---

## 💡 Examples

### Basic Routing

```bash
# Route a code query
curl -X POST http://localhost:9113/route \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Write a Python function",
    "domain": "code"
  }'
```

### A/B Testing Workflow

```bash
# Create test
curl -X POST http://localhost:9113/ab-test \
  -H "Authorization: Bearer your-token" \
  -d '{"test_id": "test-001", "strategy": "basic_vs_contrastive"}'

# Check progress
curl http://localhost:9113/ab-test/test-001 \
  -H "Authorization: Bearer your-token"

# Complete test
curl -X POST http://localhost:9113/ab-test/test-001/complete \
  -H "Authorization: Bearer your-token"
```

### Feature Flag Management

```bash
# List flags
curl http://localhost:9113/features \
  -H "Authorization: Bearer your-token"

# Enable feature with 50% rollout
curl -X POST http://localhost:9113/features/contrastive_routing \
  -H "Authorization: Bearer your-token" \
  -d '{"enabled": true, "rollout_percentage": 50}'
```

### Cost Optimization

```bash
# Get cost report
curl http://localhost:9113/cost-report \
  -H "Authorization: Bearer your-token"

# Adjust weights (cost-focused)
curl -X POST http://localhost:9113/cost-weights \
  -H "Authorization: Bearer your-token" \
  -d '{"cost": 0.8, "quality": 0.1, "latency": 0.1}'
```

---

## 🔧 SDK Examples

### Python Client

```python
import requests

class RouterClient:
    def __init__(self, base_url="http://localhost:9113", token=None):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def route(self, query, domain="general"):
        response = requests.post(
            f"{self.base_url}/route",
            json={"query": query, "domain": domain},
            headers=self.headers
        )
        return response.json()

# Usage
client = RouterClient(token="your-token")
result = client.route("Write Python code", domain="code")
print(f"Routed to: {result['model']}")
```

### Swift Client

```swift
import Foundation

class RouterClient {
    let baseURL = URL(string: "http://localhost:9113")!
    let token: String?

    func route(query: String, domain: String = "general") async throws -> RoutingChoice {
        var request = URLRequest(url: baseURL.appendingPathComponent("/route"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let payload = ["query": query, "domain": domain]
        request.httpBody = try JSONEncoder().encode(payload)

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(RoutingChoice.self, from: data)
    }
}
```

---

## 📞 Support

For API issues or questions:

- Check the health endpoint: `GET /health`
- Review logs: `tail -f logs/routing_api_hardened.log`
- Monitor metrics in Grafana
- Contact the development team

---

**Version:** 1.0
**Last Updated:** 2025-10-16
**Base URL:** http://localhost:9113
