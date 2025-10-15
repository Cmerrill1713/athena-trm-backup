# Security Policy

## Reporting Security Issues

Please report security vulnerabilities to: christianmerrill@users.noreply.github.com

## Known Risk Register

| ID | Package | Severity | Mitigation | Owner | Review Date |
|----|---------|----------|------------|-------|-------------|
| R-01 | validator@13.11.0 | Moderate | URL validation bypass in stress tests only; no fix available upstream. Using override to pin to latest version. Not used in production paths. | @Cmerrill1713 | 2025-11-15 |
| R-02 | protobuf (Rust) | Low | In vendored/archived code only; active Cargo projects will be patched when dependencies updated. | @Cmerrill1713 | 2025-11-15 |

## Security Update Cadence

- **Critical/High:** Immediate patching within 24 hours
- **Medium:** Patched within 7 days  
- **Low:** Tracked and patched in regular release cycles

## Dependency Updates

- Automated Dependabot alerts enabled
- Monthly dependency review and updates
- All dependencies pinned with lock files

## Recent Security Fixes

### 2025-10-15
- ✅ CVE-2024-53981 (High): python-multipart 0.0.12 → 0.0.18
- ✅ CVE-2025-7783 (Critical): form-data (Node.js)  
- ✅ CVE-2025-58754 (High): axios (Node.js)
- ✅ CVE-2024-45337 (Critical): golang.org/x/crypto 0.14.0 → 0.43.0
- ✅ CVE-2025-22869 (High): golang.org/x/crypto
- ✅ CVE-2024-27304 (High): github.com/jackc/pgx/v5 5.4.3 → 5.7.6
- ✅ CVE-2023-39325 (High): golang.org/x/net 0.10.0 → 0.46.0
- ✅ CVE-2024-21503 (Medium): black 22.3.0 → 24.10.0
- ✅ Multiple golang.org/x/net CVEs (Medium)
- ✅ CVE-2024-24786 (Medium): google.golang.org/protobuf 1.31.0 → 1.36.10

**Status:** 17/20 vulnerabilities resolved (100% critical/high fixed)
