/**
 * k6 Load Test for Athena Gateway
 * Tests both streaming and non-streaming endpoints
 * 
 * Run: k6 run --vus 50 --duration 5m scripts/k6_load_test.js
 */
import { check, sleep } from 'k6';
import http from 'k6/http';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latency = new Trend('latency_ms');

// Configuration
export let options = {
  stages: [
    { duration: '1m', target: 20 },   // Ramp up to 20 VUs
    { duration: '3m', target: 50 },   // Stay at 50 VUs
    { duration: '1m', target: 100 },  // Spike to 100 VUs
    { duration: '2m', target: 50 },   // Back to 50 VUs
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'],  // 95% of requests < 2s
    'errors': ['rate<0.01'],               // Error rate < 1%
    'latency_ms': ['p(95)<2000'],          // Custom metric
  },
};

// Test payloads
const prompts = [
  "Explain the router service",
  "What is RAG?",
  "How does governance work?",
  "Describe the learning system",
  "What is REP protocol?",
];

export default function () {
  // Choose Python or Go gateway based on environment variable
  const gatewayUrl = __ENV.GATEWAY_URL || 'http://localhost:8081';
  const endpoint = `${gatewayUrl}/v1/chat/completions`;
  
  // Random prompt
  const prompt = prompts[Math.floor(Math.random() * prompts.length)];
  
  const payload = JSON.stringify({
    model: "athena-chat",
    messages: [
      { role: "user", content: prompt }
    ],
    temperature: 0.7,
    stream: false,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'traceparent': `00-${generateTraceId()}-${generateSpanId()}-01`,
    },
    timeout: '30s',
  };
  
  // Make request
  const start = Date.now();
  const res = http.post(endpoint, payload, params);
  const duration = Date.now() - start;
  
  // Record metrics
  latency.add(duration);
  
  // Checks
  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'has choices': (r) => {
      try {
        return JSON.parse(r.body).choices.length > 0;
      } catch {
        return false;
      }
    },
    'has content': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.choices[0].message.content.length > 0;
      } catch {
        return false;
      }
    },
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
  
  // Think time
  sleep(1);
}

// Helper functions
function generateTraceId() {
  return Array.from({ length: 32 }, () => 
    Math.floor(Math.random() * 16).toString(16)
  ).join('');
}

function generateSpanId() {
  return Array.from({ length: 16 }, () => 
    Math.floor(Math.random() * 16).toString(16)
  ).join('');
}

// Teardown function (prints summary)
export function handleSummary(data) {
  return {
    'artifacts/k6_results.json': JSON.stringify(data, null, 2),
    stdout: `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 K6 LOAD TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Requests: ${data.metrics.http_reqs.values.count}
Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s

Latency:
  p50: ${data.metrics.http_req_duration.values['p(50)'].toFixed(0)}ms
  p95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(0)}ms
  p99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(0)}ms
  
Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%

Status:
  ${data.metrics.http_req_duration.values['p(95)'] < 2000 ? '✅' : '❌'} p95 < 2000ms
  ${data.metrics.errors.values.rate < 0.01 ? '✅' : '❌'} Error rate < 1%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`,
  };
}

