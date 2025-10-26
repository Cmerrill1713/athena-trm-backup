# 🚀 PRODUCTION-READY PLAN - From City to Livable

**Turning 220+ capabilities into a shippable, operable system**

---

## ✅ **COMPLETED (Just Now)**

### **1. Capability Registry** ✅
**File:** `capability_registry.csv` & `.json`
- 52 core capabilities cataloged
- Includes: owner, risk, SLO, auth, deps, tests
- Single source of truth created

### **2. Gateway Denylist** ✅
**File:** `gateway_denylist.json` & `.conf`
- 27 deprecated endpoints identified
- Returns 410 Gone with alternatives
- Ready to deploy to nginx/gateway

### **3. Production Makefile** ✅
**File:** `Makefile.production`
- Complete workflow automation
- Canary deployment targets
- Metrics snapshot
- Ship-check gates

---

## 📋 **NEXT: HIGH-LEVERAGE FIXES**

### **Priority 1: Immediate (Today)**

**A. Deploy Gateway Denylist** ⏳
```bash
make gateway-denylist-deprecated
# Apply gateway_denylist.conf to nginx
```
**Impact:** 27 broken endpoints stop confusing users

**B. Add Rate Limiting** ⏳
```bash
# Apply rate_limit_config.json to services
# Add middleware to UAI, Router, MCP
```
**Impact:** Prevent abuse, ensure fairness

**C. Lock CORS** ⏳
```bash
# Update auth_policy.json origins
# Remove allow_origins=["*"]
# Add specific PWA origin
```
**Impact:** Security hardening

---

### **Priority 2: This Week**

**D. Contract Tests** ⏳
```bash
pip install schemathesis
schemathesis run http://localhost:8080/openapi.json
# Add to ship-check
```
**Impact:** Catch API regressions

**E. Performance Gates** ⏳
```bash
# Create check_performance_gates.sh
# Verify p95 latency ≤ baseline × 1.10
# Verify 5xx < 0.3%
```
**Impact:** Prevent performance degradation

**F. Grafana Dashboards** ⏳
```bash
# Create 6 critical dashboards:
# 1. Route mix over time
# 2. p50/p95 latency by service
# 3. 5xx rate by service
# 4. Canary status + error budget
# 5. RAG recall proxy
# 6. Learning cycle metrics
```
**Impact:** Visibility during incidents

---

### **Priority 3: Nice to Have**

**G. Ownership Enforcement**
- Add CODEOWNERS file
- Require owner in OpenAPI spec
- CI check for owner field

**H. Shadow Routing**
- Use existing shadow targets in Makefile
- Mirror traffic to staging

**I. Traffic Replay**
- Capture sample traffic
- Replay nightly in staging

---

## 🎯 **THE WORKFLOW (Ready to Use)**

### **Pre-Deploy:**
```bash
make capability-registry          # Know what exists
make gateway-denylist-deprecated  # Block dead endpoints
make ship-check                   # All gates must pass
```

### **Canary Deploy:**
```bash
make canary-start    # Start at 5%
make canary-watch    # Monitor in another terminal
make canary-promote  # 5% → 25%
make canary-promote  # 25% → 50%
make canary-promote  # 50% → 100%
make metrics-snapshot # Lock new baseline
```

### **Emergency:**
```bash
make canary-rollback  # Instant rollback
```

---

## 📊 **CURRENT STATUS**

### **Completed:**
- ✅ Capability registry (52 entries)
- ✅ Gateway denylist (27 deprecated)
- ✅ Production Makefile
- ✅ Rate limit config
- ✅ Auth policy
- ✅ Input validation rules

### **In Progress:**
- ⏳ Deploying denylist
- ⏳ Adding rate limiting middleware
- ⏳ Locking CORS
- ⏳ Contract tests
- ⏳ Performance gates
- ⏳ Grafana dashboards

---

## 🏆 **BOTTOM LINE**

**From:** 220+ capabilities, no structure
**To:** Cataloged, gated, monitored, deployable

**You said:** "Make it livable"
**We're building:** Production-grade infrastructure

**Next:** Deploy guardrails and gates! 🚀

