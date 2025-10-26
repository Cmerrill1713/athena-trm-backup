// services/openai-compat/middleware.js
const { reqCounter, latHist, streamErr } = require('./metrics');

// Request metrics middleware
const metricsMiddleware = (req, res, next) => {
  const startTime = Date.now();
  const service = 'openai-compat';
  const route = req.path;
  
  // Start latency timer
  const end = latHist.labels(service, route).startTimer();
  
  // Track response finish
  res.on('finish', () => {
    // Record latency
    end();
    
    // Record request count
    reqCounter.labels(service, route, String(res.statusCode)).inc();
    
    // Log slow requests
    const duration = Date.now() - startTime;
    if (duration > 1000) {
      console.warn(`Slow request: ${req.method} ${route} took ${duration}ms`);
    }
  });
  
  // Track stream errors
  res.on('error', (error) => {
    streamErr.labels(error.message || 'unknown').inc();
  });
  
  next();
};

// SSE stream error tracking
const trackStreamError = (reason) => {
  streamErr.labels(reason).inc();
};

// Route selection tracking
const trackRouteSelection = (route, modality) => {
  const { routeSelection } = require('./metrics');
  routeSelection.labels(route, modality).inc();
};

module.exports = {
  metricsMiddleware,
  trackStreamError,
  trackRouteSelection
};
