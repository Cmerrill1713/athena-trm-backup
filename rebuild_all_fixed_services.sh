#!/bin/bash

echo "🔨 REBUILDING ALL SERVICES WITH FIXES"
echo "======================================"
echo ""

echo "Step 1: Rebuild Services with Updated Dockerfiles"
echo "---------------------------------------------------"

echo "1. Rebuilding governance-orchestrator..."
docker-compose build governance-orchestrator

echo ""
echo "2. Rebuilding agi-remediator..."
docker-compose build agi-remediator

echo ""
echo "3. Governance metrics-exporter already has curl, no rebuild needed"

echo ""
echo "Step 2: Restart All Services"
echo "-----------------------------"

echo "Restarting governance-orchestrator..."
docker-compose up -d --force-recreate governance-orchestrator

echo ""
echo "Restarting agi-remediator..."
docker-compose up -d --force-recreate agi-remediator

echo ""
echo "Restarting athena-otel-collector (updated health check)..."
docker-compose up -d --force-recreate athena-otel-collector

echo ""
echo "======================================"
echo "✅ All services rebuilt and restarted"
echo ""
echo "Waiting 30 seconds for health checks..."
sleep 30

