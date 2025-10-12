# Post-Incident Template

## Incident: [Title]

**Date**: YYYY-MM-DD
**Duration**: HH:MM
**Severity**: P0 / P1 / P2
**Status**: Resolved / Monitoring

---

## Summary

[2 sentences max: What broke and what we did]

---

## Impact

- **Users Affected**: [number or "all"]
- **Duration**: [start time - end time UTC]
- **Symptoms**:
  - [ ] Service unavailable
  - [ ] Degraded performance
  - [ ] Data inconsistency
  - [ ] Auth failures
  - [ ] Other: ___________

---

## Timeline (UTC)

| Time | Event | Action |
|------|-------|--------|
| HH:MM | Incident detected | [How: alert, user report, monitoring] |
| HH:MM | Investigation started | [Initial findings] |
| HH:MM | Root cause identified | [What was found] |
| HH:MM | Mitigation applied | [What was done] |
| HH:MM | Service restored | [Verification] |
| HH:MM | Incident closed | [Final checks] |

---

## Root Cause

[Detailed explanation of what went wrong and why]

**Contributing Factors**:
- [ ] Configuration error
- [ ] Deployment issue
- [ ] Dependency failure
- [ ] Resource exhaustion
- [ ] Human error
- [ ] External service
- [ ] Other: ___________

---

## Resolution

**Immediate Fix**:
```bash
[Commands or steps taken to restore service]
```

**Verification**:
```bash
[Commands used to verify fix]
```

---

## Prevention

### Immediate Actions
- [ ] Add test: [description]
- [ ] Add alert: [metric/condition]
- [ ] Add guardrail: [what prevents recurrence]
- [ ] Update runbook: [what section]
- [ ] Add monitoring: [what to track]

### Future Improvements
- [ ] Architectural change: [description]
- [ ] Process improvement: [description]
- [ ] Tooling enhancement: [description]

---

## Artifacts

**Correlation IDs**: [trace_id, request_id, etc.]

**Logs**:
- UAT: `/tmp/uat_8181.log` [lines XXX-YYY]
- Athena: `/tmp/athena_8090.log` [lines XXX-YYY]
- Bridge: `/tmp/bridge_8014.log` [lines XXX-YYY]

**Pull Requests**:
- Fix: [#PR_NUMBER]
- Prevention: [#PR_NUMBER]

**Dashboard**: [Grafana link if available]

---

## Owner & Follow-ups

**Incident Commander**: [Name]
**Root Cause Analysis**: [Name]
**Fix Implementation**: [Name]

**Follow-up Items**:
- [ ] Task 1: [description] - Owner: [name] - Due: [date]
- [ ] Task 2: [description] - Owner: [name] - Due: [date]
- [ ] Task 3: [description] - Owner: [name] - Due: [date]

---

## Lessons Learned

**What Went Well**:
- Detection time: [how long to detect]
- Response time: [how long to fix]
- Communication: [what worked]

**What Could Improve**:
- [Specific improvement 1]
- [Specific improvement 2]
- [Specific improvement 3]

---

**Reviewed By**: [Name, Date]
**Approved By**: [Name, Date]
**Next Review**: [Date]
