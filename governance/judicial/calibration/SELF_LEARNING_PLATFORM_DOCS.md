# 🔄 Self-Learning AI Platform Architecture

## Overview

This platform implements a production-grade self-learning system that continuously improves AI responses through multi-layer feedback loops, automated experimentation, and safe deployment practices.

## Core Components

### 1. Signal Capture Layer

#### Explicit Signals
```typescript
interface UserFeedback {
  traceId: string;
  rating: 'positive' | 'negative';
  action: 'regenerate' | 'edit' | 'abandon';
  timestamp: Date;
  modelVersion: string;
  promptVariant: string;
}
```

#### Implicit Signals
```typescript
interface InteractionSignals {
  traceId: string;
  dwellTime: number;        // seconds spent reading response
  followUpCount: number;    // subsequent messages in conversation
  completionRate: boolean;  // did user continue conversation?
  copyEvents: boolean;      // did user copy response?
}
```

#### Storage Schema
```sql
-- Postgres: feedback.feedback_signals
CREATE TABLE feedback_signals (
    trace_id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    model_version VARCHAR(50),
    prompt_variant VARCHAR(100),
    explicit_rating INTEGER,  -- -1, 0, 1
    implicit_score FLOAT,     -- 0.0 to 1.0
    created_at TIMESTAMP
);

-- Weaviate: semantic feedback analysis
{
  "class": "FeedbackPattern",
  "properties": [
    {"name": "trace_id", "dataType": ["string"]},
    {"name": "feedback_text", "dataType": ["text"]},
    {"name": "sentiment", "dataType": ["number"]},
    {"name": "success_patterns", "dataType": ["text[]"]}
  ]
}
```

### 2. Bandit Optimization Engine

#### Thompson Sampling Implementation
```python
class PromptBandit:
    def __init__(self, variants: List[str]):
        self.variants = variants
        self.alpha = defaultdict(lambda: 1.0)  # success count
        self.beta = defaultdict(lambda: 1.0)   # failure count

    def select_variant(self) -> str:
        """Select prompt variant using Thompson sampling"""
        samples = {}
        for variant in self.variants:
            # Sample from Beta distribution
            samples[variant] = np.random.beta(
                self.alpha[variant],
                self.beta[variant]
            )
        return max(samples, key=samples.get)

    def update(self, variant: str, reward: float):
        """Update bandit with feedback signal"""
        # Convert continuous reward to binary success
        success = 1 if reward > 0.5 else 0
        self.alpha[variant] += success
        self.beta[variant] += (1 - success)
```

#### Integration Points
```python
# In Athena service
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Select prompt variant
    variant = bandit.select_variant()

    # Generate response with selected variant
    response = await generate_with_variant(request.message, variant)

    # Attach trace ID for feedback correlation
    trace_id = generate_trace_id()
    response.metadata.trace_id = trace_id

    # Store selection for later feedback
    await redis.setex(f"variant:{trace_id}", 3600, variant)

    return response
```

### 3. RAG Self-Improvement Loop

#### Query Analysis Pipeline
```python
class RAGOptimizer:
    def __init__(self):
        self.recall_threshold = 0.7
        self.min_samples = 100

    async def analyze_query_performance(self, query: str, results: List[Dict]):
        """Analyze retrieval performance for a query"""
        # Calculate recall metrics
        relevant_found = sum(1 for r in results if r.get('relevant', False))
        recall = relevant_found / len(results) if results else 0

        # Flag low-recall queries
        if recall < self.recall_threshold:
            await self.flag_for_improvement(query, results)

    async def flag_for_improvement(self, query: str, results: List[Dict]):
        """Mark query for automated improvement"""
        await db.execute("""
            INSERT INTO rag_improvements (query, results, recall_score, status)
            VALUES ($1, $2, $3, 'pending')
        """, query, json.dumps(results), recall)
```

#### Automated Reranking
```python
class DynamicReranker:
    def __init__(self):
        self.performance_window = timedelta(hours=24)
        self.adjustment_threshold = 0.05

    async def adjust_thresholds(self):
        """Dynamically adjust reranking thresholds based on performance"""
        # Analyze recent performance
        recent_perf = await self.get_recent_performance()

        if abs(recent_perf - self.target_recall) > self.adjustment_threshold:
            # Adjust reranking parameters
            adjustment = (self.target_recall - recent_perf) * 0.1
            self.rerank_threshold = max(0.1, min(0.9, self.rerank_threshold + adjustment))

            # Log the change
            logger.info("Adjusted rerank threshold", {
                "old_threshold": self.rerank_threshold - adjustment,
                "new_threshold": self.rerank_threshold,
                "performance_delta": recent_perf - self.target_recall
            })
```

### 4. LLM Judgment Layer

#### Response Evaluation
```python
class ResponseEvaluator:
    def __init__(self, evaluation_model: str = "gpt-3.5-turbo"):
        self.model = evaluation_model
        self.criteria = {
            'helpfulness': 'How helpful is this response?',
            'factuality': 'How factually accurate is this response?',
            'clarity': 'How clear and understandable is this response?',
            'completeness': 'How complete is this response?'
        }

    async def evaluate_response(self, query: str, response: str) -> Dict[str, float]:
        """Use LLM to evaluate response quality"""
        evaluation_prompt = f"""
        Evaluate this AI response on a scale of 1-10 for each criterion:

        Query: {query}
        Response: {response}

        Criteria: {', '.join(self.criteria.keys())}

        Return JSON with scores for each criterion.
        """

        evaluation = await openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )

        return json.loads(evaluation.choices[0].message.content)
```

