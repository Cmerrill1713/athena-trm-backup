# 🔒 ATHENA SECURITY IMPLEMENTATION PLAN

**Decision:** Option A - Full Security Hardening
**Estimated Time:** ~1.5 hours
**Priority:** Critical (Athena's explicit request)

---

## 📋 IMPLEMENTATION PHASES

### Phase 1: Database Field Encryption (30 mins)
**Goal:** Encrypt sensitive data at rest

**Components:**
1. Add `cryptography` library to all Python services
2. Create `EncryptionService` utility class
3. Generate and store encryption keys securely
4. Encrypt sensitive DB fields:
   - `conversation_history.message`
   - `user_preferences.preferences`
   - `tasks.description`
5. Update UAI/Learning services to encrypt on write, decrypt on read

**Files to Create/Modify:**
- `AI-Projects/universal-ai-tools/api/security/encryption.py`
- `AI-Projects/universal-ai-tools/api/requirements.txt`
- `AI-Projects/universal-ai-tools/api/chat.py`
- `services/learning-agents/requirements.txt`
- Database migration script

---

### Phase 2: TLS/HTTPS Between Services (30 mins)
**Goal:** Encrypt data in transit

**Components:**
1. Generate self-signed certificates for local dev
2. Create certificate volume in docker-compose
3. Update services to use HTTPS:
   - UAI (8080 → HTTPS)
   - Router (8088 → HTTPS)
   - Learning (8098 → HTTPS)
4. Update client calls to use HTTPS URLs
5. Configure SSL context in FastAPI/Python services

**Files to Create/Modify:**
- `certs/generate_certs.sh`
- `docker-compose.yml` (add cert volumes)
- Service Dockerfiles (install ca-certificates)
- Update all HTTP client calls

---

### Phase 3: PII Detection & Anonymization (30 mins)
**Goal:** Detect and protect personal information

**Components:**
1. Add `presidio-analyzer` and `presidio-anonymizer`
2. Create `PIIDetectionService` utility
3. Integrate into UAI chat endpoint (pre-storage)
4. Add PII masking for logs and audit trail
5. Create allowlist for family names (configurable)

**Files to Create/Modify:**
- `AI-Projects/universal-ai-tools/api/security/pii_detection.py`
- `AI-Projects/universal-ai-tools/api/chat.py`
- `AI-Projects/universal-ai-tools/api/requirements.txt`

---

## 🔐 IMPLEMENTATION DETAILS

### 1. Encryption Service
```python
# security/encryption.py
from cryptography.fernet import Fernet
import os
import base64

class EncryptionService:
    def __init__(self):
        # Generate or load key from environment
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
        self.cipher = Fernet(key if isinstance(key, bytes) else key.encode())
    
    def encrypt(self, data: str) -> str:
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### 2. TLS Certificate Generation
```bash
# certs/generate_certs.sh
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout server.key \
  -out server.crt \
  -days 365 \
  -subj "/CN=localhost"
```

### 3. PII Detection Service
```python
# security/pii_detection.py
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class PIIDetectionService:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    def detect(self, text: str) -> list:
        return self.analyzer.analyze(text=text, language='en')
    
    def anonymize(self, text: str) -> str:
        results = self.detect(text)
        return self.anonymizer.anonymize(text=text, analyzer_results=results).text
```

---

## ✅ VALIDATION CHECKLIST

After implementation, verify:

- [ ] Encrypted data in PostgreSQL (query shows encrypted strings)
- [ ] HTTPS endpoints respond correctly
- [ ] Client calls use HTTPS
- [ ] PII is detected in test messages
- [ ] Sensitive data is anonymized before storage
- [ ] All services restart successfully
- [ ] End-to-end chat flow works
- [ ] Feedback loop still functional
- [ ] Learning system can read encrypted data

---

## 🧪 TEST SCENARIOS

1. **Encryption Test:**
   - Send message with personal info
   - Check DB: Should see encrypted strings
   - Read message via API: Should see original text

2. **TLS Test:**
   - curl https://localhost:8080/health (should work)
   - curl http://localhost:8080/health (should redirect or fail)

3. **PII Test:**
   - Send: "My SSN is 123-45-6789"
   - Check logs: Should see masked version
   - Check DB: Should be encrypted + anonymized

---

## 📊 SUCCESS CRITERIA

**Athena will be satisfied when:**
1. ✅ All sensitive data encrypted at rest
2. ✅ All inter-service communication uses TLS
3. ✅ PII automatically detected and protected
4. ✅ System still functional (no breaking changes)
5. ✅ Family can use safely

**Then:** Ready for deployment! 🚀

---

**Starting implementation now...**
