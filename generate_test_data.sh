#!/bin/bash
# Generate test data for learning system

echo "🔄 Generating test feedback..."

# Generate some positive feedback
for i in {1..5}; do
  curl -s -X POST http://localhost:8080/v1/feedback \
    -H "Content-Type: application/json" \
    -d "{
      \"message_id\": \"test-msg-$i\",
      \"sentiment\": \"positive\",
      \"response_preview\": \"Test response $i - AI provided helpful information\",
      \"timestamp\": $(date +%s)
    }" > /dev/null
done

# Generate some negative feedback
for i in {6..8}; do
  curl -s -X POST http://localhost:8080/v1/feedback \
    -H "Content-Type: application/json" \
    -d "{
      \"message_id\": \"test-msg-$i\",
      \"sentiment\": \"negative\",
      \"response_preview\": \"Test response $i - AI response was unclear\",
      \"timestamp\": $(date +%s)
    }" > /dev/null
done

echo "✅ Generated 8 test feedback items (5 positive, 3 negative)"

echo ""
echo "🔄 Generating test routing decisions..."

# Generate routing decisions
routes=("ollama" "ollama" "cloud" "ollama" "ollama")
for i in {1..5}; do
  docker exec -i athena-postgres psql -U athena -d athena << SQL
  INSERT INTO routing_decisions (route, latency_ms, success, tokens_generated, ece_estimate)
  VALUES ('${routes[$((i-1))]}', $((50 + RANDOM % 100)), true, $((100 + RANDOM % 200)), $(echo "scale=4; $RANDOM / 32767" | bc));
SQL
done

echo "✅ Generated 5 test routing decisions"

echo ""
echo "🎯 Test data generation complete!"
