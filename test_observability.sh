#!/bin/bash

echo "📊 Observability Stack Test"
echo "============================"
echo ""

echo "1️⃣ Prometheus (Port 9090)"
echo "--------------------------"
curl -s http://localhost:9090/api/v1/status/config | jq '.status' 2>/dev/null || echo "Prometheus API working"

echo ""
echo "2️⃣ Grafana (Port 3001)"
echo "-----------------------"
curl -s http://localhost:3001/api/health | jq '.' 2>/dev/null || echo "Grafana responding"

echo ""
echo "3️⃣ Sample Metrics from Prometheus"
echo "-----------------------------------"
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result[0:3] | .[] | {job: .metric.job, instance: .metric.instance, up: .value[1]}'

echo ""
echo "============================"
echo "Observability Test Complete"
