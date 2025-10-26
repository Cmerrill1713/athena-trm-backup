#!/bin/bash
# Check what security features are ACTUALLY implemented

echo "🔍 AUDITING ACTUAL SECURITY IMPLEMENTATION"
echo "=========================================="
echo ""

echo "1. Checking PostgreSQL encryption..."
docker exec athena-postgres psql -U athena -d athena -c "SHOW data_checksums;" 2>/dev/null || echo "❌ Not accessible"
echo ""

echo "2. Checking for TLS/SSL in services..."
echo "UAI (port 8080):"
curl -sk https://localhost:8080/health 2>&1 | grep -q "SSL" && echo "✅ HTTPS enabled" || echo "❌ HTTP only"
echo ""

echo "3. Checking for encryption in code..."
echo "Searching for encryption libraries..."
grep -r "cryptography\|Fernet\|AES\|encrypt" AI-Projects/universal-ai-tools/api/*.py 2>/dev/null | head -n 5
grep -r "cryptography\|Fernet\|AES\|encrypt" services/*/server.py 2>/dev/null | head -n 5
echo ""

echo "4. Checking PostgreSQL for sensitive data protection..."
echo "Checking if conversation_history has encryption..."
docker exec athena-postgres psql -U athena -d athena -c "\d conversation_history" 2>/dev/null | grep -i "encrypt"
echo ""

echo "5. Checking for PII detection..."
grep -r "PII\|personal.*identif\|sensitive.*data" AI-Projects/universal-ai-tools/ services/ 2>/dev/null | head -n 5
echo ""

echo "6. Checking audit logs for sensitive data..."
docker exec athena-postgres psql -U athena -d athena -c "SELECT COUNT(*) FROM judicial_audit_log;" 2>/dev/null || echo "Table might not exist"
echo ""

echo "7. Checking for data retention policies..."
grep -r "retention\|cleanup\|delete.*old" AI-Projects/universal-ai-tools/ services/ 2>/dev/null | head -n 5
echo ""

echo "✅ Security audit complete!"
