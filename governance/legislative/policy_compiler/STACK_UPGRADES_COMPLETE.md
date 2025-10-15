# Stack Upgrades Complete

> **Fast, worth-it improvements implemented**

## ✅ Upgrades Implemented

### 1. .env File Support

**What:** Load tokens and ports from `.env.stack` file
**Why:** Easier configuration management, no hard-coded tokens
**How:** Makefile now includes `.env.stack` if present

**Usage:**
```bash
# Copy the example
cp .env.stack.example .env.stack

# Edit your values
vim .env.stack

# Start stack (uses your .env values)
make stack-up
```

**Example .env.stack:**
```bash
UAT_PORT=8181
ATH_PORT=8090
BRIDGE_PORT=8014
UAT_TOKEN=your-secure-token
ATH_TOKEN=your-secure-token
ENV=dev
USE_MOCK=0
```

### 2. Exit Codes from /run_tests

**What:** Athena returns HTTP 422 when tests fail
**Why:** Makes CI pipelines stricter and clearer
**How:** `/run_tests` endpoint returns non-200 on test failures

**Before:**
```json
HTTP 200 OK
{
  "ok": false,
  "summary": {"failed": 5}
}
```

**After:**
```json
HTTP 422 Unprocessable Entity
{
  "ok": false,
  "summary": {"failed": 5}
}
```

**CI/CD Usage:**
```bash
# Fails the build if tests fail
curl -f -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer $ATH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke"}' || exit 1
```

### 3. Artifacts on Fail

**What:** Include `artifact_path` in response when report exists
**Why:** Easy CI artifact upload
**How:** Response includes path to `pytest_report.json`

**Response with artifact:**
```json
{
  "ok": false,
  "summary": {...},
  "artifact_path": "/Users/christianmerrill/Documents/GitHub/pytest_report.json",
  "report": {...}
}
```

**CI/CD Upload Example:**
```yaml
- name: Run Tests
  run: |
    response=$(curl -X POST http://127.0.0.1:8090/run_tests \
      -H "Authorization: Bearer $ATH_TOKEN" \
      -d '{"markers":"smoke"}')
    echo "$response" | jq .

- name: Upload Test Artifacts
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: pytest-report
    path: pytest_report.json
```

---

## Implementation Details

### Makefile Changes

Added `.env.stack` support:
```makefile
# -------- Load .env.stack if exists --------
-include .env.stack

# -------- Ports & Tokens --------
UAT_PORT ?= 8181
ATH_PORT ?= 8090
...
```

The `-include` directive loads the file if it exists, but doesn't fail if missing.

### Athena API Changes

**File:** `AI-Projects/universal-ai-tools/athena/api.py`

1. **Added JSONResponse import:**
```python
from fastapi.responses import StreamingResponse, JSONResponse
```

2. **Enhanced `/run_tests` endpoint:**
```python
# Add artifact path if report exists
if report_exists:
    response_data["artifact_path"] = report_path

# Return non-200 status if tests failed
if proc.returncode != 0:
    return JSONResponse(
        status_code=422,
        content=response_data
    )
```

---

## Verification

### Test .env Support
```bash
# Create custom config
cat > .env.stack << EOF
UAT_PORT=9181
ATH_PORT=9090
BRIDGE_PORT=9014
UAT_TOKEN=testtoken
ATH_TOKEN=testtoken
EOF

# Start stack
make stack-up

# Verify custom ports
lsof -iTCP:9181,9090,9014 -sTCP:LISTEN
```

### Test Exit Codes
```bash
# Start stack
make stack-up

# Run tests that will fail
response=$(curl -w "\n%{http_code}" -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"nonexistent"}')

# Check status code
echo "$response" | tail -n 1
# Should be 422 if tests failed
```

### Test Artifact Path
```bash
# Run tests
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke"}' | jq .artifact_path

# Should output: "/Users/christianmerrill/Documents/GitHub/pytest_report.json"
```

---

