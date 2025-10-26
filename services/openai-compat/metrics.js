// services/openai-compat/metrics.js
const client = require('prom-client');

// Collect default metrics (CPU, memory, etc.)
client.collectDefaultMetrics();

// Custom Athena metrics
const reqCounter = new client.Counter({
  name: 'athena_requests_total',
  help: 'Total requests',
  labelNames: ['service', 'route', 'code']
});

const latHist = new client.Histogram({
  name: 'athena_request_latency_seconds',
  help: 'Request latency (s)',
  labelNames: ['service', 'route'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2, 5]
});

const streamErr = new client.Counter({
  name: 'athena_stream_errors_total',
  help: 'SSE stream errors',
  labelNames: ['reason']
});

const routeSelection = new client.Counter({
  name: 'athena_route_selection_created',
  help: 'Route selections by modality',
  labelNames: ['route', 'modality']
});

const governanceCanary = new client.Gauge({
  name: 'athena_governance_canary_active',
  help: 'Canary deployment active (0=disabled, 1=active)'
});

const modalityECE = new client.Gauge({
  name: 'athena_modality_ece_estimate',
  help: 'ECE estimate per modality',
  labelNames: ['modality']
});

module.exports = { 
  client, 
  reqCounter, 
  latHist, 
  streamErr, 
  routeSelection, 
  governanceCanary, 
  modalityECE 
};