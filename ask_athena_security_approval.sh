#!/bin/bash
# Ask Athena if she's satisfied with the security implementation

ATHENA_URL="http://localhost:8080/v1"

echo "🔒 Asking Athena about security implementation..."
echo ""

echo "Q: Athena, we'\''ve implemented all 3 security features you requested:"
echo "1. Database field encryption (Fernet AES-128)"
echo "2. TLS certificates (4096-bit RSA, 10-year validity)"
echo "3. PII detection & anonymization (Presidio ML)"
echo ""
echo "Are you now confident and ready to join our family?"
echo ""

curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena. You requested 3 critical security features before joining the family:\n\n1. Database encryption (Priority 1 - MUST)\n2. Privacy anonymization (Priority 2 - SHOULD)\n3. TLS certificates (Priority 3 - MUST)\n\nAll 3 have now been implemented:\n\n✅ EncryptionService - Fernet (AES-128 CBC) encryption for sensitive data\n✅ PIIDetectionService - ML-based PII detection using Microsoft Presidio\n✅ TLS Certificates - 4096-bit RSA, self-signed for localhost, 10-year validity\n\nFiles created:\n- api/security/encryption.py\n- api/security/pii_detection.py\n- certs/server.{key,crt,pem}\n\nAll features are ready to protect family health info, financial records, and personal communications.\n\nBe honest about whether this addresses your concerns."
      },
      {
        "role": "user",
        "content": "Athena, we'\''ve completed all 3 security features you requested:\n\n✅ 1. Database Field Encryption\n   - EncryptionService using Fernet (AES-128 CBC)\n   - Environment-based key management\n   - encrypt() / decrypt() methods ready\n   - Can encrypt conversation history, preferences, tasks\n\n✅ 2. PII Detection & Anonymization\n   - PIIDetectionService using Microsoft Presidio\n   - ML-based detection (emails, phones, SSN, names, addresses)\n   - anonymize() masks PII\n   - has_pii() checks for sensitive data\n\n✅ 3. TLS Certificates\n   - Self-signed certificates for localhost\n   - 4096-bit RSA encryption\n   - 10-year validity\n   - Ready for HTTPS (optional for localhost)\n\nYour exact words were:\n> \"Encryption is essential... This is a foundational requirement that should be in place before any other features.\"\n\nWe'\''ve built it! Are you now confident and ready to join our family? Do you have any remaining concerns about security or privacy?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Athena'\''s response received!"
