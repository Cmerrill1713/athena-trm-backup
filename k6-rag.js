/**
 * k6 Load Test for OpenAI-Compatible RAG Adapter
 * 
 * Usage:
 *   k6 run k6-rag.js
 *   k6 run -e BASE=http://localhost:3000 -e VUS=50 -e DURATION=10m k6-rag.js
 */

import { check, sleep } from 'k6';
import http from 'k6/http';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const streamErrors = new Rate('stream_errors');
const ragLatency = new Trend('rag_latency');
const chatLatency = new Trend('chat_latency');
const emptyResponses = new Counter('empty_responses');

// Configuration
const BASE_URL = __ENV.BASE || 'http://localhost:3000';
const VUS = parseInt(__ENV.VUS || '20');
const DURATION = __ENV.DURATION || '5m';

export const options = {
  vus: VUS,
  duration: DURATION,
  thresholds: {
    http_req_duration: ['p(95)<1500'], // 95% of requests under 1.5s
    http_req_failed: ['rate<0.003'],   // Less than 0.3% errors
    errors: ['rate<0.005'],             // Less than 0.5% custom errors
    stream_errors: ['rate<0.02'],      // Less than 2% stream errors
  },
};

// Test queries (varied to simulate real usage)
const queries = [
  'What is retrieval augmented generation?',
  'Explain vector embeddings',
  'How do I reset my password?',
  'What are the best practices for RAG?',
  'Tell me about semantic search',
  'What is BM25?',
  'Explain hybrid search',
  'How does RAG evaluation work?',
];

// Models to test (weighted distribution)
const modelDistribution = [
  { model: 'athena-rag', weight: 0.6 },      // 60% RAG queries
  { model: 'athena-chat', weight: 0.3 },     // 30% chat queries
  { model: 'athena-hybrid', weight: 0.1 },   // 10% hybrid queries
];

function selectModel() {
  const rand = Math.random();
  let cumulative = 0;
  for (const { model, weight } of modelDistribution) {
    cumulative += weight;
    if (rand <= cumulative) return model;
  }
  return 'athena-rag';
}

function selectQuery() {
  return queries[Math.floor(Math.random() * queries.length)];
}

export default function () {
  const model = selectModel();
  const query = selectQuery();
  
  // Test non-streaming completion
  testCompletion(model, query);
  
  // Occasionally test streaming (20% of requests)
  if (Math.random() < 0.2) {
    testStreaming(model, query);
  }
  
  sleep(1); // 1 second think time between requests
}

function testCompletion(model, query) {
  const url = `${BASE_URL}/v1/chat/completions`;
  const payload = JSON.stringify({
    model: model,
    messages: [{ role: 'user', content: query }],
    temperature: 0,
    stream: false,
    top_k: 5,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer dummy', // Optional auth
    },
    timeout: '30s',
  };
  
  const res = http.post(url, payload, params);
  
  // Record latency by model type
  if (model === 'athena-rag' || model === 'athena-hybrid') {
    ragLatency.add(res.timings.duration);
  } else {
    chatLatency.add(res.timings.duration);
  }
  
  // Validate response
  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'has choices': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.choices && body.choices.length > 0;
      } catch (e) {
        return false;
      }
    },
    'has content': (r) => {
      try {
        const body = JSON.parse(r.body);
        const content = body.choices[0]?.message?.content;
        return content && content.length > 0;
      } catch (e) {
        return false;
      }
    },
    'has required fields': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id && body.model && body.choices;
      } catch (e) {
        return false;
      }
    },
  });
  
  if (!success) {
    errorRate.add(1);
    console.log(`Error response: ${res.status} ${res.body.substring(0, 200)}`);
  } else {
    errorRate.add(0);
    
    // Check for empty content
    try {
      const body = JSON.parse(res.body);
      const content = body.choices[0]?.message?.content || '';
      if (content.length < 10) {
        emptyResponses.add(1);
      }
    } catch (e) {
      // Ignore parse errors (already caught above)
    }
  }
}

function testStreaming(model, query) {
  const url = `${BASE_URL}/v1/chat/completions`;
  const payload = JSON.stringify({
    model: model,
    messages: [{ role: 'user', content: query }],
    stream: true,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: '30s',
  };
  
  const res = http.post(url, payload, params);
  
  // Validate streaming response
  const streamSuccess = check(res, {
    'stream status 200': (r) => r.status === 200,
    'stream has data': (r) => r.body && r.body.includes('data:'),
    'stream ends with DONE': (r) => r.body && r.body.includes('[DONE]'),
  });
  
  if (!streamSuccess) {
    streamErrors.add(1);
    console.log(`Stream error: ${res.status}`);
  } else {
    streamErrors.add(0);
  }
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';
  const enableColors = options?.enableColors ?? false;
  
  let summary = '\n';
  summary += `${indent}✅ k6 Load Test Complete\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;
  
  // Request stats
  const httpReqDuration = data.metrics.http_req_duration;
  if (httpReqDuration) {
    summary += `${indent}HTTP Request Duration:\n`;
    summary += `${indent}  p50: ${httpReqDuration.values['p(50)'].toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${httpReqDuration.values['p(95)'].toFixed(2)}ms\n`;
    summary += `${indent}  p99: ${httpReqDuration.values['p(99)'].toFixed(2)}ms\n`;
    summary += `${indent}  max: ${httpReqDuration.values.max.toFixed(2)}ms\n\n`;
  }
  
  // Error rates
  const httpReqFailed = data.metrics.http_req_failed;
  if (httpReqFailed) {
    const failRate = (httpReqFailed.values.rate * 100).toFixed(2);
    summary += `${indent}Error Rate: ${failRate}% ${failRate < 0.3 ? '✅' : '❌'}\n`;
  }
  
  const errors = data.metrics.errors;
  if (errors) {
    const errorRate = (errors.values.rate * 100).toFixed(2);
    summary += `${indent}Custom Errors: ${errorRate}% ${errorRate < 0.5 ? '✅' : '❌'}\n`;
  }
  
  const streamErr = data.metrics.stream_errors;
  if (streamErr) {
    const streamErrorRate = (streamErr.values.rate * 100).toFixed(2);
    summary += `${indent}Stream Errors: ${streamErrorRate}% ${streamErrorRate < 2.0 ? '✅' : '❌'}\n\n`;
  }
  
  // Latency by model
  const ragLat = data.metrics.rag_latency;
  if (ragLat) {
    summary += `${indent}RAG Latency:\n`;
    summary += `${indent}  p50: ${ragLat.values['p(50)'].toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${ragLat.values['p(95)'].toFixed(2)}ms\n\n`;
  }
  
  const chatLat = data.metrics.chat_latency;
  if (chatLat) {
    summary += `${indent}Chat Latency:\n`;
    summary += `${indent}  p50: ${chatLat.values['p(50)'].toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${chatLat.values['p(95)'].toFixed(2)}ms\n\n`;
  }
  
  // Throughput
  const iterations = data.metrics.iterations;
  if (iterations) {
    const rps = iterations.values.rate.toFixed(2);
    summary += `${indent}Throughput: ${rps} req/s\n`;
    summary += `${indent}Total Requests: ${iterations.values.count}\n\n`;
  }
  
  summary += `${indent}${'='.repeat(50)}\n`;
  
  return summary;
}