#### Feedback Aggregation
```python
class FeedbackAggregator:
    @staticmethod
    async def nightly_summary():
        """Generate nightly performance summary"""
        # Aggregate explicit feedback
        explicit = await db.fetch("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as total
            FROM feedback_signals
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)

        # Aggregate LLM evaluations
        llm_scores = await db.fetch("""
            SELECT AVG(helpfulness) as avg_helpful,
                   AVG(factuality) as avg_factual,
                   AVG(clarity) as avg_clear
            FROM llm_evaluations
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)

        # Store summary for trend analysis
        await db.execute("""
            INSERT INTO daily_performance (date, explicit_rating, llm_helpful, llm_factual, llm_clear)
            VALUES (CURRENT_DATE, $1, $2, $3, $4)
        """, explicit['avg_rating'], llm_scores['avg_helpful'], llm_scores['avg_factual'], llm_scores['avg_clear'])
```

### 5. Feature Flag Integration

#### Unleash Configuration
```typescript
// Feature flag definitions
const FEATURE_FLAGS = {
  PROMPT_VARIANT_A: 'prompt-optimization-v1',
  NEW_RERANKER: 'rag-reranker-v2',
  EXTENDED_CONTEXT: 'context-window-expansion',
  STREAMING_RESPONSES: 'response-streaming'
} as const;

// Usage in Athena
async function generate_response(query: string): Promise<string> {
  // Check feature flags for capabilities
  const useNewReranker = await unleash.isEnabled(FEATURE_FLAGS.NEW_RERANKER, {
    userId: getUserId(),
    properties: { query_length: query.length }
  });

  const enableStreaming = await unleash.isEnabled(FEATURE_FLAGS.STREAMING_RESPONSES);

  // Select prompt variant
  const promptVariant = await select_prompt_variant();

  // Generate with selected features
  return await generate_with_features(query, {
    reranker: useNewReranker ? 'v2' : 'v1',
    streaming: enableStreaming,
    prompt_variant: promptVariant
  });
}
```

#### Gradual Rollout Strategy
```python
class FeatureRollout:
    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        self.rollout_strategy = 'gradual'  # gradual | canary | percentage

    async def rollout_plan(self) -> List[Dict]:
        """Generate rollout plan based on strategy"""
        if self.rollout_strategy == 'gradual':
            return [
                {'percentage': 1, 'duration_days': 1},
                {'percentage': 5, 'duration_days': 2},
                {'percentage': 25, 'duration_days': 3},
                {'percentage': 100, 'duration_days': 0}
            ]
        # ... other strategies

    async def monitor_rollout(self):
        """Monitor feature performance during rollout"""
        # Track metrics by feature variant
        performance = await self.get_feature_performance()

        if performance['error_rate'] > 0.05:  # 5% error threshold
            await self.rollback_feature()
        elif performance['user_satisfaction'] > 0.8:  # 80% satisfaction
            await self.advance_rollout()
```

## Monitoring & Alerting

### Key Metrics to Track
```python
# Prometheus metrics for self-learning
SELF_LEARNING_METRICS = {
    'bandit_selections': Counter('bandit_variant_selections_total', 'Prompt variant selections'),
    'feedback_signals': Counter('feedback_signals_total', 'User feedback signals'),
    'llm_evaluations': Histogram('llm_evaluation_scores', 'LLM evaluation scores'),
    'rag_improvements': Counter('rag_improvement_flags_total', 'RAG improvement flags'),
    'feature_flag_changes': Counter('feature_flag_changes_total', 'Feature flag updates')
}
```

### Alert Rules
```yaml
# SLO burn alerts for self-learning
groups:
  - name: self_learning_slos
    rules:
      - alert: LowFeedbackSignalRate
        expr: rate(feedback_signals_total[1h]) < 10
        for: 30m
        labels: {severity: warning}
        annotations:
          summary: "Low feedback signal rate"
          description: "Learning system receiving < 10 feedback signals/hour"

      - alert: PoorLLMScoreTrend
        expr: rate(llm_evaluation_scores{quantile="0.5"}[1h]) < -0.1
        for: 1h
        labels: {severity: warning}
        annotations:
          summary: "LLM evaluation scores declining"
          description: "Median evaluation score trending down"
```

## API Endpoints

### Feedback Submission
```typescript
POST /api/feedback
{
  "trace_id": "uuid",
  "rating": 1 | 0 | -1,
  "action": "regenerate" | "edit" | "abandon",
  "metadata": {
    "response_length": 150,
    "processing_time": 2.3
  }
}
```

### Performance Analytics
```typescript
GET /api/analytics/performance
// Returns learning metrics and trends

GET /api/analytics/bandit-status
// Returns current prompt variant performance

GET /api/analytics/rag-performance
// Returns RAG improvement metrics
```

## Deployment Safety

### Pre-deployment Checks
```bash
# Validate feature flags
make feature-flag-check

# Run learning system tests
make learning-system-test

# Validate telemetry pipeline
make telemetry-validation
```

### Rollback Procedures
```bash
# Emergency rollback
make learning-system-rollback

# Gradual feature flag rollback
make feature-flag-rollback FEATURE=rag-reranker-v2

# Restore from backup
make learning-data-restore TIMESTAMP=2024-01-15-14-30
```

## Future Enhancements

### Advanced Learning Techniques
- **Reinforcement Learning**: Direct policy optimization from user feedback
- **Federated Learning**: Cross-platform learning while preserving privacy
- **Meta-Learning**: Learning to learn new tasks faster
- **Causal Inference**: Understanding why certain approaches work

### Integration Points
- **A/B Testing Framework**: More sophisticated experimentation
- **Model Registry**: Version control for model improvements
- **Data Quality Monitoring**: Automated detection of feedback quality issues
- **Explainability Layer**: Making learning decisions interpretable

---

*This architecture enables continuous, safe, and measurable improvement of AI capabilities through structured learning loops and comprehensive telemetry.*