## Benefits

### 1. .env File Support
✅ No hard-coded tokens in Makefile
✅ Easy per-environment configuration
✅ Gitignore `.env.stack` for security
✅ Example file for onboarding

### 2. Exit Codes
✅ Strict CI/CD pipelines
✅ Clear failure signals
✅ Standard HTTP semantics
✅ Works with `curl -f`

### 3. Artifact Path
✅ Easy CI artifact upload
✅ Clear file location
✅ No path guessing
✅ Works with GitHub Actions

---

## Migration Guide

### For Existing Deployments

**Step 1:** Create `.env.stack`
```bash
cp .env.stack.example .env.stack
# Edit with your values
```

**Step 2:** Add to .gitignore
```bash
echo ".env.stack" >> .gitignore
```

**Step 3:** Update CI/CD
```yaml
# Old (always returns 200)
- run: curl http://127.0.0.1:8090/run_tests | jq .ok

# New (respects exit codes)
- run: |
    response=$(curl -f http://127.0.0.1:8090/run_tests)
    echo "$response" | jq .
```

**Step 4:** Test
```bash
make stack-down
make stack-up
make athena-tests
```

---

## Documentation Updates

Updated documentation to reflect new features:
- **STACK_VERIFICATION_PLAYBOOK.md** - New verification guide
- **STACK_MANAGEMENT_GUIDE.md** - Updated with .env support
- **STACK_QUICK_REF.md** - Updated examples

---

## Configuration Reference

### .env.stack Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UAT_PORT` | 8181 | UAT service port |
| `ATH_PORT` | 8090 | Athena service port |
| `BRIDGE_PORT` | 8014 | Bridge adapter port |
| `UAT_TOKEN` | supersecret | UAT auth token |
| `ATH_TOKEN` | supersecret | Athena auth token |
| `BRIDGE_TOKEN` | (empty) | Bridge token (optional in dev) |
| `ENV` | dev | Environment (dev/staging/prod) |
| `USE_MOCK` | 0 | Use mock data (0=real, 1=mock) |

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Tests passed |
| 422 | Unprocessable Entity | Tests failed |
| 401 | Unauthorized | Invalid token |
| 504 | Gateway Timeout | Tests timeout (>10min) |
| 500 | Internal Server Error | Execution error |

---

## Next Steps

### Immediate
1. **Create your .env.stack:**
   ```bash
   cp .env.stack.example .env.stack
   ```

2. **Test the upgrades:**
   ```bash
   make stack-up
   make athena-tests
   ```

3. **Update CI/CD pipelines** to use `-f` flag with curl

### Optional Future Enhancements

1. **Multiple .env profiles:**
   - `.env.stack.dev`
   - `.env.stack.staging`
   - `.env.stack.prod`
   - Load via `ENV=prod make stack-up`

2. **Automatic artifact cleanup:**
   - Remove old `pytest_report.json` before test run
   - Timestamp artifact files

3. **Structured logging:**
   - JSON logs for easier parsing
   - Log aggregation integration

4. **Health check intervals:**
   - Periodic health checks in background
   - Auto-restart on failures

---

## Troubleshooting

### .env not loading
```bash
# Verify file exists
ls -la .env.stack

# Check Makefile syntax
make -n stack-up | head -5

# Should see environment variables
```

### HTTP 422 unexpected
```bash
# This is now expected when tests fail
# Check test results:
curl http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -d '{}' | jq .summary
```

### Artifact path missing
```bash
# Artifact only included if report generated
# Check if pytest-json-report is installed:
python3 -m pip list | grep pytest-json-report
```

---

## Summary

✅ **.env support** - Easy configuration
✅ **Exit codes** - Strict CI/CD
✅ **Artifact paths** - Easy uploads

**Total time:** ~5 minutes of implementation
**Value:** High - Better DX, stricter testing, easier CI/CD

---

**Ready to use!** Start with `cp .env.stack.example .env.stack` and `make stack-up`
